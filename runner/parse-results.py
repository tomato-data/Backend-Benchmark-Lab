#!/usr/bin/env python3
"""Parse k6 JSON results and calculate averages."""

import json
import sys
from pathlib import Path
from statistics import mean, stdev

SCENARIOS = [
    "01-lightweight",
    "02-json-payload",
    "03-db-read",
    "04-db-write",
    "05-external-api",
    "06-middleware-chain",
    "07-file-upload",
    "08-concurrent-mixed",
]


def parse_summary_json(filepath: Path) -> dict[str, float] | None:
    """Extract key metrics from k6 --summary-export JSON."""
    try:
        with open(filepath) as f:
            data = json.load(f)

        metrics = data.get("metrics", {})

        return {
            "rps": metrics.get("http_reqs", {}).get("rate", 0),
            "latency_avg": metrics.get("http_req_duration", {}).get("avg", 0),
            "latency_p95": metrics.get("http_req_duration", {}).get("p(95)", 0),
            "latency_p99": metrics.get("http_req_duration", {}).get("p(99)", 0),
        }
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def extract_scenario(filename: str) -> str | None:
    """Extract scenario name from filename."""
    # 파일명: {scenario}-run{i}.json
    # 예: 01-lightweight-run1.json
    for scenario in SCENARIOS:
        if filename.startswith(f"{scenario}-run"):
            return scenario
    return None


def find_all_results(results_dir: Path) -> dict[str, dict[str, list[Path]]]:
    """Find all result files, grouped by server scenario."""
    # 구조: results/{server}/{date}/{scenario}-run{i}.json
    results: dict[str, dict[str, list[Path]]] = {}
    for server_dir in results_dir.iterdir():
        if not server_dir.is_dir():
            continue

        server = server_dir.name
        if server not in results:
            results[server] = {}

        # 날짜 디렉토리 순회
        for date_dir in server_dir.iterdir():
            if not date_dir.is_dir():
                continue

            for f in date_dir.glob("*.json"):
                scenario = extract_scenario(f.name)
                if scenario:
                    if scenario not in results[server]:
                        results[server][scenario] = []
                    results[server][scenario].append(f)

    return results


def calculate_averages(files: list[Path]) -> dict[str, float | int] | None:
    """Calculate average metrics from a list of result files."""
    if not files:
        return None

    rps_list: list[float] = []
    latency_avg_list: list[float] = []
    latency_p95_list: list[float] = []
    latency_p99_list: list[float] = []

    for f in files:
        if not f.exists():
            continue
        metrics = parse_summary_json(f)
        if metrics:
            rps_list.append(metrics["rps"])
            latency_avg_list.append(metrics["latency_avg"])
            latency_p95_list.append(metrics["latency_p95"])
            latency_p99_list.append(metrics["latency_p99"])

    if not rps_list:
        return None

    return {
        "runs": len(rps_list),
        "rps_avg": round(mean(rps_list), 2),
        "rps_std": round(stdev(rps_list), 2) if len(rps_list) > 1 else 0,
        "latency_avg": round(mean(latency_avg_list), 3),
        "latency_p95": round(mean(latency_p95_list), 3),
        "latency_p99": round(mean(latency_p99_list), 3),
    }


def print_markdown_table(results: dict[str, dict[str, dict[str, float | int]]]) -> None:
    """Print results as markdown table."""
    if not results:
        print("No results to display.")
        return

    print(
        "| Server | Scenario | Runs | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |"
    )
    print(
        "|--------|----------|------|---------------|-------------|-------------|-------------|"
    )

    for server in sorted(results.keys()):
        for scenario in SCENARIOS:
            if scenario in results[server]:
                data = results[server][scenario]
                rps = f"{data['rps_avg']}±{data['rps_std']}"
                print(
                    f"| {server} | {scenario} | {data['runs']} | {rps} | {data['latency_avg']}ms | {data['latency_p95']}ms | {data['latency_p99']}ms |"
                )


if __name__ == "__main__":
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        sys.exit(1)

    # 존재하는 JSON 파일에서 서버/시나리오 자동 탐지
    all_results = find_all_results(results_dir)

    if not all_results:
        print("No result files found.")
        sys.exit(1)

    # 평균 계산
    aggregated: dict[str, dict[str, dict[str, float | int]]] = {}
    for server, scenarios in all_results.items():
        if server not in aggregated:
            aggregated[server] = {}
        for scenario, files in scenarios.items():
            data = calculate_averages(files)
            if data:
                aggregated[server][scenario] = data

    print_markdown_table(aggregated)
