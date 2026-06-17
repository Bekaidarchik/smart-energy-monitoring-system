"""Generate and analyze low-voltage smart energy monitoring data."""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "figures"
SUMMARY_PATH = ROOT / "analysis" / "analysis_summary.txt"

FIELDS = [
    "timestamp_s",
    "voltage_v",
    "current_a",
    "power_w",
    "energy_j",
    "load_type",
    "measurement_status",
    "notes",
]

LOADS = {
    "LED strip": (12.05, 0.34, 0.025, "steady low-voltage lighting load"),
    "small DC fan": (5.08, 0.26, 0.035, "startup surge then settling fan load"),
    "power resistor": (9.02, 0.12, 0.010, "stable resistive test load"),
    "pulsed load": (7.45, 0.18, 0.055, "simulated IoT-style duty cycle"),
}

COLORS = {
    "LED strip": "#2563eb",
    "small DC fan": "#16a34a",
    "power resistor": "#dc2626",
    "pulsed load": "#9333ea",
    "axis": "#334155",
    "grid": "#cbd5e1",
    "text": "#0f172a",
}


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def simulated_rows(duration_s: int = 15) -> list[dict[str, str]]:
    random.seed(219)
    rows: list[dict[str, str]] = []
    for load_name, (base_v, base_a, ripple_a, note) in LOADS.items():
        energy_j = 0.0
        previous_t = 0.0
        for sample in range(duration_s + 1):
            t = float(sample)
            voltage = base_v + 0.025 * math.sin(t / 11) + random.uniform(-0.035, 0.035)
            current = base_a + ripple_a * math.sin(t / 8) + random.uniform(-0.006, 0.006)
            if load_name == "small DC fan" and t < 12:
                current += 0.11 * math.exp(-t / 4.2)
            if load_name == "pulsed load":
                current += 0.075 if (int(t) // 10) % 2 == 0 else -0.025
            current = max(current, 0.0)
            power = voltage * current
            energy_j += power * (t - previous_t if sample else 0.0)
            previous_t = t
            rows.append(
                {
                    "timestamp_s": f"{t:.1f}",
                    "voltage_v": f"{voltage:.3f}",
                    "current_a": f"{current:.4f}",
                    "power_w": f"{power:.4f}",
                    "energy_j": f"{energy_j:.3f}",
                    "load_type": load_name,
                    "measurement_status": "simulated",
                    "notes": note,
                }
            )
    return rows


def parse_float(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
    return None


def clean_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for row in rows:
        timestamp = parse_float(row, "timestamp_s")
        timestamp_ms = parse_float(row, "timestamp_ms")
        voltage = parse_float(row, "voltage_v", "bus_voltage_v")
        current = parse_float(row, "current_a")
        current_ma = parse_float(row, "current_ma")
        if timestamp is None and timestamp_ms is not None:
            timestamp = timestamp_ms / 1000
        if current is None and current_ma is not None:
            current = current_ma / 1000
        if timestamp is None or voltage is None or current is None:
            continue
        if timestamp < 0 or voltage < 0 or current < 0:
            continue
        is_hardware = timestamp_ms is not None or current_ma is not None
        load = row.get("load_type", "").strip() or ("hardware load" if is_hardware else "unknown load")
        grouped[load].append(
            {
                "timestamp_s": timestamp,
                "voltage_v": voltage,
                "current_a": current,
                "measurement_status": row.get("measurement_status", "").strip()
                or ("measured" if is_hardware else "simulated"),
                "notes": row.get("notes", "").strip() or ("INA219 serial capture" if is_hardware else ""),
            }
        )

    clean: list[dict[str, str]] = []
    for load, load_rows in sorted(grouped.items()):
        energy_j = 0.0
        previous_t: float | None = None
        for row in sorted(load_rows, key=lambda item: float(item["timestamp_s"])):
            t = float(row["timestamp_s"])
            power = float(row["voltage_v"]) * float(row["current_a"])
            if previous_t is not None:
                energy_j += power * max(t - previous_t, 0.0)
            previous_t = t
            clean.append(
                {
                    "timestamp_s": f"{t:.1f}",
                    "voltage_v": f"{float(row['voltage_v']):.3f}",
                    "current_a": f"{float(row['current_a']):.4f}",
                    "power_w": f"{power:.4f}",
                    "energy_j": f"{energy_j:.3f}",
                    "load_type": load,
                    "measurement_status": str(row["measurement_status"]),
                    "notes": str(row["notes"]),
                }
            )
    return clean


def group_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, float | str]]]:
    grouped: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for row in rows:
        grouped[row["load_type"]].append(
            {
                "timestamp_s": float(row["timestamp_s"]),
                "voltage_v": float(row["voltage_v"]),
                "current_a": float(row["current_a"]),
                "power_w": float(row["power_w"]),
                "energy_j": float(row["energy_j"]),
                "load_type": row["load_type"],
            }
        )
    return dict(grouped)


