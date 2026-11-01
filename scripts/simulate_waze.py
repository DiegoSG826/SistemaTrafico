"""Cliente sintético del contrato canónico. No implementa ni suplanta una API oficial."""
import argparse
import os
import time
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

from ml_model.synthetic import live_minute


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.getenv("API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=10, trust_env=False) as client:
        response = client.post("/auth/token", json={"email": os.environ["ADMIN_EMAIL"],
                                                    "password": os.environ["ADMIN_PASSWORD"]})
        response.raise_for_status()
        client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        while True:
            catalog = client.get("/intersections")
            catalog.raise_for_status()
            records = []
            for item in catalog.json()["items"]:
                if not item["state"].get("sim_time"):
                    raise RuntimeError("Iniciar el trabajador para disponer de reloj simulado")
                end = datetime.fromisoformat(item["state"]["sim_time"]).replace(second=0, microsecond=0)
                for group in item["groups"]:
                    if group["code"] == "PEATON":
                        continue
                    for minute in range(5, 0, -1):
                        start = end-timedelta(minutes=minute)
                        counts, weather, speed = live_minute(start, item["id"], group["code"], args.seed)
                        records.append({"group_id": group["id"], "window_start": start.isoformat(),
                            "window_end": (start+timedelta(minutes=1)).isoformat(),
                            "arrivals": int(counts.sum()), "weather": weather,
                            "speed_kmh": speed, "source": "synthetic"})
            response = client.post("/traffic_records", json=records)
            response.raise_for_status()
            print(response.json())
            if args.once:
                return
            time.sleep(5)


if __name__ == "__main__":
    main()
