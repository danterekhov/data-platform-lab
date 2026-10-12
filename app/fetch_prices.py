import argparse
import os
from datetime import datetime, timezone

import psycopg
import requests

API_URL = "https://api.coingecko.com/api/v3/simple/price"
DEFAULT_COINS = ["bitcoin", "ethereum", "solana"]
DATABASE_URL = os.environ.get("DATABASE_URL")


def fetch_prices(coins: list[str]) -> dict:
    params = {"ids": ",".join(coins), "vs_currencies": "usd"}
    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def store_prices(conn: psycopg.Connection, data: dict, fetched_at: datetime) -> int:
    coins = [name for name in data if not name.startswith("_")]
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id          SERIAL PRIMARY KEY,
                coin        TEXT        NOT NULL,
                price_usd   NUMERIC     NOT NULL,
                fetched_at  TIMESTAMPTZ NOT NULL
            )
            """
        )
        for coin in coins:
            cur.execute(
                "INSERT INTO prices (coin, price_usd, fetched_at) VALUES (%s, %s, %s)",
                (coin, data[coin]["usd"], fetched_at),
            )
    conn.commit()
    return len(coins)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch crypto prices and store them in PostgreSQL")
    parser.add_argument("--coins", nargs="+", default=DEFAULT_COINS, help="coin ids")
    args = parser.parse_args()

    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL environment variable is not set")

    data = fetch_prices(args.coins)
    fetched_at = datetime.now(timezone.utc)

    with psycopg.connect(DATABASE_URL) as conn:
        count = store_prices(conn, data, fetched_at)

    print(f"Stored {count} prices at {fetched_at.isoformat()}")


if __name__ == "__main__":
    main()
