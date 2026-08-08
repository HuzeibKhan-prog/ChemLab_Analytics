
# 🧪 ChemLab Analytics

**A Web-Based Chemistry and Mathematical Data Analysis System**

A Flask web app for students to perform chemistry calculations, run
mathematical/statistical analysis, analyze uploaded lab data, and visualize
results — no database required.

## Modules

1. **Chemistry Calculator** — molecular mass, moles ↔ mass, molarity,
   dilution, density, percentage concentration, ideal gas law, basic
   stoichiometry.
2. **Mathematics & Statistics** — mean, median, mode, variance, standard
   deviation, percentage, correlation, basic equations, function graphing.
3. **Laboratory Data Analyzer** — upload a CSV of experimental readings;
   Pandas computes average/max/min/std dev/correlation and Matplotlib/
   Seaborn render charts.
4. **Visualization** — line charts, bar charts, scatter plots, distribution
   plots, and correlation heatmaps.
5. **Experiment Analysis** — guided predefined experiments: temperature vs
   reaction rate, concentration vs reaction rate, titration analysis,
   density experiment, and a simple gas-law experiment.

## Setup

```bash
cd ChemLab_Analytics
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Project structure

```
ChemLab_Analytics/
├── app.py                     # Flask app + all API routes
├── requirements.txt
├── data/
│   └── experiments.csv        # bundled sample dataset
├── analysis/
│   ├── chemistry.py           # chemistry calculation engine
│   ├── mathematics.py         # stats / equations / function eval
│   └── data_analysis.py       # Pandas summaries + Matplotlib/Seaborn charts
├── templates/
│   ├── base.html              # shared shell (sidebar nav)
│   ├── index.html             # dashboard
│   ├── chemistry.html
│   ├── mathematics.html
│   ├── analyzer.html
│   └── experiments.html
├── static/
│   ├── css/style.css
│   └── js/script.js
└── graphs/                    # (reserved for saved chart exports)
```

## How it works

- The **frontend** (HTML/CSS/JS) posts form values to JSON API endpoints
  under `/api/...`.
- **Flask** routes in `app.py` validate input and call into the
  `analysis/` package.
- **Chemistry** calculations are pure Python (formula parsing supports
  nested parentheses, e.g. `Al2(SO4)3`).
- **Statistics** use Python's `statistics` module plus NumPy for
  correlation.
- **CSV analysis** uses Pandas to compute summary statistics and
  correlation matrices; the most recently uploaded dataset is kept in
  memory for chart generation (no database — single-process only).
- **Charts** are rendered server-side with Matplotlib/Seaborn, encoded as
  base64 PNGs, and streamed directly into the page — no chart files are
  written to disk unless you choose to save the image yourself.

## Notes

- All numeric solvers (dilution, density, % concentration, ideal gas law)
  accept "solve for the blank field" style input — leave whichever value
  is unknown empty and the others filled in.
- The bundled sample dataset (`data/experiments.csv`) matches the module 3
  example: `Temperature,Reaction_Rate`.
- No external services or database are used — everything runs locally.

## Author 

- Huzeib Khan