def bounds(values: list[float], padding: float = 0.08) -> tuple[float, float]:
    low, high = min(values), max(values)
    if math.isclose(low, high):
        return low - 1, high + 1
    pad = (high - low) * padding
    return low - pad, high + pad


def points(rows: list[dict[str, float | str]], y_key: str, x: int, y: int, width: int, height: int) -> str:
    xs = [float(row["timestamp_s"]) for row in rows]
    ys = [float(row[y_key]) for row in rows]
    x_low, x_high = bounds(xs, 0)
    y_low, y_high = bounds(ys)
    mapped = []
    for xv, yv in zip(xs, ys):
        px = x + (xv - x_low) / (x_high - x_low) * width
        py = y + height - (yv - y_low) / (y_high - y_low) * height
        mapped.append(f"{px:.1f},{py:.1f}")
    return " ".join(mapped)


def svg_header(title: str, subtitle: str, width: int = 900, height: int = 520) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title>{title}</title>",
        f"<desc>{subtitle}</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="36" y="38" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="{COLORS["text"]}">{title}</text>',
        f'<text x="36" y="62" font-family="Arial, sans-serif" font-size="13" fill="#475569">{subtitle}</text>',
    ]


def axes(parts: list[str], x: int, y: int, width: int, height: int, y_label: str) -> None:
    for i in range(5):
        gy = y + i * height / 4
        parts.append(f'<line x1="{x}" y1="{gy:.1f}" x2="{x + width}" y2="{gy:.1f}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
    parts.append(f'<line x1="{x}" y1="{y + height}" x2="{x + width}" y2="{y + height}" stroke="{COLORS["axis"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + height}" stroke="{COLORS["axis"]}" stroke-width="1.5"/>')
    parts.append(f'<text x="{x - 10}" y="{y + height / 2}" transform="rotate(-90 {x - 10} {y + height / 2})" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["axis"]}">{y_label}</text>')
    parts.append(f'<text x="{x + width / 2}" y="{y + height + 36}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["axis"]}">Time (seconds)</text>')


def save_line_chart(grouped: dict[str, list[dict[str, float | str]]], filename: str, title: str, subtitle: str, y_key: str, y_label: str) -> None:
    parts = svg_header(title, subtitle)
    x, y, width, height = 82, 92, 758, 320
    axes(parts, x, y, width, height, y_label)
    for index, (load, rows) in enumerate(grouped.items()):
        color = COLORS.get(load, "#475569")
        parts.append(f'<polyline points="{points(rows, y_key, x, y, width, height)}" fill="none" stroke="{color}" stroke-width="2.8"/>')
        lx = 90 + index * 190
        parts.append(f'<rect x="{lx}" y="446" width="18" height="4" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{lx + 26}" y="454" font-family="Arial, sans-serif" font-size="13" fill="{COLORS["text"]}">{load}</text>')
    parts.append("</svg>")
    (FIGURES_DIR / filename).write_text("\n".join(parts), encoding="utf-8")


def save_voltage_current(grouped: dict[str, list[dict[str, float | str]]]) -> None:
    rows = grouped["small DC fan"]
    parts = svg_header("Voltage and Current Over Time", "Representative low-voltage fan profile from the simulation-first dataset.")
    top, bottom = (80, 92, 760, 150), (80, 310, 760, 150)
    axes(parts, *top, "Voltage (V)")
    axes(parts, *bottom, "Current (A)")
    parts.append(f'<polyline points="{points(rows, "voltage_v", *top)}" fill="none" stroke="#0f766e" stroke-width="3"/>')
    parts.append(f'<polyline points="{points(rows, "current_a", *bottom)}" fill="none" stroke="#b45309" stroke-width="3"/>')
    parts.append('<text x="720" y="112" font-family="Arial, sans-serif" font-size="13" fill="#0f766e">Voltage</text>')
    parts.append('<text x="720" y="330" font-family="Arial, sans-serif" font-size="13" fill="#b45309">Current</text>')
    parts.append("</svg>")
    (FIGURES_DIR / "voltage_current_over_time.svg").write_text("\n".join(parts), encoding="utf-8")


def save_load_comparison(grouped: dict[str, list[dict[str, float | str]]]) -> None:
    parts = svg_header("Load Comparison", "Average power and total energy for each simulated low-voltage load.")
    x0, y0, plot_h, bar_w = 140, 96, 300, 72
    averages = [(load, mean(float(row["power_w"]) for row in rows)) for load, rows in grouped.items()]
    max_power = max(value for _, value in averages) * 1.15
    parts.append(f'<line x1="96" y1="{y0 + plot_h}" x2="835" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1.5"/>')
    parts.append(f'<line x1="96" y1="{y0}" x2="96" y2="{y0 + plot_h}" stroke="{COLORS["axis"]}" stroke-width="1.5"/>')
    for index, (load, avg_power) in enumerate(averages):
        x = x0 + index * 160
        h = avg_power / max_power * plot_h
        y = y0 + plot_h - h
        energy_wh = float(grouped[load][-1]["energy_j"]) / 3600
        color = COLORS.get(load, "#475569")
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}" rx="4"/>')
        parts.append(f'<text x="{x + bar_w / 2}" y="{y - 10:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="{COLORS["text"]}">{avg_power:.2f} W</text>')
        parts.append(f'<text x="{x + bar_w / 2}" y="{y0 + plot_h + 24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["text"]}">{load}</text>')
        parts.append(f'<text x="{x + bar_w / 2}" y="{y0 + plot_h + 44}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#64748b">{energy_wh:.3f} Wh</text>')
    parts.append('<text x="86" y="246" transform="rotate(-90 86 246)" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#334155">Average power (W)</text>')
    parts.append("</svg>")
    (FIGURES_DIR / "load_comparison.svg").write_text("\n".join(parts), encoding="utf-8")


