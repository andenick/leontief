# Shock Propagation: Hypothetical Extraction Method

Measures each sector's systemic importance by asking: *if this sector vanished
completely — as buyer and as supplier — how much gross output would the economy lose?*

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

Outputs: `outputs/hem_2024.csv`, `outputs/fig_hem_ranking.json`

## Data

| File | Description |
|---|---|
| `data/A_square_2024.csv` | 71x71 direct-requirements matrix, 2024 (clean square, derived from BEA Leontief inverse) |
| `data/fd_agg_2024.csv` | Aggregated final demand per sector, 2024 (sum of BEA FD table columns) |
| `data/sector_names.csv` | BEA sector code to name mapping |

## Method

Complete HEM (Miller & Blair 2022, Ch. 12): for sector k, zero row k and
column k of A_square, recompute L' = (I - A')^{-1}, and measure output loss =
total(L·f) − total(L'·f). Uses numpy.linalg.inv; no scipy or networkx.
