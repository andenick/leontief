# Key Sectors: Rasmussen Linkage Indices

## What it shows

Using the Leontief inverse $L$ for 2024 (and 2002 for comparison), this script computes
Rasmussen backward and forward linkage indices for all 71 BEA Summary sectors.

- **Backward linkage** (power of dispersion): how strongly does sector $j$ pull from suppliers?
- **Forward linkage** (sensitivity of dispersion): how widely does sector $i$ feed into downstream industries?

"Key sectors" are those with both indices above 1 — the economy's strategic hinges.

## Quick start

```bash
pip install -r requirements.txt
python analysis.py
```

## Data directory

| File | Description |
|---|---|
| `data/L_2024.csv` | 71×71 Leontief inverse, 2024 (exported from site_data cache) |
| `data/L_2002.csv` | 71×71 Leontief inverse, 2002 (for comparison) |
| `data/sector_names.csv` | BEA sector code → name mapping |

## Outputs

| File | Description |
|---|---|
| `outputs/linkages_2024.csv` | Sector, name, backward, forward, is_key |
| `outputs/fig_linkage_scatter.json` | Plotly scatter: BL vs FL, 2024 |
| `outputs/fig_key_sectors_bar.json` | Plotly bar: top-15 combined linkage, 2024 |