def write_summary(grouped: dict[str, list[dict[str, float | str]]]) -> None:
    lines = [
        "Smart Energy Monitoring System - Analysis Summary",
        "=" * 54,
        "",
        "Dataset status: simulation-first. No real hardware measurements are claimed.",
        "Sampling interval: 1 second.",
        "Measurement model: safe low-voltage DC loads using the same voltage, current, power, and energy calculations planned for an INA219 hardware prototype.",
        "",
        "Per-load results:",
    ]
    for load, rows in grouped.items():
        powers = [float(row["power_w"]) for row in rows]
        voltages = [float(row["voltage_v"]) for row in rows]
        currents = [float(row["current_a"]) for row in rows]
        energy_j = float(rows[-1]["energy_j"])
        lines.extend(
            [
                f"- {load}:",
                f"  average voltage = {mean(voltages):.3f} V",
                f"  average current = {mean(currents):.4f} A",
                f"  average power   = {mean(powers):.3f} W",
                f"  peak power      = {max(powers):.3f} W",
                f"  total energy    = {energy_j:.2f} J ({energy_j / 3600:.4f} Wh)",
            ]
        )
    highest = max(grouped, key=lambda name: mean(float(row["power_w"]) for row in grouped[name]))
    lines.extend(
        [
            "",
            f"Highest average simulated power: {highest}.",
            "Main takeaway: the workflow converts sensor-style voltage and current samples into power, cumulative energy, and comparison plots that can be reused unchanged once real INA219 data is collected.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    simulated = simulated_rows()
    write_csv(DATA_DIR / "simulated_measurements.csv", simulated)
    raw_path = DATA_DIR / "raw_measurements.csv"
    if not raw_path.exists():
        write_csv(raw_path, simulated)
    clean = clean_rows(read_csv(raw_path))
    write_csv(DATA_DIR / "cleaned_measurements.csv", clean)
    grouped = group_rows(clean)
    save_voltage_current(grouped)
    save_line_chart(grouped, "power_over_time.svg", "Power Over Time", "Calculated power from voltage and current for each low-voltage load.", "power_w", "Power (W)")
    save_line_chart(grouped, "cumulative_energy.svg", "Cumulative Energy", "Energy is accumulated from power and sampling interval, reported in joules.", "energy_j", "Energy (J)")
    save_load_comparison(grouped)
    write_summary(grouped)
    print(f"Wrote {len(clean)} cleaned rows")
    print(f"Figures: {FIGURES_DIR}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
