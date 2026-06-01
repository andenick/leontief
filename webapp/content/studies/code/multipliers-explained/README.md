# Multipliers Explained: Output Multiplier Distribution and Trend

## What it shows

The output multiplier of sector $j$ is the column sum of the Leontief inverse:
$m_j = \sum_i L_{ij}$. It answers: "If final demand for sector $j$ rises by $1,
by how much does total economy-wide output rise?"

This script shows:
1. The cross-sector distribution for 2024 (top and bottom 10 sectors)
2. The economy-wide mean multiplier trend from 1997 to 2024

## Quick start

```bash
pip install -r requirements.txt
python analysis.py
```

## Data directory

| File | Description |
|---|---|
| `data/L_2024.csv` | 71×71 Leontief inverse, 2024 |
| `data/multiplier_timeseries.csv` | Year + 71 sector multiplier columns, 1997-2024 |
| `data/sector_names.csv` | BEA sector code → name mapping |

## Outputs

| File | Description |
|---|---|
| `outputs/multipliers_2024.csv` | Rank, sector, name, multiplier (2024) |
| `outputs/fig_mult_rank_2024.json` | Plotly bar: top & bottom 10 sectors, 2024 |
| `outputs/fig_mult_trend.json` | Plotly line: mean multiplier per year, 1997-2024 |
