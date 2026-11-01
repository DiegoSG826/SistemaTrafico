"""Prueba RNF-01: 10 usuarios, 600 s, consultas y recomendaciones (sin aplicar)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time

from dotenv import load_dotenv
import httpx
import numpy as np


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/load.json"))
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=5, trust_env=False) as client:
        login = client.post("/auth/token", json={"email": os.environ["ADMIN_EMAIL"],
                                                "password": os.environ["ADMIN_PASSWORD"]})
        login.raise_for_status()
        token = login.json()["access_token"]
    deadline = time.monotonic()+args.seconds
    def run(_):
        samples = {"query": [], "prediction": [], "errors": 0, "conflicts": 0}
        with httpx.Client(base_url=args.url, timeout=5, trust_env=False,
                         headers={"Authorization": f"Bearer {token}"}) as client:
            # Calentamiento sin contabilizar.
            client.get("/intersections").raise_for_status()
            while time.monotonic() < deadline:
                start = time.perf_counter()
                try:
                    response = client.get("/intersections")
                    response.raise_for_status()
                    samples["query"].append(time.perf_counter()-start)
                    item = response.json()["items"][0]
                    start = time.perf_counter()
                    response = client.post("/predict_light", json={"intersection_id": item["id"],
                                                                  "previous_version": item["plan_version"]})
                    if response.status_code == 409:
                        samples["conflicts"] += 1
                    else:
                        response.raise_for_status()
                        samples["prediction"].append(time.perf_counter()-start)
                except httpx.HTTPError:
                    samples["errors"] += 1
                time.sleep(.1)
        return samples
    with ThreadPoolExecutor(max_workers=args.users) as pool:
        runs = list(pool.map(run, range(args.users)))
    report = {"users": args.users, "duration_s": args.seconds,
              "errors": sum(r["errors"] for r in runs), "conflicts": sum(r["conflicts"] for r in runs)}
    for key in ("query", "prediction"):
        values = [v for r in runs for v in r[key]]
        report[key] = {"requests": len(values), "p95_ms": float(np.percentile(values, 95)*1000) if values else None}
    args.output.parent.mkdir(exist_ok=True, parents=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
