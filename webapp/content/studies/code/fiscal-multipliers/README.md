# Fiscal Multipliers: Government Spending Categories, 2024

Output multiplier by BEA government final-demand category, using L (2024).

## Run

```bash
pip install -r requirements.txt
python analysis.py
```

## Outputs

- `outputs/fiscal.csv` — multiplier table (aggregate + individual categories)
- `outputs/fig_fiscal_mult.json` — Plotly bar chart

## Data

- `data/L_2024.csv` — 71x71 Leontief inverse (BEA, 2024)
- `data/fd_2024.csv` — Full BEA final-demand matrix (70 sectors x 19 columns)
- `data/fd_cols.csv` — F-code -> label mapping from BEA/sectors.json
- `data/sector_names.csv` — BEA sector code -> name

## Government F-codes

Federal Defense:    F06C (consumption), F06E (equipment), F06N (structures), F06S (software)
Federal Nondefense: F07C, F07E, F07N, F07S
State & Local:      F10C, F10E, F10N, F10S

## Alignment note

L has 71 sectors; FD has 70 rows. Missing from FD: `441`, `445`, `452`
(retail detail sectors not in BEA FD table; set to 0). FD rows `Other` and
`Used` have no counterpart in L and are dropped. Net intersection: 68 sectors.
The 3 missing retail sectors receive zero government final demand, which is
correct — government spending does not appear in those BEA rows.
