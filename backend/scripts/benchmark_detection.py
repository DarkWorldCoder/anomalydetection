"""Benchmark Isolation Forest inference with real project dataset records."""

from __future__ import annotations

import argparse
import json
import math
import platform
import resource
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.detection import TrafficRecord
from app.services.detection_service import detect, load_artifacts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "datasets" / "dataset_4_sample_100_mixed.json"


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil((percentage / 100) * len(ordered)) - 1)
    return ordered[index]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure model-only detection latency and throughput using real dataset records."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--records", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_path = args.dataset.resolve()
    if args.records < 1 or args.warmup < 0 or args.repeats < 1:
        raise SystemExit("records and repeats must be positive; warmup cannot be negative")

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise SystemExit("dataset must be a non-empty JSON array or an object with a records array")

    selected = [TrafficRecord.model_validate(row) for row in rows[: args.records]]
    config, model = load_artifacts()

    cold_started = time.perf_counter()
    cold_result = detect(selected[0])
    cold_latency_ms = (time.perf_counter() - cold_started) * 1000

    for _ in range(args.warmup):
        for record in selected:
            detect(record)

    run_seconds: list[float] = []
    predictions: list[str] = []
    for repeat in range(args.repeats):
        started = time.perf_counter()
        results = [detect(record) for record in selected]
        run_seconds.append(time.perf_counter() - started)
        if repeat == 0:
            predictions = [result["prediction"] for result in results]

    per_record_ms = [(seconds / len(selected)) * 1000 for seconds in run_seconds]
    throughput = [len(selected) / seconds for seconds in run_seconds]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": "Python time.perf_counter model microbenchmark",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dataset": str(dataset_path),
        "records_per_run": len(selected),
        "warmup_runs": args.warmup,
        "measured_runs": args.repeats,
        "model": {
            "trees": model["n_trees"],
            "features": len(config["feature_names"]),
            "threshold": config["threshold"],
        },
        "results": {
            "cold_first_record_ms": round(cold_latency_ms, 4),
            "mean_run_seconds": round(statistics.mean(run_seconds), 6),
            "mean_latency_ms_per_record": round(statistics.mean(per_record_ms), 4),
            "median_latency_ms_per_record": round(statistics.median(per_record_ms), 4),
            "p95_latency_ms_per_record": round(percentile(per_record_ms, 95), 4),
            "p99_latency_ms_per_record": round(percentile(per_record_ms, 99), 4),
            "mean_throughput_records_per_second": round(statistics.mean(throughput), 2),
            "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
            "suspicious_records": predictions.count("Suspicious"),
            "benign_records": predictions.count("Benign"),
            "cold_first_prediction": cold_result["prediction"],
        },
        "individual_run_seconds": [round(value, 6) for value in run_seconds],
    }

    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Saved benchmark evidence to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
