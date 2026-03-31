from fastapi import APIRouter, HTTPException, Request
from google.cloud import secretmanager
import asyncio
import httpx
import logging
import mysql.connector
import os
import db

# Configure logger for route handlers
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games")


# Secrets
def get_secret(secret_id: str, project_id: str = "937961278554") -> str:
    # Fetches a secret from Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        # Build the resource name of the secret
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

        # Access the secret
        response = client.access_secret_version(request={"name": name})

        # Decode the secret payload
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_id}: {e}")
        # Fallback to local environment variables
        return os.getenv(secret_id, "")


# External API URLs
RAWG_API_KEY = get_secret("RAWG_KEY")
RECAPTCHA_SECRET_KEY = get_secret("RECAPTCHA_KEY")
RAWG_API_URL = "https://api.rawg.io/api/games"
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/games"
EXCHANGE_API_URL = "https://api.frankfurter.app/latest?from=USD&to=EUR,RON"


@router.get("")
async def get_all_games():
    """Fetches all games, merging tags in Python using descriptive, explicit logic."""
    with db.db_session() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM game")
            all_games_rows = cursor.fetchall()

            games_by_id = {}
            for game_data in all_games_rows:
                game_id = game_data["id"]
                game_data["tags"] = []
                games_by_id[game_id] = game_data

            cursor.execute("SELECT game_id, tag_name FROM applied_tag")
            all_tag_associations = cursor.fetchall()

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
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM game WHERE id = %s", (game_id,))
            game_data = cursor.fetchone()

            if not game_data:
                logger.warning(f"Game ID {game_id} not found in library.")
                raise HTTPException(
                    status_code=404, detail=f"Game ID {game_id} not found."
                )

            cursor.execute(
                "SELECT tag_name FROM applied_tag WHERE game_id = %s", (game_id,)
            )
            game_data["tags"] = [t["tag_name"] for t in cursor.fetchall()]
            
            cursor.execute("SELECT url FROM media WHERE game_id = %s", (game_id,))
            media_urls = [m["url"] for m in cursor.fetchall()]

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
            "media": {
                "cover_url": cover_image,
                "urls": media_urls
            },
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
        conn.start_transaction()
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO game (title, description) VALUES (%s, %s)",
                    (title, desc),
                )
                new_id = cursor.lastrowid

                for tag_name in tags:
                    cursor.execute(
                        "INSERT IGNORE INTO tag (name) VALUES (%s)", (tag_name,)
                    )
                    cursor.execute(
                        "INSERT INTO applied_tag (game_id, tag_name) VALUES (%s, %s)",
                        (new_id, tag_name),
                    )
                
                for url in media_urls:
                    cursor.execute(
                        "INSERT IGNORE INTO media (url, game_id) VALUES (%s, %s)",
                        (url, new_id)
                    )

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
        conn.start_transaction()
        with conn.cursor() as cursor:
            try:
                # There are no cascade constraints in the SQL database.
                # We need to manually do the following cleanup.
                for table in ["applied_tag", "library", "media"]:
                    cursor.execute((
                        f"DELETE FROM {table} WHERE game_id = %s"),
                        (game_id,),
                    )
                
                # After cleanning related tables, we do the final deletion.
                cursor.execute(("DELETE FROM game WHERE id = %s"), (game_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    logger.info(
                        f"Attempted to delete game {game_id} but it was not found."
                    )
                    return {"status": "success", "message": "Game not found"}

                logger.info(
                    f"Successfully deleted game {game_id} and all related records."
                )
                return {"status": "success", "message": "Game successfully deleted"}
            except Exception:
                conn.rollback()
                raise
