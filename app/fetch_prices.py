import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.coingecko.com/api/v3/simple/price"
DEFAULT_COINS = ["bitcoin", "ethereum", "solana"]


def fetch_prices(coins: list[str]) -> dict:
    params = {"ids": ",".join(coins), "vs_currencies": "usd"}
    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def save_prices(data: dict, out_dir: str) -> Path:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"prices_{timestamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch crypto prices from CoinGecko")
    parser.add_argument("--coins", nargs="+", default=DEFAULT_COINS, help="coin ids")
    parser.add_argument("--out", default="data", help="output directory")
    args = parser.parse_args()

    data = fetch_prices(args.coins)
    data["_fetched_at"] = datetime.now(timezone.utc).isoformat()

    path = save_prices(data, args.out)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
