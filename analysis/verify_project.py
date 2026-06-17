"""Verify the portfolio project against the starter brief.

The checks are intentionally small and direct. They prove that the expected
files exist, generated data follows the required schema, plots are valid SVG,
and the documentation keeps the low-voltage safety boundary clear.
"""

from __future__ import annotations

import csv
import math
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "verification_report.md"

DATA_COLUMNS = [
    "timestamp_s",
    "voltage_v",
    "current_a",
    "power_w",
    "energy_j",
    "load_type",
    "measurement_status",
    "notes",
]

REQUIRED_FILES = [
    "README.md",
    "hardware/materials_list.md",
    "hardware/circuit_notes.md",
    "hardware/wiring_diagram.svg",
    "hardware/prototype_photos/README.md",
    "arduino/energy_logger_ina219.ino",
    "data/README.md",
    "data/raw_measurements.csv",
    "data/cleaned_measurements.csv",
    "data/simulated_measurements.csv",
    "analysis/energy_analysis.py",
    "analysis/analysis_summary.txt",
    "analysis/README.md",
    "figures/voltage_current_over_time.svg",
    "figures/power_over_time.svg",
    "figures/cumulative_energy.svg",
    "figures/load_comparison.svg",
    "docs/reviewer_summary.md",
    "docs/portfolio_publish.md",
    "paper/project_summary.md",
]

README_SECTIONS = [
    "Why This Project Matters",
    "Prototype Overview",
    "Hardware Design",
    "Circuit Safety Note",
    "Data Collection Method",
    "Analysis and Results",
    "Current Status",
    "Limitations",
    "Future Improvements",
    "Repository Structure",
    "Skills Demonstrated",
    "How to Run the Analysis",
    "For Reviewers",
]


