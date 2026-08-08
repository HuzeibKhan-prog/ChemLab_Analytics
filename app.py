"""
ChemLab Analytics
A Web-Based Chemistry and Mathematical Data Analysis System

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import io
import os

import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file

from analysis import chemistry as chem
from analysis import mathematics as mathmod
from analysis import data_analysis as dataan

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload cap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(BASE_DIR, "data", "experiments.csv")

# In-memory store for the most recently uploaded dataset (per-process, no DB)
LAST_DATASET = {"df": None, "filename": None}


def err(message, code=400):
    return jsonify({"ok": False, "error": message}), code


def ok(payload):
    return jsonify({"ok": True, **payload})


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chemistry")
def chemistry_page():
    return render_template("chemistry.html")


@app.route("/mathematics")
def mathematics_page():
    return render_template("mathematics.html")


@app.route("/analyzer")
def analyzer_page():
    return render_template("analyzer.html")


@app.route("/experiments")
def experiments_page():
    return render_template("experiments.html")


# ---------------------------------------------------------------------------
# API — Chemistry Calculator
# ---------------------------------------------------------------------------
@app.route("/api/chemistry/molecular-mass", methods=["POST"])
def api_molecular_mass():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = chem.molecular_mass(data.get("formula", ""))
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))


@app.route("/api/chemistry/moles-mass", methods=["POST"])
def api_moles_mass():
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode")
    try:
        molar_mass = float(data.get("molar_mass"))
        if mode == "to_moles":
            mass = float(data.get("mass"))
            moles = chem.moles_from_mass(mass, molar_mass)
            return ok({"moles": round(moles, 6), "mass": mass, "molar_mass": molar_mass})
        elif mode == "to_mass":
            moles = float(data.get("moles"))
            mass = chem.mass_from_moles(moles, molar_mass)
            return ok({"mass": round(mass, 6), "moles": moles, "molar_mass": molar_mass})
        return err("mode must be 'to_moles' or 'to_mass'.")
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/molarity", methods=["POST"])
def api_molarity():
    data = request.get_json(force=True, silent=True) or {}
    try:
        moles = float(data.get("moles"))
        volume = float(data.get("volume_l"))
        result = chem.molarity(moles, volume)
        return ok({"molarity": round(result, 6)})
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/dilution", methods=["POST"])
def api_dilution():
    data = request.get_json(force=True, silent=True) or {}
    try:
        parsed = {k: (float(v) if v not in (None, "",) else None)
                  for k, v in {"c1": data.get("c1"), "v1": data.get("v1"),
                                "c2": data.get("c2"), "v2": data.get("v2")}.items()}
        result = chem.dilution(**parsed)
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/density", methods=["POST"])
def api_density():
    data = request.get_json(force=True, silent=True) or {}
    try:
        parsed = {k: (float(v) if v not in (None, "") else None)
                  for k, v in {"mass": data.get("mass"), "volume": data.get("volume"),
                                "density_val": data.get("density")}.items()}
        result = chem.density(**parsed)
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/percent-concentration", methods=["POST"])
def api_percent_concentration():
    data = request.get_json(force=True, silent=True) or {}
    try:
        parsed = {k: (float(v) if v not in (None, "") else None)
                  for k, v in {"solute_mass": data.get("solute_mass"),
                                "solution_mass": data.get("solution_mass"),
                                "percent": data.get("percent")}.items()}
        result = chem.percent_concentration(**parsed)
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/ideal-gas", methods=["POST"])
def api_ideal_gas():
    data = request.get_json(force=True, silent=True) or {}
    try:
        parsed = {k: (float(v) if v not in (None, "") else None)
                  for k, v in {"p": data.get("p"), "v": data.get("v"),
                                "n": data.get("n"), "t": data.get("t")}.items()}
        result = chem.ideal_gas_law(**parsed)
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/chemistry/stoichiometry", methods=["POST"])
def api_stoichiometry():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = chem.stoichiometry(
            mass_a=float(data.get("mass_a")),
            molar_mass_a=float(data.get("molar_mass_a")),
            molar_mass_b=float(data.get("molar_mass_b")),
            coeff_a=float(data.get("coeff_a", 1)),
            coeff_b=float(data.get("coeff_b", 1)),
        )
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


# ---------------------------------------------------------------------------
# API — Mathematics & Statistics
# ---------------------------------------------------------------------------
@app.route("/api/math/stats", methods=["POST"])
def api_math_stats():
    data = request.get_json(force=True, silent=True) or {}
    try:
        values = data.get("values", [])
        return ok(mathmod.summary_stats(values))
    except mathmod.MathError as e:
        return err(str(e))


@app.route("/api/math/percentage", methods=["POST"])
def api_math_percentage():
    data = request.get_json(force=True, silent=True) or {}
    try:
        part = float(data.get("part"))
        whole = float(data.get("whole"))
        return ok({"percentage": mathmod.percentage(part, whole)})
    except mathmod.MathError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/math/correlation", methods=["POST"])
def api_math_correlation():
    data = request.get_json(force=True, silent=True) or {}
    try:
        r = mathmod.correlation(data.get("x", []), data.get("y", []))
        return ok({"correlation": r})
    except mathmod.MathError as e:
        return err(str(e))


@app.route("/api/math/equation", methods=["POST"])
def api_math_equation():
    data = request.get_json(force=True, silent=True) or {}
    eq_type = data.get("type")
    try:
        if eq_type == "linear":
            result = mathmod.solve_linear(float(data.get("a")), float(data.get("b")))
        elif eq_type == "quadratic":
            result = mathmod.solve_quadratic(float(data.get("a")), float(data.get("b")), float(data.get("c")))
        else:
            return err("type must be 'linear' or 'quadratic'.")
        return ok(result)
    except (TypeError, ValueError):
        return err("Please provide valid numeric coefficients.")


@app.route("/api/math/graph", methods=["POST"])
def api_math_graph():
    data = request.get_json(force=True, silent=True) or {}
    try:
        expr = data.get("expression", "")
        x_min = float(data.get("x_min", -10))
        x_max = float(data.get("x_max", 10))
        points = int(data.get("points", 200))
        result = mathmod.evaluate_function(expr, x_min, x_max, points)
        return ok(result)
    except mathmod.MathError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric range values.")


# ---------------------------------------------------------------------------
# API — Laboratory Data Analyzer
# ---------------------------------------------------------------------------
@app.route("/api/analyzer/upload", methods=["POST"])
def api_analyzer_upload():
    if "file" not in request.files:
        return err("No file uploaded. Use form field name 'file'.")
    f = request.files["file"]
    if f.filename == "":
        return err("No file selected.")
    try:
        df = dataan.load_csv(f.stream)
    except dataan.DataAnalysisError as e:
        return err(str(e))
    LAST_DATASET["df"] = df
    LAST_DATASET["filename"] = f.filename
    try:
        summary = dataan.describe_dataframe(df)
    except dataan.DataAnalysisError as e:
        return err(str(e))
    return ok({"filename": f.filename, "summary": summary})


@app.route("/api/analyzer/sample", methods=["POST"])
def api_analyzer_sample():
    df = dataan.load_csv(SAMPLE_CSV)
    LAST_DATASET["df"] = df
    LAST_DATASET["filename"] = "experiments.csv (sample)"
    summary = dataan.describe_dataframe(df)
    return ok({"filename": "experiments.csv (sample)", "summary": summary})


@app.route("/api/analyzer/chart", methods=["POST"])
def api_analyzer_chart():
    data = request.get_json(force=True, silent=True) or {}
    df = LAST_DATASET["df"]
    if df is None:
        return err("Upload a CSV or load the sample dataset first.")
    chart_type = data.get("chart_type")
    x_col = data.get("x_col")
    y_col = data.get("y_col")
    try:
        if chart_type == "line":
            img = dataan.make_line_chart(df, x_col, y_col)
        elif chart_type == "bar":
            img = dataan.make_bar_chart(df, x_col, y_col)
        elif chart_type == "scatter":
            img = dataan.make_scatter_chart(df, x_col, y_col)
        elif chart_type == "distribution":
            img = dataan.make_distribution_chart(df, x_col)
        elif chart_type == "heatmap":
            img = dataan.make_correlation_heatmap(df)
        else:
            return err("Unknown chart_type.")
        return ok({"image_base64": img})
    except (dataan.DataAnalysisError, KeyError) as e:
        return err(str(e))


# ---------------------------------------------------------------------------
# API — Predefined Experiments
# ---------------------------------------------------------------------------
@app.route("/api/experiments/temperature-rate", methods=["POST"])
def api_exp_temp_rate():
    """Temperature vs reaction rate: fit + correlation + chart."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        temps = [float(v) for v in data.get("temperature", [])]
        rates = [float(v) for v in data.get("rate", [])]
        if len(temps) != len(rates) or len(temps) < 2:
            return err("Provide matching temperature and rate readings (at least 2 pairs).")
        df = pd.DataFrame({"Temperature": temps, "Reaction_Rate": rates})
        r = mathmod.correlation(temps, rates)
        img = dataan.make_scatter_chart(df, "Temperature", "Reaction_Rate",
                                         title="Effect of Temperature on Reaction Rate")
        return ok({"correlation": r, "image_base64": img, "n": len(temps)})
    except (mathmod.MathError, ValueError, TypeError) as e:
        return err(str(e))


