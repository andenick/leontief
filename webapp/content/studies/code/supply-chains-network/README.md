# Supply Chains as Networks — Replication

Eigenvector centrality and supply-chain strength in the 2024 BEA input-output A-matrix.
No network libraries used — pure numpy/pandas.

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

## Outputs

| File | Description |
|---|---|
| `outputs/centrality_2024.csv` | Per-sector eigenvector centrality, in-strength, out-strength |
| `outputs/fig_centrality.json` | Plotly JSON: top-15 by eigenvector centrality (bar) |
| `outputs/fig_strength_scatter.json` | Plotly JSON: in-strength vs out-strength scatter, coloured by agg15 |

## Data

| File | Source |
|---|---|
| `data/A_square_2024.csv` | `site_data/cache/2024__A_square.parquet` (68×68 commodity-by-commodity) |
| `data/sector_agg15.csv` | `site_data/sectors.json` (code, name, agg15 group) |
| `data/sector_names.csv` | `site_data/sectors.json` (code, name only) |

## Methods

- **Eigenvector centrality**: power iteration on A until ||v_new − v|| < 1e-12
- **In-strength**: column sums of A (intermediate-input share of each sector's gross output)
- **Out-strength**: row sums of A (total intermediate sales across all buyer sectors)
- **Dominant eigenvalue**: Rayleigh quotient after convergence (~0.980 in 2024)
