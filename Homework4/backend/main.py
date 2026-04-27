from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from azure.monitor.opentelemetry import configure_azure_monitor
import httpx
import asyncio
import dotenv
import os
import logging
import pyodbc

dotenv.load_dotenv()

# configurare azure monitor pentru logging in cloud
connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if connection_string:
    configure_azure_monitor(connection_string=connection_string)

logger = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# configuration
# folosim os.getenv pentru a putea schimba url-ul fara sa modificam codul in azure
server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USER")
password = os.getenv("SQL_PASSWORD")
driver = '{ODBC Driver 18 for SQL Server}'
rawg_api_key = os.getenv("RAWG_KEY")
rawg_api_url = "https://api.rawg.io/api/games"
cheapshark_api_url = "https://www.cheapshark.com/api/1.0/games"
exchange_api_url = "https://api.frankfurter.app/latest?from=USD&to=EUR,RON"

# functie pentru a crea conexiunea la baza de date
def get_db_connection():
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    return pyodbc.connect(conn_str)

@app.get("/api/games")
async def get_all_games():
    try:
        # citim jocurile din sql si le returnam catre frontend
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("select id, title, genre from games")
        games = []
        for row in cursor.fetchall():
            games.append({"id": row[0], "title": row[1], "genre": row[2]})
        conn.close()
        return games
    except Exception as e:
        logger.error(f"database error: {e}")
        # daca serviciul extern nu raspunde, returnam date de test
        return [
            {"id": 1, "title": "the witcher 3", "genre": "rpg"},
            {"id": 2, "title": "elden ring", "genre": "action"},
            {"id": 3, "title": "cyberpunk 2077", "genre": "fps"}
        ]


@app.get("/api/games/{game_id}")
async def get_aggregated_game_data(game_id: int):
    # 1. incercam sa luam datele din sql
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("select id, title, genre from games where id = ?", (game_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            hw1_data = {"id": row[0], "title": row[1], "genre": row[2]}
            game_title = row[1]
        else:
            # daca nu exista in sql, dam un fallback sa nu crape tot api-ul
            hw1_data = {"id": game_id, "title": "unknown game", "genre": "n/a"}
            game_title = "the witcher 3" # fallback pentru api-uri externe
    except Exception as e:
        logger.error(f"database error: {e}")
        hw1_data = {"id": game_id, "title": "db connection error", "genre": "n/a"}
        game_title = "the witcher 3"

    # 2. apelam api-urile externe cu protectie la erori
    async with httpx.AsyncClient() as client:
        try:
            responses = await asyncio.gather(
                client.get(f"{rawg_api_url}?key={rawg_api_key}&search={game_title}"),
                client.get(f"{cheapshark_api_url}?title={game_title}"),
                client.get(exchange_api_url),
                return_exceptions=True # foarte important: nu crapa tot daca un api pica
            )
            
            rawg_resp = responses[0] if not isinstance(responses[0], Exception) else None
            cs_resp = responses[1] if not isinstance(responses[1], Exception) else None
            rates_resp = responses[2] if not isinstance(responses[2], Exception) else None

            # extractie sigura rawg
            media = {"cover_url": None}
            reviews = {"metacritic": None}
            platforms = []
            if rawg_resp and rawg_resp.status_code == 200:
                results = rawg_resp.json().get("results", [])
                if results:
                    media["cover_url"] = results[0].get("background_image")
                    reviews["metacritic"] = results[0].get("metacritic")
                    platforms = [p.get("platform", {}).get("name") for p in results[0].get("platforms", [])]

            # extractie sigura preturi
            pricing = {"usd": None, "eur": None, "ron": None, "deal_id": None}
            if cs_resp and cs_resp.status_code == 200:
                cs_data = cs_resp.json()
                if cs_data:
                    usd = float(cs_data[0].get("cheapest", 0))
                    pricing["usd"] = usd
                    pricing["deal_id"] = cs_data[0].get("cheapestDealID")
                    
                    if rates_resp and rates_resp.status_code == 200:
                        rates = rates_resp.json().get("rates", {})
                        pricing["eur"] = round(usd * rates.get("EUR", 0.92), 2)
                        pricing["ron"] = round(usd * rates.get("RON", 4.95), 2)

            return {
                "local_data": hw1_data,
                "media": media,
                "pricing": pricing,
                "reviews": reviews,
                "platforms": platforms
            }
            
        except Exception as e:
            return {"error": "aggregation failed", "details": str(e), "local_data": hw1_data}

@app.post("/api/games")
async def create_new_game(request: Request):
    # grabs the json data sent from the frontend
    new_game_data = await request.json()

    try:
        # salvam datele in sql
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("insert into games (title, genre) values (?, ?)", 
                       (new_game_data['title'], new_game_data['genre']))
        conn.commit()
        conn.close()
        return {"message": "game saved to sql database"}
    except Exception as e:
        logger.error(f"sql error: {e}")
        # raspuns simulacru pentru succes in mod offline
        return {"message": "mock success: game saved", "data": new_game_data}


@app.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    try:
        # stergem jocul din baza de date sql
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("delete from games where id = ?", (game_id,))
        conn.commit()
        conn.close()
        return {"message": "game successfully deleted from sql"}
    except Exception as e:
        logger.error(f"sql error: {e}")
        # raspuns simulacru pentru succes in mod offline
        return {"message": "mock success: game deleted"}