"""
ChemLab Analytics - Laboratory Data Analyzer & Visualization Engine
Reads CSV data with Pandas, computes descriptive statistics with NumPy,
and renders charts with Matplotlib/Seaborn, returned as base64 PNGs so the
frontend can display them without writing files the browser must fetch.
"""

import base64
import io

import matplotlib
matplotlib.use("Agg")  # headless rendering, no display server needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="darkgrid")

# Palette tuned to match the app's lab-notebook visual identity
PALETTE = ["#3fb8af", "#e8a13b", "#8c6fd6", "#e0574e"]


class DataAnalysisError(ValueError):
    pass


def load_csv(filepath_or_buffer) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath_or_buffer)
    except Exception as e:
        raise DataAnalysisError(f"Could not read CSV: {e}")
    if df.empty:
        raise DataAnalysisError("CSV file is empty.")
    return df


def numeric_columns(df: pd.DataFrame):
    return df.select_dtypes(include=[np.number]).columns.tolist()


def describe_dataframe(df: pd.DataFrame) -> dict:
    """Produce average/max/min/std/correlation summary for all numeric columns."""
    num_cols = numeric_columns(df)
    if not num_cols:
        raise DataAnalysisError("No numeric columns found in the uploaded CSV.")

    stats = {}
    for col in num_cols:
        series = df[col].dropna()
        stats[col] = {
            "average": round(float(series.mean()), 6),
            "max": round(float(series.max()), 6),
            "min": round(float(series.min()), 6),
            "std_dev": round(float(series.std()), 6) if len(series) > 1 else None,
            "count": int(series.count()),
        }

    correlation_matrix = None
    if len(num_cols) >= 2:
        corr = df[num_cols].corr(numeric_only=True).round(4)
        correlation_matrix = {
            "columns": num_cols,
            "matrix": corr.values.tolist(),
        }

    return {
        "columns": df.columns.tolist(),
        "numeric_columns": num_cols,
        "row_count": int(len(df)),
        "stats": stats,
        "correlation": correlation_matrix,
        "preview": df.head(10).to_dict(orient="records"),
    }


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _style_axes(ax, fig):
    fig.patch.set_facecolor("#12181d")
    ax.set_facecolor("#161f26")
    ax.tick_params(colors="#c9d6dd")
    ax.xaxis.label.set_color("#e7ecef")
    ax.yaxis.label.set_color("#e7ecef")
    ax.title.set_color("#e7ecef")
    for spine in ax.spines.values():
        spine.set_color("#2a3640")


def make_line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = None) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _style_axes(ax, fig)
    ax.plot(df[x_col], df[y_col], marker="o", color=PALETTE[0], linewidth=2.2, markersize=6)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title or f"{y_col} vs {x_col}")
    ax.grid(True, alpha=0.25)
    return _fig_to_base64(fig)


def make_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = None) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _style_axes(ax, fig)
    ax.scatter(df[x_col], df[y_col], color=PALETTE[1], s=60, edgecolor="#12181d", linewidth=0.5)
    if len(df) >= 2:
        m, b = np.polyfit(df[x_col], df[y_col], 1)
        xs = np.linspace(df[x_col].min(), df[x_col].max(), 50)
        ax.plot(xs, m * xs + b, color=PALETTE[3], linestyle="--", linewidth=1.6, label="trend")
        ax.legend(facecolor="#161f26", labelcolor="#e7ecef", edgecolor="#2a3640")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title or f"{y_col} vs {x_col} (scatter)")
    return _fig_to_base64(fig)


def make_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = None) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _style_axes(ax, fig)
    ax.bar(df[x_col].astype(str), df[y_col], color=PALETTE[2])
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title or f"{y_col} by {x_col}")
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
    return _fig_to_base64(fig)


def make_distribution_chart(df: pd.DataFrame, col: str, title: str = None) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _style_axes(ax, fig)
    sns.histplot(df[col].dropna(), kde=True, ax=ax, color=PALETTE[0], edgecolor="#12181d")
    ax.set_xlabel(col)
    ax.set_ylabel("Frequency")
    ax.set_title(title or f"Distribution of {col}")
    return _fig_to_base64(fig)


def make_correlation_heatmap(df: pd.DataFrame) -> str:
    num_cols = numeric_columns(df)
    if len(num_cols) < 2:
        raise DataAnalysisError("Need at least 2 numeric columns for a correlation heatmap.")
    fig, ax = plt.subplots(figsize=(6, 5))
    _style_axes(ax, fig)
    corr = df[num_cols].corr(numeric_only=True)
    sns.heatmap(corr, annot=True, cmap="mako", ax=ax, cbar=True,
                linewidths=0.5, linecolor="#12181d", fmt=".2f")
    ax.set_title("Correlation Heatmap")
    return _fig_to_base64(fig)
