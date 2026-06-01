# COVID Structural Shift — Replication

How COVID-19 bent the U.S. input-output structure: three structural-change metrics
computed from consecutive BEA A-matrices, 1997–2024.

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

## Outputs

| File | Description |
|---|---|
| `outputs/structural_change.csv` | Year-pair metrics with structural_distance |
| `outputs/fig_covid_shift.json` | Plotly JSON: structural distance bar chart with Lilien index overlay |

## Data

| File | Source |
|---|---|
| `data/structural_change.csv` | Exported from `Outputs/Data/structural_change_1997_2024.xlsx` |
| `data/covid_sector_shift.csv` | Exported from `Outputs/Data/covid_structural_shift.xlsx` with sector names joined |

## Methods

- **Structural distance**: $1 - \cos(\text{vec}(A_t), \text{vec}(A_{t+1}))$
- **Mean absolute change**: $\bar{d}_t = n^{-2} \sum_{ij} |a_{ij,t+1} - a_{ij,t}|$
- **Lilien index**: cross-industry dispersion of output growth rates, weighted by output shares
