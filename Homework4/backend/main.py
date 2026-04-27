from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from azure.monitor.opentelemetry import configure_azure_monitor
import httpx
import asyncio
import dotenv
import os
import logging

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
hw1_api_url = os.getenv("HW1_API_URL", "http://127.0.0.1:8000/games")
rawg_api_key = os.getenv("RAWG_KEY")
rawg_api_url = "https://api.rawg.io/api/games"
cheapshark_api_url = "https://www.cheapshark.com/api/1.0/games"
exchange_api_url = "https://api.frankfurter.app/latest?from=USD&to=EUR,RON"


@app.get("/api/games")
async def get_all_games():
    async with httpx.AsyncClient() as client:
        try:
            # fecthes data from hw1 api and returns it to the frontend
            hw1_response = await client.get(hw1_api_url)

            if hw1_response.status_code != 200:
                raise HTTPException(
                    status_code=502, detail="error reading from game library service."
                )

            return hw1_response.json()

        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="internal server error: could not connect to game library service.",
            )


@app.get("/api/games/{game_id}")
async def get_aggregated_game_data(game_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # fetches data from all apis
            hw1_response = await client.get(f"{hw1_api_url}/{game_id}")
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="internal server error: could not connect to game library service.",
            )

        if hw1_response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"game id {game_id} not found in local library."
            )
        elif hw1_response.status_code != 200:
            raise HTTPException(
                status_code=502, detail="error reading from game library service."
            )

        hw1_data = hw1_response.json()

        game_title = hw1_data.get("title")
        if not game_title:
            raise HTTPException(
                status_code=400, detail="local game data is missing a title."
            )

        # fetch concurrently from all external apis
        try:
            rawg_task = client.get(
                f"{rawg_api_url}?key={rawg_api_key}&search={game_title}"
            )
            cs_task = client.get(f"{cheapshark_api_url}?title={game_title}")
            rates_task = client.get(exchange_api_url)

            # wait for all external apis to finish at the same time
            rawg_resp, cs_resp, rates_resp = await asyncio.gather(
                rawg_task, cs_task, rates_task
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="failed to connect to one or more external apis.",
            )

        # extract rawg data (image, metacritic, platforms)
        rawg_data = rawg_resp.json()
        cover_image = None
        metacritic_score = None
        platforms = []

        if rawg_resp.status_code == 200 and rawg_data.get("results"):
            first_result = rawg_data["results"][0]
            cover_image = first_result.get("background_image")
            metacritic_score = first_result.get("metacritic")

            if first_result.get("platforms"):
                for p in first_result["platforms"]:
                    platform_name = p.get("platform", {}).get("name")
                    if platform_name:
                        platforms.append(platform_name)

        # extract cheapshark price and link
        cs_data = cs_resp.json()
        price_usd = None
        deal_id = None

        if cs_resp.status_code == 200 and len(cs_data) > 0:
            best_match = cs_data[0]
            price_usd = float(best_match.get("cheapest", 0.0))
            deal_id = best_match.get(
                "cheapestDealID"
            )  # grabs the id to link to the store

        # calculate exchange rates
        rates_data = rates_resp.json()
        price_eur = None
        price_ron = None

        if rates_resp.status_code == 200 and price_usd is not None:
            eur_rate = rates_data["rates"].get("EUR", 1.0)
            ron_rate = rates_data["rates"].get("RON", 1.0)
            price_eur = round(price_usd * eur_rate, 2)
            price_ron = round(price_usd * ron_rate, 2)

        return {
            "local_data": hw1_data,
            "media": {"cover_url": cover_image},
            "pricing": {
                "usd": price_usd,
                "eur": price_eur,
                "ron": price_ron,
                "deal_id": deal_id,
            },
            "reviews": {"metacritic": metacritic_score},
            "platforms": platforms,
        }


@app.post("/api/games")
async def create_new_game(request: Request):
    # grabs the json data sent from the frontend
    new_game_data = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            # forward the data to the local hw1 web service
            hw1_response = await client.post(hw1_api_url, json=new_game_data)

            if hw1_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=hw1_response.status_code,
                    detail="failed to save game to local library.",
                )

            return hw1_response.json()

        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="could not connect to game library service."
            )


@app.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    async with httpx.AsyncClient() as client:
        try:
            hw1_response = await client.delete(f"{hw1_api_url}/{game_id}")

            if hw1_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=hw1_response.status_code,
                    detail="failed to delete game from local library.",
                )

            return {"message": "game successfully deleted"}

        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="could not connect to game library service."
            )