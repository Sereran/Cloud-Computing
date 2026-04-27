from fastapi import APIRouter, HTTPException, Request

# from google.cloud import secretmanager
import asyncio
import httpx
import logging
import os
from src import db

# Configure logger for route handlers
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games")

# External API URLs
RAWG_API_KEY = db.get_secret("RAWG-KEY")
RAWG_API_URL = "https://api.rawg.io/api/games"
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/games"
EXCHANGE_API_URL = "https://api.frankfurter.app/latest?from=USD&to=EUR,RON"


@router.get("")
async def get_all_games():
    """Fetches all games, merging tags in Python using descriptive, explicit logic."""
    with db.db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game")
        columns = [column[0] for column in cursor.description]
        all_games_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        games_by_id = {}
        for game_data in all_games_rows:
            game_id = game_data["id"]
            game_data["tags"] = []
            games_by_id[game_id] = game_data

        cursor.execute("SELECT game_id, tag_name FROM applied_tag")
        columns = [column[0] for column in cursor.description]
        all_tag_associations = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for association in all_tag_associations:
            game_id_from_tag = association["game_id"]
            tag_name = association["tag_name"]

            if game_id_from_tag in games_by_id:
                games_by_id[game_id_from_tag]["tags"].append(tag_name)

        logger.info(f"Retrieved {len(games_by_id)} games from library.")
        return list(games_by_id.values())


@router.get("/{game_id}")
async def get_aggregated_game_data(game_id: int):
    """Fetches a single game and its resources using direct, simple queries."""
    with db.db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game WHERE id = ?", (game_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"Game ID {game_id} not found in library.")
            raise HTTPException(status_code=404, detail=f"Game ID {game_id} not found.")

        columns = [column[0] for column in cursor.description]
        game_data = dict(zip(columns, row))

        cursor.execute("SELECT tag_name FROM applied_tag WHERE game_id = ?", (game_id,))
        game_data["tags"] = [t[0] for t in cursor.fetchall()]

        cursor.execute("SELECT url FROM media WHERE game_id = ?", (game_id,))
        media_urls = [m[0] for m in cursor.fetchall()]

        game_title = game_data.get("title")

    # External aggregation logic (outside DB context)
    async with httpx.AsyncClient() as client:
        try:
            rawg_task = client.get(
                f"{RAWG_API_URL}?key={RAWG_API_KEY}&search={game_title}"
            )
            cs_task = client.get(f"{CHEAPSHARK_API_URL}?title={game_title}")
            rates_task = client.get(EXCHANGE_API_URL)
            rawg_resp, cs_resp, rates_resp = await asyncio.gather(
                rawg_task, cs_task, rates_task
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to external APIs: {e}")
            raise HTTPException(
                status_code=502, detail="Failed to connect to external APIs."
            )

        rawg_data = rawg_resp.json()
        cover_image, metacritic, platforms = None, None, []
        if rawg_resp.status_code == 200 and rawg_data.get("results"):
            item = rawg_data["results"][0]
            cover_image, metacritic = item.get("background_image"), item.get(
                "metacritic"
            )
            platforms = [
                p.get("platform", {}).get("name")
                for p in item.get("platforms", [])
                if p.get("platform", {}).get("name")
            ]

        cs_data = cs_resp.json()
        price_usd, deal_id = (
            (float(cs_data[0]["cheapest"]), cs_data[0]["cheapestDealID"])
            if cs_resp.status_code == 200 and cs_data
            else (None, None)
        )

        price_eur, price_ron = None, None
        if rates_resp.status_code == 200 and price_usd is not None:
            rates = rates_resp.json().get("rates", {})
            price_eur, price_ron = round(price_usd * rates.get("EUR", 1.0), 2), round(
                price_usd * rates.get("RON", 1.0), 2
            )

        logger.info(
            f"Successfully aggregated data for game '{game_title}' ({game_id})."
        )
        return {
            "game_data": game_data,
            "media": {"cover_url": cover_image, "urls": media_urls},
            "pricing": {
                "usd": price_usd,
                "eur": price_eur,
                "ron": price_ron,
                "deal_id": deal_id,
            },
            "reviews": {"metacritic": metacritic},
            "platforms": platforms,
        }


@router.post("")
async def create_game(request: Request):
    """Creates a game using atomic transactions within the context manager."""
    data = await request.json()
    title, desc, tags, media_urls = (
        data.get("title"),
        data.get("description", ""),
        data.get("tags", []),
        data.get("media_urls", []),
    )

    with db.db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO game (title, description) OUTPUT INSERTED.id VALUES (?, ?)",
                (title, desc),
            )
            new_id = cursor.fetchone()[0]

            for tag_name in tags:
                try:
                    cursor.execute("INSERT INTO tag (name) VALUES (?)", (tag_name,))
                except Exception:
                    pass  # Ignore duplicates (equivalent to INSERT IGNORE)

                cursor.execute(
                    "INSERT INTO applied_tag (game_id, tag_name) VALUES (?, ?)",
                    (new_id, tag_name),
                )

            for url in media_urls:
                try:
                    cursor.execute(
                        "INSERT INTO media (url, game_id) VALUES (?, ?)", (url, new_id)
                    )
                except Exception:
                    pass  # Ignore duplicates

            conn.commit()
            logger.info(f"Successfully created game '{title}' with ID {new_id}.")
            return {"id": new_id, "title": title, "description": desc, "tags": tags}
        except Exception:
            conn.rollback()
            raise


@router.delete("/{game_id}")
async def delete_game(game_id: int):
    """Cascading delete with automatic resource cleanup."""
    with db.db_session() as conn:
        cursor = conn.cursor()
        try:
            # SQL Server doesn't support %s, use ?
            for table in ["applied_tag", "library", "media"]:
                cursor.execute(
                    (f"DELETE FROM {table} WHERE game_id = ?"),
                    (game_id,),
                )

            # After cleaning related tables, we do the final deletion.
            cursor.execute(("DELETE FROM game WHERE id = ?"), (game_id,))
            conn.commit()

            if cursor.rowcount == 0:
                logger.info(f"Attempted to delete game {game_id} but it was not found.")
                return {"status": "success", "message": "Game not found"}

            logger.info(f"Successfully deleted game {game_id} and all related records.")
            return {"status": "success", "message": "Game successfully deleted"}
        except Exception:
            conn.rollback()
            raise
