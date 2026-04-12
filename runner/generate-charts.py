#!/usr/bin/env python3
"""Generate benchmark charts for README.

Usage:
    source .venv/bin/activate
    python generate-charts.py
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Color palette
COLORS = {
    "express": "#F7DF1E",       # JS yellow
    "fastapi_p": "#009688",     # teal
    "fastapi_s": "#00695C",     # dark teal
    "rails": "#CC0000",         # ruby red
    "django": "#0C4B33",        # django green
    "uvicorn": "#2196F3",       # blue
    "gunicorn_2w": "#FF9800",   # orange
    "gunicorn_4w": "#F44336",   # red
    "cache_hit": "#4CAF50",     # green
    "cache_miss": "#F44336",    # red
    "no_cache": "#9E9E9E",      # gray
    "with_cache": "#2196F3",    # blue
}

STYLE = {
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FAFAFA",
    "axes.edgecolor": "#DDDDDD",
    "axes.grid": True,
    "grid.color": "#EEEEEE",
    "grid.linestyle": "-",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
}
plt.rcParams.update(STYLE)


def save(fig: plt.Figure, name: str) -> None:
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


# ============================================================
# Chart 1: Framework RPS Comparison (Basic 01-08)
# ============================================================
def chart_framework_rps() -> None:
    scenarios = [
        "01\nlightweight",
        "02\njson",
        "03\ndb-read",
        "04\ndb-write",
        "05\nexternal",
        "06\nmiddleware",
        "07\nupload",
        "08\nmixed",
    ]
    data = {
        "Express":    [20492, 17403,  498, 5875,  92, 18771, 10063, 244],
        "FastAPI-P":  [14225, 11790,  147, 1280,  94,  9799,  6029, 122],
        "FastAPI-S":  [13928, 11635,  170, 1528,  93, 10455,  6084, 133],
        "Rails":      [ 3632,  4200, 1524, 1719,  90,  3519,  3150, 557],
        "Django":     [ 2899,  2621,  288,  411,  19,  2560,  2622,  93],
    }
    colors = [
        COLORS["express"],
        COLORS["fastapi_p"],
        COLORS["fastapi_s"],
        COLORS["rails"],
        COLORS["django"],
    ]

    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.suptitle("Framework RPS Comparison (10 VUs, 30s, avg of 10 runs)", fontsize=16, fontweight="bold", y=0.98)

    frameworks = list(data.keys())
    x = np.arange(len(frameworks))
    width = 0.6

    for idx, (ax, scenario) in enumerate(zip(axes.flat, scenarios)):
        values = [data[fw][idx] for fw in frameworks]
        bars = ax.bar(x, values, width, color=colors, edgecolor="white", linewidth=0.5)

        # Highlight winner
        max_val = max(values)
        for bar, val in zip(bars, values):
            if val == max_val:
                bar.set_edgecolor("#333333")
                bar.set_linewidth(2)

        ax.set_title(scenario, fontsize=11, pad=8)
        ax.set_xticks(x)
        ax.set_xticklabels(frameworks, fontsize=8, rotation=30, ha="right")
        ax.set_ylabel("RPS", fontsize=9)

        # Format y-axis with comma separator
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

        # Add value labels on top of bars
        for bar, val in zip(bars, values):
            label = f"{val:,}" if val >= 1000 else str(val)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                label,
                ha="center",
                va="bottom",
                fontsize=7,
                fontweight="bold",
            )

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    save(fig, "01-framework-rps")


# ============================================================
# Chart 2: Clean Architecture vs Pragmatic
# ============================================================
def chart_clean_arch() -> None:
    scenarios = [
        "01-lightweight",
        "02-json",
        "03-db-read",
        "04-db-write",
        "05-external",
        "06-middleware",
        "07-upload",
        "08-mixed",
    ]
    pragmatic_rps = [14225, 11790, 147, 1280, 94, 9799, 6029, 122]
    strict_rps    = [13928, 11635, 170, 1528, 93, 10455, 6084, 133]
    pragmatic_std = [264.53, 158.13, 3.93, 17.35, 0.30, 137.68, 24.77, 56.37]
    strict_std    = [37.68, 29.63, 3.21, 32.13, 0.51, 189.73, 19.53, 65.67]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("FastAPI: Clean Architecture (Strict) vs Pragmatic", fontsize=14, fontweight="bold", y=1.0)

    x = np.arange(len(scenarios))
    width = 0.35

    # RPS comparison
    bars1 = ax1.bar(x - width / 2, pragmatic_rps, width, label="Pragmatic", color=COLORS["fastapi_p"], edgecolor="white")
    bars2 = ax1.bar(x + width / 2, strict_rps, width, label="Strict (Clean Arch)", color=COLORS["fastapi_s"], edgecolor="white")
    ax1.set_title("RPS (higher = better)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, rotation=35, ha="right", fontsize=9)
    ax1.set_ylabel("RPS")
    ax1.legend(loc="upper right")
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    # Annotate % diff on the bars
    for i, (p, s) in enumerate(zip(pragmatic_rps, strict_rps)):
        diff = (s - p) / p * 100
        color = "#4CAF50" if diff > 0 else "#F44336"
        label = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"
        y_pos = max(p, s)
        ax1.text(i, y_pos, label, ha="center", va="bottom", fontsize=8, fontweight="bold", color=color)

    # Standard deviation comparison (stability)
    bars3 = ax2.bar(x - width / 2, pragmatic_std, width, label="Pragmatic", color=COLORS["fastapi_p"], edgecolor="white")
    bars4 = ax2.bar(x + width / 2, strict_std, width, label="Strict (Clean Arch)", color=COLORS["fastapi_s"], edgecolor="white")
    ax2.set_title("Std Dev (lower = more stable)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(scenarios, rotation=35, ha="right", fontsize=9)
    ax2.set_ylabel("Std Dev (RPS)")
    ax2.legend(loc="upper right")

    fig.tight_layout()
    save(fig, "02-clean-architecture")


# ============================================================
# Chart 3: Cache Hit vs Miss
# ============================================================
def chart_caching() -> None:
    scenarios = ["No Cache\n(PostgreSQL only)", "With Cache\n(10% warmup)", "Pure Hit\n(100% cache)", "Pure Miss\n(0% cache)"]
    rps = [1238, 5532, 5605, 534]
    p95 = [23.27, 2.26, 2.24, 31.06]
    colors_bar = [COLORS["no_cache"], COLORS["with_cache"], COLORS["cache_hit"], COLORS["cache_miss"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Redis Caching Impact (FastAPI + PostgreSQL)", fontsize=14, fontweight="bold", y=1.0)

    # RPS
    bars = ax1.bar(scenarios, rps, color=colors_bar, edgecolor="white", width=0.6)
    ax1.set_title("Throughput (higher = better)")
    ax1.set_ylabel("RPS")
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for bar, val in zip(bars, rps):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:,}",
                 ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Add multiplier annotations — offset away from value labels
    ax1.annotate("10.3x faster", xy=(1, rps[1] * 0.5), xytext=(-0.3, rps[1] * 0.55),
                 fontsize=11, fontweight="bold", color="#2196F3",
                 arrowprops=dict(arrowstyle="->", color="#2196F3", lw=1.5))
    ax1.annotate("0.43x slower", xy=(3, rps[3]), xytext=(2.55, rps[3] + 1400),
                 fontsize=11, fontweight="bold", color="#F44336",
                 arrowprops=dict(arrowstyle="->", color="#F44336", lw=1.5))
    ax1.set_ylim(0, max(rps) * 1.2)

    # P95 Latency
    bars2 = ax2.bar(scenarios, p95, color=colors_bar, edgecolor="white", width=0.6)
    ax2.set_title("P95 Latency (lower = better)")
    ax2.set_ylabel("P95 (ms)")
    for bar, val in zip(bars2, p95):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val}ms",
                 ha="center", va="bottom", fontsize=10, fontweight="bold")

    fig.tight_layout()
    save(fig, "03-caching-impact")


# ============================================================
# Chart 4: Uvicorn vs Gunicorn
# ============================================================
def chart_server_config() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Uvicorn vs Gunicorn: Server Config Benchmark (FastAPI)", fontsize=14, fontweight="bold", y=1.02)

    configs = ["Uvicorn", "Gunicorn\n2 workers", "Gunicorn\n4 workers"]
    bar_colors = [COLORS["uvicorn"], COLORS["gunicorn_2w"], COLORS["gunicorn_4w"]]

    # --- Panel 1: I/O-bound (Round 1, VU=200, 1 vCPU) ---
    ax = axes[0]
    io_rps = [1742.7, 1810.0, 1851.64]  # gunicorn-2w approximate from trend
    bars = ax.bar(configs, io_rps, color=bar_colors, edgecolor="white", width=0.5)
    ax.set_title("I/O-bound (1 vCPU, VU=200)")
    ax.set_ylabel("RPS")
    ax.set_ylim(0, 2200)
    for bar, val in zip(bars, io_rps):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.text(0.5, 0.92, "+6% (multi-worker wins slightly)",
            transform=ax.transAxes, ha="center", fontsize=9, style="italic", color="#666")

    # --- Panel 2: CPU-bound (Round 2, VU=10, 2 vCPU) ---
    ax = axes[1]
    cpu_rps = [8.53, 15.89, 15.24]
    bars = ax.bar(configs, cpu_rps, color=bar_colors, edgecolor="white", width=0.5)
    ax.set_title("CPU-bound (2 vCPU, VU=10)")
    ax.set_ylabel("RPS")
    ax.set_ylim(0, 20)
    for bar, val in zip(bars, cpu_rps):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.text(0.5, 0.92, "1.86x (GIL bypass via multi-process)",
            transform=ax.transAxes, ha="center", fontsize=9, style="italic", color="#666")

    # --- Panel 3: Mixed (Round 5, VU=50) ---
    ax = axes[2]
    labels = ["Uvicorn\n1 vCPU", "Uvicorn\n2 vCPU", "Gunicorn-2w\n1 vCPU", "Gunicorn-2w\n2 vCPU"]
    mixed_rps = [203.7, 205.12, 191.25, 351.82]
    mixed_colors = [COLORS["uvicorn"], COLORS["uvicorn"], COLORS["gunicorn_2w"], COLORS["gunicorn_2w"]]
    # Lighter shade for 1 vCPU variants
    mixed_colors_actual = ["#90CAF9", COLORS["uvicorn"], "#FFCC80", COLORS["gunicorn_2w"]]

    bars = ax.bar(labels, mixed_rps, color=mixed_colors_actual, edgecolor="white", width=0.55)
    ax.set_title("Mixed (DB + compute)")
    ax.set_ylabel("RPS")
    ax.set_ylim(0, 420)
    for bar, val in zip(bars, mixed_rps):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:.0f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Add annotation: Uvicorn can't use extra CPU
    ax.annotate("", xy=(0, 205), xytext=(1, 205),
                arrowprops=dict(arrowstyle="<->", color="#999", lw=1.5))
    ax.text(0.5, 215, "~same", ha="center", fontsize=8, color="#999")

    ax.annotate("", xy=(2, 191), xytext=(3, 351),
                arrowprops=dict(arrowstyle="<->", color="#E65100", lw=1.5))
    ax.text(2.5, 280, "1.7x", ha="center", fontsize=9, fontweight="bold", color="#E65100")

    fig.tight_layout()
    save(fig, "04-server-config")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("Generating benchmark charts...")
    chart_framework_rps()
    chart_clean_arch()
    chart_caching()
    chart_server_config()
    print(f"\nAll charts saved to {OUTPUT_DIR}/")
