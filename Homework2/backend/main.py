from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import dotenv
import os

dotenv.load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
HW1_API_URL = "http://127.0.0.1:8000/games"
RAWG_API_KEY = os.getenv("RAWG_KEY")
RAWG_API_URL = "https://api.rawg.io/api/games"
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/games"
EXCHANGE_API_URL = "https://api.frankfurter.app/latest?from=USD&to=EUR,RON"


@app.get("/api/games")
async def get_all_games():
    async with httpx.AsyncClient() as client:
        try:
            # fecthes data from HW1 API and returns it to the frontend
            hw1_response = await client.get(HW1_API_URL)

            if hw1_response.status_code != 200:
                raise HTTPException(
                    status_code=502, detail="Error reading from Game Library Service."
                )

            return hw1_response.json()

        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error: Could not connect to Game Library Service.",
            )


@app.get("/api/games/{game_id}")
async def get_aggregated_game_data(game_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # fetches data from all APIs
            hw1_response = await client.get(f"{HW1_API_URL}/{game_id}")
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error: Could not connect to Game Library Service.",
            )

        if hw1_response.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Game ID {game_id} not found in local library."
            )
        elif hw1_response.status_code != 200:
            raise HTTPException(
                status_code=502, detail="Error reading from Game Library Service."
            )

        hw1_data = hw1_response.json()

        game_title = hw1_data.get("title")
        if not game_title:
            raise HTTPException(
                status_code=400, detail="Local game data is missing a title."
            )

        # fetch concurrently from all external APIs
        try:
            rawg_task = client.get(
                f"{RAWG_API_URL}?key={RAWG_API_KEY}&search={game_title}"
            )
            cs_task = client.get(f"{CHEAPSHARK_API_URL}?title={game_title}")
            rates_task = client.get(EXCHANGE_API_URL)

            # wait for all external APIs to finish at the same time
            rawg_resp, cs_resp, rates_resp = await asyncio.gather(
                rawg_task, cs_task, rates_task
            )

        except httpx.RequestError:
            raise HTTPException(
                status_code=502,
                detail="Failed to connect to one or more external APIs.",
            )

        # extract RAWG Data (Image, Metacritic, Platforms)
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

        # extract CheapShark price and link
        cs_data = cs_resp.json()
        price_usd = None
        deal_id = None

        if cs_resp.status_code == 200 and len(cs_data) > 0:
            best_match = cs_data[0]
            price_usd = float(best_match.get("cheapest", 0.0))
            deal_id = best_match.get(
                "cheapestDealID"
            )  # grabs the ID to link to the store

        # calculate Exchange Rates
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
    # grabs the JSON data sent from the frontend
    new_game_data = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            # forward the data to the local HW1 Web Service
            hw1_response = await client.post(HW1_API_URL, json=new_game_data)

            if hw1_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=hw1_response.status_code,
                    detail="Failed to save game to local library.",
                )

            return hw1_response.json()

        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="Could not connect to Game Library Service."
            )


@app.delete("/api/games/{game_id}")
async def delete_game(game_id: int):
    async with httpx.AsyncClient() as client:
        try:
            hw1_response = await client.delete(f"{HW1_API_URL}/{game_id}")

            if hw1_response.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=hw1_response.status_code,
                    detail="Failed to delete game from local library.",
                )

            return {"message": "Game successfully deleted"}

        except httpx.RequestError:
            raise HTTPException(
                status_code=500, detail="Could not connect to Game Library Service."
            )