@app.route("/api/experiments/concentration-rate", methods=["POST"])
def api_exp_conc_rate():
    data = request.get_json(force=True, silent=True) or {}
    try:
        conc = [float(v) for v in data.get("concentration", [])]
        rates = [float(v) for v in data.get("rate", [])]
        if len(conc) != len(rates) or len(conc) < 2:
            return err("Provide matching concentration and rate readings (at least 2 pairs).")
        df = pd.DataFrame({"Concentration": conc, "Reaction_Rate": rates})
        r = mathmod.correlation(conc, rates)
        img = dataan.make_scatter_chart(df, "Concentration", "Reaction_Rate",
                                         title="Concentration vs Reaction Rate")
        return ok({"correlation": r, "image_base64": img, "n": len(conc)})
    except (mathmod.MathError, ValueError, TypeError) as e:
        return err(str(e))


@app.route("/api/experiments/titration", methods=["POST"])
def api_exp_titration():
    """Titration analysis: find concentration of unknown via M1V1 = M2V2 at equivalence point."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        known_molarity = float(data.get("known_molarity"))
        known_volume = float(data.get("known_volume_ml"))
        unknown_volume = float(data.get("unknown_volume_ml"))
        if unknown_volume <= 0:
            return err("Unknown volume must be greater than zero.")
        unknown_molarity = (known_molarity * known_volume) / unknown_volume
        return ok({
            "unknown_molarity": round(unknown_molarity, 6),
            "known_molarity": known_molarity,
            "known_volume_ml": known_volume,
            "unknown_volume_ml": unknown_volume,
        })
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


@app.route("/api/experiments/density-exp", methods=["POST"])
def api_exp_density():
    data = request.get_json(force=True, silent=True) or {}
    try:
        masses = [float(v) for v in data.get("mass", [])]
        volumes = [float(v) for v in data.get("volume", [])]
        if len(masses) != len(volumes) or len(masses) < 1:
            return err("Provide matching mass and volume readings.")
        densities = [round(m / v, 5) for m, v in zip(masses, volumes) if v != 0]
        avg_density = round(sum(densities) / len(densities), 5) if densities else None
        df = pd.DataFrame({"Trial": [f"Trial {i+1}" for i in range(len(masses))],
                            "Density": densities})
        img = dataan.make_bar_chart(df, "Trial", "Density", title="Density Across Trials")
        return ok({"densities": densities, "average_density": avg_density, "image_base64": img})
    except (dataan.DataAnalysisError, ValueError, TypeError) as e:
        return err(str(e))


@app.route("/api/experiments/gas-law", methods=["POST"])
def api_exp_gas_law():
    data = request.get_json(force=True, silent=True) or {}
    try:
        parsed = {k: (float(v) if v not in (None, "") else None)
                  for k, v in {"p": data.get("p"), "v": data.get("v"),
                                "n": data.get("n"), "t": data.get("t")}.items()}
        result = chem.ideal_gas_law(**parsed)
        return ok(result)
    except chem.ChemistryError as e:
        return err(str(e))
    except (TypeError, ValueError):
        return err("Please provide valid numeric inputs.")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
