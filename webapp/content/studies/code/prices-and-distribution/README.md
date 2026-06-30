# Study 9: Cost-Push Prices and the Wage Share

Replication bundle for the Leontief I-O study *"Cost-Push Prices and the Wage Share"*.

## Quick start

```bash
pip install -r requirements.txt
python analysis.py
```

Or open `analysis.ipynb` in Jupyter for an interactive walkthrough.

## What this computes

1. **Baseline price vector** from the cost-push model: `p = v @ (I-A)^{-1}`
   where `v_j = (V001_j + V003_j) / x_j` (unit value added per sector).
2. **+10% wage shock**: applies `delta_v = 0.10 * comp_coeff` and computes
   price changes `delta_p = delta_v @ (I-A)^{-1}`.
3. **Labor share trend** 1997–2024 from pre-exported BEA data.

## Data sources

| File | Description |
|---|---|
| `data/A_square_2024.csv` | 68×68 technical coefficients (A_square), BEA 2024 |
| `data/value_added_2024.csv` | V001, V003, VABAS, VAPRO × 68 sectors |
| `data/total_output_2024.csv` | Gross output by sector (T018 from Use table) |
| `data/labor_share.csv` | Economy-wide labor share 1997–2024 |
| `data/sector_names.csv` | BEA sector code → name |

## Outputs

| File | Description |
|---|---|
| `outputs/prices.csv` | Per-sector baseline price, shocked price, Δp (%) |
| `outputs/fig_price_passthrough.json` | Plotly: top-15 sectors by price increase |
| `outputs/fig_labor_share_trend.json` | Plotly: labor share 1997–2024 |

## References

- Miller & Blair (2022). *Input-Output Analysis* (3rd ed.)
- Pasinetti (1981). *Structural Change and Economic Growth*
- Godley & Lavoie (2007). *Monetary Economics*
- Shaikh (2016). *Capitalism: Competition, Conflict, Crises*