def pass_fail(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_required_files() -> tuple[bool, str]:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        return False, "Missing files: " + ", ".join(missing)
    return True, f"All {len(REQUIRED_FILES)} required files are present."


def check_csv_schema_and_math() -> tuple[bool, str]:
    csv_path = ROOT / "data" / "cleaned_measurements.csv"
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if reader.fieldnames != DATA_COLUMNS:
        return False, f"Unexpected CSV columns: {reader.fieldnames}"
    if len(rows) < 30:
        return False, f"Expected a useful dataset, found only {len(rows)} rows."

    allowed_status = {"measured", "simulated", "placeholder"}
    grouped: dict[str, list[dict[str, float]]] = defaultdict(list)

    for index, row in enumerate(rows, start=2):
        try:
            timestamp_s = float(row["timestamp_s"])
            voltage_v = float(row["voltage_v"])
            current_a = float(row["current_a"])
            power_w = float(row["power_w"])
            energy_j = float(row["energy_j"])
        except ValueError:
            return False, f"Non-numeric measurement value on CSV line {index}."

        if row["measurement_status"] not in allowed_status:
            return False, f"Unexpected measurement_status on CSV line {index}."
        if timestamp_s < 0 or voltage_v < 0 or current_a < 0 or power_w < 0 or energy_j < 0:
            return False, f"Negative measurement value on CSV line {index}."
        if not math.isclose(power_w, voltage_v * current_a, rel_tol=0.0015, abs_tol=0.001):
            return False, f"Power does not match V*I on CSV line {index}."

        grouped[row["load_type"]].append(
            {
                "timestamp_s": timestamp_s,
                "energy_j": energy_j,
            }
        )

    if len(grouped) < 3:
        return False, f"Expected comparison data for at least 3 loads, found {len(grouped)}."

    for load_type, load_rows in grouped.items():
        previous_time = -1.0
        previous_energy = -1.0
        for row in load_rows:
            if row["timestamp_s"] < previous_time:
                return False, f"Timestamps are not sorted for {load_type}."
            if row["energy_j"] < previous_energy:
                return False, f"Energy is not cumulative for {load_type}."
            previous_time = row["timestamp_s"]
            previous_energy = row["energy_j"]
        if load_rows[-1]["energy_j"] <= 0:
            return False, f"Final energy is not positive for {load_type}."

    return True, f"CSV schema, statuses, V*I power, and cumulative energy pass for {len(rows)} rows across {len(grouped)} loads."


def check_svg_files() -> tuple[bool, str]:
    svg_paths = [
        "figures/voltage_current_over_time.svg",
        "figures/power_over_time.svg",
        "figures/cumulative_energy.svg",
        "figures/load_comparison.svg",
        "hardware/wiring_diagram.svg",
    ]
    for path in svg_paths:
        root = ET.parse(ROOT / path).getroot()
        if not root.tag.endswith("svg"):
            return False, f"{path} is not an SVG document."
    return True, f"All {len(svg_paths)} SVG files parse as XML."


def check_readme_sections() -> tuple[bool, str]:
    readme = read_text("README.md")
    missing = [section for section in README_SECTIONS if f"## {section}" not in readme]
    if missing:
        return False, "README is missing sections: " + ", ".join(missing)
    return True, "README contains every required section from the starter brief."


def check_arduino_logger() -> tuple[bool, str]:
    sketch = read_text("arduino/energy_logger_ina219.ino")
    required_snippets = [
        "Adafruit_INA219",
        "ina219.begin()",
        "timestamp_ms,voltage_v,current_ma,power_mw",
        "getBusVoltage_V()",
        "getCurrent_mA()",
        "getPower_mW()",
        "Serial.print",
    ]
    missing = [snippet for snippet in required_snippets if snippet not in sketch]
    if missing:
        return False, "Arduino logger is missing: " + ", ".join(missing)
    return True, "Arduino INA219 logger initializes the sensor, reads voltage/current/power, and prints CSV rows."


def check_safety_language() -> tuple[bool, str]:
    combined = "\n".join(
        read_text(path)
        for path in [
            "README.md",
            "hardware/circuit_notes.md",
            "hardware/materials_list.md",
            "paper/project_summary.md",
        ]
    ).lower()
    required_phrases = ["low-voltage dc", "do not connect", "mains"]
    missing = [phrase for phrase in required_phrases if phrase not in combined]
    if missing:
        return False, "Safety documentation is missing: " + ", ".join(missing)
    forbidden_claims = ["monitors my whole house", "measures mains electricity."]
    found = [claim for claim in forbidden_claims if claim in combined]
    if found:
        return False, "Forbidden or misleading claim found: " + ", ".join(found)
    return True, "Safety wording clearly limits the project to low-voltage DC loads."


def check_publish_metadata() -> tuple[bool, str]:
    publish = read_text("docs/portfolio_publish.md")
    required = [
        "smart-energy-monitoring-system",
        "Low-cost Arduino/ESP32 energy monitoring prototype",
        "second pinned GitHub project after EcoStep",
    ]
    missing = [text for text in required if text not in publish]
    if missing:
        return False, "Portfolio publishing guide is missing: " + ", ".join(missing)
    return True, "Portfolio publishing guide records the repo name, description, and pinning position."


def main() -> int:
    checks = [
        ("Repository structure", check_required_files),
        ("CSV data and calculations", check_csv_schema_and_math),
        ("SVG outputs", check_svg_files),
        ("README sections", check_readme_sections),
        ("Arduino logger", check_arduino_logger),
        ("Safety language", check_safety_language),
        ("Portfolio publishing metadata", check_publish_metadata),
    ]

    report_lines = [
        "# Verification Report",
        "",
        "Generated by `python analysis/verify_project.py`.",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]

    all_passed = True
    for name, check in checks:
        passed, evidence = check()
        all_passed = all_passed and passed
        report_lines.append(f"| {name} | {pass_fail(passed)} | {evidence} |")

    report_lines.extend(
        [
            "",
            "External GitHub publishing note: this verifier confirms the local repository package. The repository has been created at https://github.com/Bekaidarchik/smart-energy-monitoring-system. Profile pinning after EcoStep must be completed from the GitHub profile customization UI.",
        ]
    )

    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(REPORT_PATH)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
