"""
ChemLab Analytics - Mathematics & Statistics Engine
Descriptive statistics, correlation, percentage, and simple equation /
function-graph helpers.
"""

import math
import statistics as st

import numpy as np


class MathError(ValueError):
    pass


def _clean_numbers(values):
    if not values:
        raise MathError("Provide at least one numeric value.")
    try:
        nums = [float(v) for v in values]
    except (TypeError, ValueError):
        raise MathError("All values must be numeric.")
    return nums


def mean(values):
    nums = _clean_numbers(values)
    return round(st.mean(nums), 6)


def median(values):
    nums = _clean_numbers(values)
    return round(st.median(nums), 6)


def mode(values):
    nums = _clean_numbers(values)
    try:
        return round(st.mode(nums), 6)
    except st.StatisticsError:
        # multimodal - return all modes
        counts = {}
        for n in nums:
            counts[n] = counts.get(n, 0) + 1
        top = max(counts.values())
        return sorted([k for k, v in counts.items() if v == top])


def variance(values, sample=True):
    nums = _clean_numbers(values)
    if len(nums) < 2 and sample:
        raise MathError("Sample variance requires at least 2 values.")
    return round(st.variance(nums) if sample else st.pvariance(nums), 6)


def std_dev(values, sample=True):
    nums = _clean_numbers(values)
    if len(nums) < 2 and sample:
        raise MathError("Sample standard deviation requires at least 2 values.")
    return round(st.stdev(nums) if sample else st.pstdev(nums), 6)


def percentage(part, whole):
    if whole == 0:
        raise MathError("Whole value cannot be zero.")
    return round((part / whole) * 100, 6)


def correlation(x_values, y_values):
    x = _clean_numbers(x_values)
    y = _clean_numbers(y_values)
    if len(x) != len(y):
        raise MathError("x and y must have the same number of values.")
    if len(x) < 2:
        raise MathError("Correlation requires at least 2 paired values.")
    r = float(np.corrcoef(x, y)[0, 1])
    if math.isnan(r):
        raise MathError("Correlation undefined (zero variance in one series).")
    return round(r, 6)


def summary_stats(values):
    nums = _clean_numbers(values)
    result = {
        "n": len(nums),
        "mean": mean(nums),
        "median": median(nums),
        "min": round(min(nums), 6),
        "max": round(max(nums), 6),
        "range": round(max(nums) - min(nums), 6),
    }
    try:
        result["mode"] = mode(nums)
    except MathError:
        result["mode"] = None
    if len(nums) >= 2:
        result["variance"] = variance(nums)
        result["std_dev"] = std_dev(nums)
    else:
        result["variance"] = None
        result["std_dev"] = None
    return result


# ---------------------------------------------------------------------------
# Basic equations
# ---------------------------------------------------------------------------
def solve_linear(a, b):
    """Solve ax + b = 0"""
    if a == 0:
        if b == 0:
            return {"type": "linear", "solutions": "infinite", "message": "All real numbers satisfy this equation."}
        return {"type": "linear", "solutions": [], "message": "No solution."}
    return {"type": "linear", "solutions": [round(-b / a, 6)]}


def solve_quadratic(a, b, c):
    """Solve ax^2 + bx + c = 0"""
    if a == 0:
        return solve_linear(b, c)
    disc = b ** 2 - 4 * a * c
    if disc > 0:
        sq = math.sqrt(disc)
        x1 = (-b + sq) / (2 * a)
        x2 = (-b - sq) / (2 * a)
        return {"type": "quadratic", "discriminant": round(disc, 6), "solutions": sorted([round(x1, 6), round(x2, 6)])}
    elif disc == 0:
        x = -b / (2 * a)
        return {"type": "quadratic", "discriminant": 0, "solutions": [round(x, 6)]}
    else:
        real = round(-b / (2 * a), 6)
        imag = round(math.sqrt(-disc) / (2 * a), 6)
        return {
            "type": "quadratic",
            "discriminant": round(disc, 6),
            "solutions": [f"{real} + {imag}i", f"{real} - {imag}i"],
        }


# ---------------------------------------------------------------------------
# Function graphing: evaluate expressions safely over a range
# ---------------------------------------------------------------------------
SAFE_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "sqrt": math.sqrt, "log": math.log10, "ln": math.log,
    "exp": math.exp, "abs": abs, "pi": math.pi, "e": math.e,
}


def evaluate_function(expr: str, x_min: float, x_max: float, points: int = 200):
    """Evaluate a user-supplied expression in terms of x over [x_min, x_max]."""
    if x_max <= x_min:
        raise MathError("x_max must be greater than x_min.")
    if points < 2 or points > 2000:
        raise MathError("points must be between 2 and 2000.")

    xs = np.linspace(x_min, x_max, points)
    ys = []
    for xv in xs:
        local_env = dict(SAFE_FUNCS)
        local_env["x"] = xv
        try:
            y = eval(expr, {"__builtins__": {}}, local_env)
        except Exception as e:
            raise MathError(f"Could not evaluate expression at x={xv}: {e}")
        ys.append(float(y))
    return {"x": xs.tolist(), "y": ys}
