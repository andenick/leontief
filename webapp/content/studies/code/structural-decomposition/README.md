# Structural Decomposition Analysis, 1997–2024

Three-term SDA of U.S. output change: technology effect vs. final-demand effect.

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

## Outputs

- `outputs/sda.csv` — 71-sector decomposition table
- `outputs/fig_sda_contributions.json` — Plotly figure: aggregate demand vs technology bar

## Data

- `data/L_1997.csv` — 71x71 Leontief inverse (BEA, 1997)
- `data/L_2024.csv` — 71x71 Leontief inverse (BEA, 2024)
- `data/fd_1997.csv` — Aggregated final-demand vector, 1997 (row-sum of BEA FD matrix, aligned to L's 71-sector index)
- `data/fd_2024.csv` — Aggregated final-demand vector, 2024
- `data/sector_names.csv` — BEA sector code -> name

## Alignment note

The BEA final-demand (FD) table has 70 sector rows; L has 71 sectors.
Missing from FD: `441` (Motor vehicle and parts dealers), `445` (Food and
beverage stores), `452` (General merchandise stores). These three retail
detail sectors receive `f = 0` in both period vectors — they have no row in
the BEA FD table. Two FD rows (`Other`, `Used`) have no counterpart in L
and are dropped. Net usable intersection: 68 sectors.
