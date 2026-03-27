#!/usr/bin/env python3
"""Parse server config experiment results and generate comparison tables."""

import json
import re
import sys
from pathlib import Path
from statistics import mean, stdev

# 서버 구성 (표시 순서)
CONFIGS = ["uvicorn", "gunicorn-2w", "gunicorn-4w"]

# 시나리오 (표시 순서)
SCENARIOS = ["io-sleep", "io-db", "cpu-fibonacci", "cpu-hash", "mixed-report"]

# 파일명 패턴 (두 가지 지원)
# 신규: {config}-cpu{CPU}-{scenario}-vu{VU}-run{i}.json
# 기존: {config}-{scenario}-vu{VU}-run{i}.json
FILENAME_PATTERN_WITH_CPU = re.compile(
    r"^(uvicorn|gunicorn-2w|gunicorn-4w)-cpu([0-9.]+)-(.+)-vu(\d+)-run(\d+)\.json$"
)
FILENAME_PATTERN_LEGACY = re.compile(
    r"^(uvicorn|gunicorn-2w|gunicorn-4w)-(.+)-vu(\d+)-run(\d+)\.json$"
)


def parse_summary_json(filepath: Path) -> dict[str, float] | None:
    """Extract key metrics from k6 --summary-export JSON."""
    try:
        with open(filepath) as f:
            data = json.load(f)

        metrics = data.get("metrics", {})

        return {
            "rps": metrics.get("http_reqs", {}).get("rate", 0),
            "latency_avg": metrics.get("http_req_duration", {}).get("avg", 0),
            "latency_p50": metrics.get("http_req_duration", {}).get("med", 0),
            "latency_p95": metrics.get("http_req_duration", {}).get("p(95)", 0),
            "latency_p99": metrics.get("http_req_duration", {}).get("p(99)", 0),
            "error_rate": metrics.get("http_req_failed", {}).get("rate", 0),
        }
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def parse_filename(filename: str) -> tuple[str, str, str, int, int] | None:
    """Parse config, cpu, scenario, VU, run number from filename.

    Returns: (config, cpu, scenario, vu, run)
    """
    # 신규 패턴 먼저 시도
    match = FILENAME_PATTERN_WITH_CPU.match(filename)
    if match:
        config, cpu, scenario, vu, run = match.groups()
        return config, cpu, scenario, int(vu), int(run)

    # 기존 패턴 fallback
    match = FILENAME_PATTERN_LEGACY.match(filename)
    if match:
        config, scenario, vu, run = match.groups()
        return config, "?", scenario, int(vu), int(run)

    return None


def find_results(results_dir: Path) -> dict[tuple[str, str, str, int], list[Path]]:
    """Find and group all result files.

    Returns: { (config, cpu, scenario, vu): [Path, ...] }
    """
    groups: dict[tuple[str, str, str, int], list[Path]] = {}

    for f in sorted(results_dir.rglob("*.json")):
        parsed = parse_filename(f.name)
        if not parsed:
            continue

        config, cpu, scenario, vu, _ = parsed
        key = (config, cpu, scenario, vu)
        if key not in groups:
            groups[key] = []
        groups[key].append(f)

    return groups


def calculate_stats(files: list[Path]) -> dict[str, float | int] | None:
    """Calculate average metrics from result files."""
    rps_list = []
    latency_avg_list = []
    latency_p50_list = []
    latency_p95_list = []
    latency_p99_list = []
    error_rate_list = []

    for f in files:
        metrics = parse_summary_json(f)
        if metrics:
            rps_list.append(metrics["rps"])
            latency_avg_list.append(metrics["latency_avg"])
            latency_p50_list.append(metrics["latency_p50"])
            latency_p95_list.append(metrics["latency_p95"])
            latency_p99_list.append(metrics["latency_p99"])
            error_rate_list.append(metrics["error_rate"])

    if not rps_list:
        return None

    return {
        "runs": len(rps_list),
        "rps_avg": round(mean(rps_list), 2),
        "rps_std": round(stdev(rps_list), 2) if len(rps_list) > 1 else 0,
        "latency_avg": round(mean(latency_avg_list), 3),
        "latency_p50": round(mean(latency_p50_list), 3),
        "latency_p95": round(mean(latency_p95_list), 3),
        "latency_p99": round(mean(latency_p99_list), 3),
        "error_rate": round(mean(error_rate_list) * 100, 2),
    }


