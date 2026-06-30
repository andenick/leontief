# Study 10: A Marxian Profit Rate from the Input-Output Table

Replication bundle for the Leontief I-O study *"A Marxian Profit Rate from the Input-Output Table"*.

## Quick start

```bash
pip install -r requirements.txt
python analysis.py
```

Or open `analysis.ipynb` in Jupyter for an interactive walkthrough.

## What this computes

1. **Labor values** (2024): `lambda = l @ (I-A)^{-1}` where `l = V001/x`.
2. **Profit-rate proxy trend** (1997–2024): `r = S / (C + V)` using
   - V = total V001 (compensation)
   - S = total V003 (gross operating surplus)
   - C = total T005 (intermediate input *flow* proxy; NOT fixed-capital stock)
3. **Value vs. price scatter** (2024): normalized labor values vs VA-per-unit proxy.

**PROXY NOTE**: C is a *flow* measure, not a capital stock. Level of r is upward-biased
relative to stock-based estimates. Trend is qualitatively robust. See study narrative
for full proxy accounting.

## Data sources

| File | Description |
|---|---|
| `data/A_square_2024.csv` | 68×68 A matrix, BEA 2024 |
| `data/value_added_2024.csv` | V001, V003, VABAS, VAPRO × 68 sectors |
| `data/total_output_2024.csv` | Gross output by sector (T018 from Use table) |
| `data/profit_rate_timeseries.csv` | Aggregates V, S, C, r for each year 1997–2024 |
| `data/sector_names.csv` | BEA sector code → name |

## Outputs

| File | Description |
|---|---|
| `outputs/marx.csv` | Per-sector: labor values, price proxy, deviation (2024) |
| `outputs/fig_profit_rate_trend.json` | Plotly: aggregate profit-rate proxy 1997–2024 |
| `outputs/fig_value_price_deviation.json` | Plotly: value vs price scatter, 2024 |

## References

- Shaikh (2016). *Capitalism: Competition, Conflict, Crises*
- Pasinetti (1981). *Structural Change and Economic Growth*
