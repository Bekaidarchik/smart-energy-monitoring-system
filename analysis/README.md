# Analysis Workflow

The analysis script creates the simulation-first dataset, cleans the records,
calculates power and cumulative energy, generates SVG figures, and writes a
plain-text summary.

Run from the repository root:

```bash
python analysis/energy_analysis.py
```

The workflow uses only the Python standard library. No extra packages are
required.

The script regenerates `data/simulated_measurements.csv` on each run. It only
creates `data/raw_measurements.csv` when that file is missing, so real hardware
captures will not be overwritten.

## Outputs

- `data/simulated_measurements.csv`
- `data/raw_measurements.csv`
- `data/cleaned_measurements.csv`
- `figures/voltage_current_over_time.svg`
- `figures/power_over_time.svg`
- `figures/cumulative_energy.svg`
- `figures/load_comparison.svg`
- `analysis/analysis_summary.txt`