def print_round_table(
    groups: dict[tuple[str, str, str, int], dict], round_name: str
) -> None:
    """Print results for a specific round as markdown table."""
    if not groups:
        return

    # CPU가 여러 종류인지 확인
    cpus = set(key[1] for key in groups.keys())
    show_cpu = len(cpus) > 1 or cpus != {"?"}

    print(f"\n### {round_name}\n")
    if show_cpu:
        print(
            "| Config | CPU | Scenario | VU | Runs | RPS (avg±std) | Latency avg | P50 | P95 | P99 | Error % |"
        )
        print(
            "|--------|-----|----------|----|------|---------------|-------------|-----|-----|-----|---------|"
        )
    else:
        print(
            "| Config | Scenario | VU | Runs | RPS (avg±std) | Latency avg | P50 | P95 | P99 | Error % |"
        )
        print(
            "|--------|----------|----|------|---------------|-------------|-----|-----|-----|---------|"
        )

    def sort_key(item):
        key = item[0]
        config_idx = CONFIGS.index(key[0]) if key[0] in CONFIGS else 99
        cpu_val = float(key[1]) if key[1] != "?" else 0
        return (config_idx, cpu_val, key[3])

    for (config, cpu, scenario, vu), stats in sorted(groups.items(), key=sort_key):
        rps = f"{stats['rps_avg']}±{stats['rps_std']}"
        if show_cpu:
            print(
                f"| {config} | {cpu} | {scenario} | {vu} | {stats['runs']} "
                f"| {rps} | {stats['latency_avg']}ms "
                f"| {stats['latency_p50']}ms | {stats['latency_p95']}ms "
                f"| {stats['latency_p99']}ms | {stats['error_rate']}% |"
            )
        else:
            print(
                f"| {config} | {scenario} | {vu} | {stats['runs']} "
                f"| {rps} | {stats['latency_avg']}ms "
                f"| {stats['latency_p50']}ms | {stats['latency_p95']}ms "
                f"| {stats['latency_p99']}ms | {stats['error_rate']}% |"
            )


def print_comparison_summary(
    groups: dict[tuple[str, str, str, int], dict],
) -> None:
    """Print a concise comparison between configs for each cpu+scenario+vu."""
    comparisons: dict[tuple[str, str, int], dict[str, dict]] = {}

    for (config, cpu, scenario, vu), stats in groups.items():
        key = (cpu, scenario, vu)
        if key not in comparisons:
            comparisons[key] = {}
        comparisons[key][config] = stats

    cpus = set(key[1] for key in groups.keys())
    show_cpu = len(cpus) > 1 or cpus != {"?"}

    print("\n### Config Comparison (RPS)\n")
    if show_cpu:
        print(
            "| CPU | Scenario | VU | uvicorn | gunicorn-2w | gunicorn-4w | Winner |"
        )
        print(
            "|-----|----------|----|---------|-------------|-------------|--------|"
        )
    else:
        print("| Scenario | VU | uvicorn | gunicorn-2w | gunicorn-4w | Winner |")
        print("|----------|----|---------|-------------|-------------|--------|")

    for (cpu, scenario, vu) in sorted(comparisons.keys()):
        configs = comparisons[(cpu, scenario, vu)]

        values = []
        for c in CONFIGS:
            if c in configs:
                values.append(f"{configs[c]['rps_avg']}")
            else:
                values.append("-")

        best_config = max(
            (c for c in CONFIGS if c in configs),
            key=lambda c: configs[c]["rps_avg"],
            default="-",
        )

        if show_cpu:
            print(
                f"| {cpu} | {scenario} | {vu} | {values[0]} | {values[1]} | {values[2]} | **{best_config}** |"
            )
        else:
            print(
                f"| {scenario} | {vu} | {values[0]} | {values[1]} | {values[2]} | **{best_config}** |"
            )


if __name__ == "__main__":
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        sys.exit(1)

    # 결과 파일 탐색 및 그룹핑
    file_groups = find_results(results_dir)

    if not file_groups:
        print("No result files found.")
        sys.exit(1)

    # 통계 계산
    stats_groups: dict[tuple[str, str, str, int], dict] = {}
    for key, files in file_groups.items():
        stats = calculate_stats(files)
        if stats:
            stats_groups[key] = stats

    # 라운드별 결과 출력
    round_dirs = set()
    for f in results_dir.rglob("*.json"):
        if f.parent.name.startswith("round"):
            round_dirs.add(f.parent.name)

    if round_dirs:
        for round_name in sorted(round_dirs):
            round_path = results_dir / round_name
            round_groups = find_results(round_path)
            round_stats = {}
            for key, files in round_groups.items():
                stats = calculate_stats(files)
                if stats:
                    round_stats[key] = stats
            print_round_table(round_stats, round_name)
            print_comparison_summary(round_stats)
    else:
        # 라운드 구분 없이 전체 출력
        print_round_table(stats_groups, "All Results")
        print_comparison_summary(stats_groups)
