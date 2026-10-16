"""Dataset inspection and statistical calculations for the MDM project."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


ALPHA = 0.05
MINIMUM_PAIRED_OBSERVATIONS = 3
MAX_VISUALIZATION_POINTS = 500

CONNECTIVITY_KEYWORDS = ("internet", "connectivity", "network")
LEARNING_KEYWORDS = (
    "interaction",
    "performance",
    "satisfaction",
    "clearing doubts",
    "participation",
    "learning",
)

# Only documented ordered response sets are encoded. Unordered categories are
# rejected rather than assigned arbitrary numeric codes.
ORDERED_SCALES: tuple[tuple[str, dict[str, float]], ...] = (
    (
        "three-level bad to good satisfaction rating",
        {"bad": 1.0, "average": 2.0, "good": 3.0},
    ),
    (
        "five-level very bad to very good rating",
        {"very bad": 1.0, "bad": 2.0, "average": 3.0, "good": 4.0, "very good": 5.0},
    ),
)


class AnalysisValidationError(ValueError):
    """An expected validation failure suitable for an API response."""


def _finite_number(value: Any) -> float | None:
    """Return a JSON-safe float, replacing NaN and infinity with None."""
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _json_value(value: Any) -> Any:
    """Convert Pandas/NumPy scalar values into strict JSON-compatible values."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return _finite_number(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _dtype_name(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string"


def suggest_analysis_columns(columns: list[str]) -> dict[str, list[str]]:
    """Suggest columns using names actually present in the supplied dataset."""
    connectivity = [
        column
        for column in columns
        if any(keyword in column.casefold() for keyword in CONNECTIVITY_KEYWORDS)
    ]
    learning = [
        column
        for column in columns
        if any(keyword in column.casefold() for keyword in LEARNING_KEYWORDS)
    ]
    return {"connectivity": connectivity, "learning_outcomes": learning}


def preview_dataframe(df: pd.DataFrame, preview_rows: int = 5) -> dict[str, Any]:
    """Return structural dataset information without altering the data."""
    if df.empty or len(df.columns) == 0:
        raise AnalysisValidationError("The CSV contains no data rows or columns.")

    records = [
        {str(key): _json_value(value) for key, value in record.items()}
        for record in df.head(preview_rows).to_dict(orient="records")
    ]
    columns = [str(column) for column in df.columns]
    return {
        "row_count": int(len(df)),
        "column_count": int(len(columns)),
        "columns": columns,
        "data_types": {str(column): _dtype_name(df[column]) for column in df.columns},
        "missing_values": {
            str(column): int(count) for column, count in df.isna().sum().items()
        },
        "duplicate_row_count": int(df.duplicated().sum()),
        "preview": records,
        "suggested_columns": suggest_analysis_columns(columns),
    }


def prepare_numeric_series(series: pd.Series, column_name: str) -> tuple[pd.Series, dict[str, Any]]:
    """Validate a numeric/ordered series and return a non-destructive encoding."""
    non_missing = series.dropna()
    if non_missing.empty:
        raise AnalysisValidationError(f"Column '{column_name}' has no usable values.")

    numeric = pd.to_numeric(series, errors="coerce")
    non_numeric_count = int((series.notna() & numeric.isna()).sum())
    if non_numeric_count == 0:
        non_finite = numeric.notna() & ~np.isfinite(numeric.astype(float))
        invalid_numeric = int(non_finite.sum())
        numeric = numeric.mask(non_finite)
        return numeric.astype(float), {
            "kind": "numeric",
            "transformation": None,
            "invalid_value_count": invalid_numeric,
        }

    normalized = series.astype("string").str.strip().str.casefold()
    observed = set(normalized.dropna().unique().tolist())
    three_scale_name, three_level = ORDERED_SCALES[0]
    five_scale_name, five_level = ORDERED_SCALES[1]

    selected_scale: tuple[str, dict[str, float]] | None = None
    if observed == set(three_level):
        selected_scale = (three_scale_name, three_level)
    elif (
        observed
        and len(observed) >= 2
        and observed.issubset(five_level)
        and observed.intersection({"very bad", "very good"})
    ):
        selected_scale = (five_scale_name, five_level)
    elif observed and observed.issubset({"bad", "average", "good"}):
        raise AnalysisValidationError(
            f"Column '{column_name}' contains an ambiguous partial ordered scale. "
            "Provide all three levels (Bad, Average, Good) or include a distinguishing "
            "five-level response such as Very Bad or Very Good."
        )

    if selected_scale is not None:
        scale_name, mapping = selected_scale
        encoded = normalized.map(mapping).astype(float)
        return encoded, {
            "kind": "ordered_rating",
            "transformation": {
                "description": scale_name,
                "mapping": {label: int(value) for label, value in mapping.items()},
            },
            "invalid_value_count": 0,
        }

    raise AnalysisValidationError(
        f"Column '{column_name}' is not numeric and does not match a documented ordered rating scale."
    )


def calculate_descriptive_statistics(series: pd.Series) -> dict[str, Any]:
    """Calculate mean, median, and sample standard deviation."""
    values = (
        pd.to_numeric(series, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
        .astype(float)
    )
    count = int(len(values))
    if count == 0:
        raise AnalysisValidationError("Descriptive statistics require at least one valid value.")

    return {
        "valid_observations": count,
        "mean": _finite_number(values.mean()),
        "median": _finite_number(values.median()),
        "sample_standard_deviation": (
            _finite_number(values.std(ddof=1)) if count >= 2 else None
        ),
        "standard_deviation_convention": "sample standard deviation (ddof=1)",
        "minimum": _finite_number(values.min()),
        "maximum": _finite_number(values.max()),
    }


def _paired_values(x: pd.Series, y: pd.Series) -> pd.DataFrame:
    paired = pd.DataFrame({"x": x, "y": y}).replace([np.inf, -np.inf], np.nan).dropna()
    return paired.astype(float)


def _association_label(coefficient: float) -> str:
    magnitude = abs(coefficient)
    if magnitude < 0.10:
        strength = "negligible"
    elif magnitude < 0.30:
        strength = "weak"
    elif magnitude < 0.50:
        strength = "moderate"
    else:
        strength = "strong"

    if coefficient > 0:
        return f"{strength} positive"
    if coefficient < 0:
        return f"{strength} negative"
    return "no monotonic"


def _continued_beta_fraction(a: float, b: float, x: float) -> float:
    """Evaluate the continued fraction used by the regularized beta function."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1e-300 if abs(d) < 1e-300 else d
    d = 1.0 / d
    result = d
    for iteration in range(1, 201):
        even = 2 * iteration
        term = iteration * (b - iteration) * x / ((qam + even) * (a + even))
        d = 1.0 + term * d
        d = 1e-300 if abs(d) < 1e-300 else d
        c = 1.0 + term / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        result *= d * c

        term = -(a + iteration) * (qab + iteration) * x / ((a + even) * (qap + even))
        d = 1.0 + term * d
        d = 1e-300 if abs(d) < 1e-300 else d
        c = 1.0 + term / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < 3e-14:
            break
    return result


def _regularized_beta(x: float, a: float, b: float) -> float:
    """Return the regularized incomplete beta function without SciPy."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    factor = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _continued_beta_fraction(a, b, x) / a
    return 1.0 - factor * _continued_beta_fraction(b, a, 1.0 - x) / b


def _correlation_p_value(coefficient: float, count: int) -> float:
    """Two-sided correlation p-value using Student's t distribution."""
    if abs(coefficient) >= 1.0:
        return 0.0
    degrees_freedom = count - 2
    t_squared = coefficient * coefficient * degrees_freedom / (1.0 - coefficient * coefficient)
    return _regularized_beta(degrees_freedom / (degrees_freedom + t_squared), degrees_freedom / 2.0, 0.5)


def calculate_spearman(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    """Calculate a two-sided Spearman rank correlation."""
    paired = _paired_values(x, y)
    count = int(len(paired))
    if count < MINIMUM_PAIRED_OBSERVATIONS:
        raise AnalysisValidationError(
            f"Spearman correlation requires at least {MINIMUM_PAIRED_OBSERVATIONS} valid pairs."
        )
    if paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        raise AnalysisValidationError("Correlation cannot be calculated for a constant variable.")

    ranked_x = paired["x"].rank(method="average").to_numpy(dtype=float)
    ranked_y = paired["y"].rank(method="average").to_numpy(dtype=float)
    coefficient = _finite_number(np.corrcoef(ranked_x, ranked_y)[0, 1])
    p_value = _finite_number(_correlation_p_value(float(coefficient), count)) if coefficient is not None else None
    if coefficient is None or p_value is None:
        raise AnalysisValidationError("Spearman correlation produced an invalid numerical result.")

    direction = _association_label(coefficient)
    return {
        "status": "available",
        "method": "Spearman rank correlation (two-sided)",
        "coefficient": coefficient,
        "p_value": p_value,
        "valid_pairs": count,
        "direction": direction,
        "interpretation": (
            f"The sample shows a {direction} monotonic association. "
            "This association does not establish causation."
        ),
    }


def calculate_regression(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    """Calculate exploratory ordinary least-squares linear regression."""
    paired = _paired_values(x, y)
    count = int(len(paired))
    if count < MINIMUM_PAIRED_OBSERVATIONS:
        raise AnalysisValidationError(
            f"Linear regression requires at least {MINIMUM_PAIRED_OBSERVATIONS} valid pairs."
        )
    if paired["x"].nunique() < 2:
        raise AnalysisValidationError("Regression cannot be calculated with a constant predictor.")

    x_values = paired["x"].to_numpy(dtype=float)
    y_values = paired["y"].to_numpy(dtype=float)
    x_centered = x_values - x_values.mean()
    y_centered = y_values - y_values.mean()
    slope = _finite_number(np.dot(x_centered, y_centered) / np.dot(x_centered, x_centered))
    intercept = _finite_number(y_values.mean() - float(slope) * x_values.mean()) if slope is not None else None
    denominator = math.sqrt(float(np.dot(x_centered, x_centered) * np.dot(y_centered, y_centered)))
    pearson_r = float(np.dot(x_centered, y_centered) / denominator) if denominator else 0.0
    r_squared = _finite_number(pearson_r * pearson_r)
    if slope is None or intercept is None or r_squared is None:
        raise AnalysisValidationError("Linear regression produced an invalid numerical result.")

    x_min = float(paired["x"].min())
    x_max = float(paired["x"].max())
    line = [
        {"x": x_min, "y": float(intercept + slope * x_min)},
        {"x": x_max, "y": float(intercept + slope * x_max)},
    ]
    return {
        "status": "available",
        "method": "Ordinary least-squares simple linear regression",
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "valid_pairs": count,
        "equation": f"y = {slope:.6g}x + {intercept:.6g}",
        "line_coordinates": line,
        "interpretation": (
            f"A one-unit increase in the predictor corresponds to an estimated "
            f"{slope:.4g}-unit change in the outcome. This exploratory model does not establish causation."
        ),
    }


def unavailable_regression(reason: str) -> dict[str, Any]:
    """Return the stable regression contract when regression is not defensible."""
    return {
        "status": "unavailable",
        "reason": reason,
        "method": "Ordinary least-squares simple linear regression",
        "slope": None,
        "intercept": None,
        "r_squared": None,
        "valid_pairs": None,
        "equation": None,
        "line_coordinates": [],
        "interpretation": "Regression was not calculated because the selected data do not support it.",
    }


def perform_hypothesis_test(correlation: dict[str, Any], alpha: float = ALPHA) -> dict[str, Any]:
    """Apply the specified two-sided Spearman significance decision rule."""
    p_value = correlation.get("p_value")
    coefficient = correlation.get("coefficient")
    if p_value is None or coefficient is None:
        raise AnalysisValidationError("Hypothesis testing requires a valid correlation result.")

    reject = float(p_value) < alpha
    decision = "Reject H0" if reject else "Fail to reject H0"
    interpretation = (
        "The sample provides evidence of a nonzero monotonic association at alpha = 0.05."
        if reject
        else "The sample does not provide sufficient evidence of a nonzero monotonic association at alpha = 0.05."
    )
    return {
        "status": "available",
        "null_hypothesis": (
            "There is no monotonic association between the selected connectivity measure "
            "and online learning outcome in the underlying population."
        ),
        "alternative_hypothesis": (
            "There is a nonzero monotonic association between the selected variables."
        ),
        "method": "Two-sided Spearman correlation significance test",
        "test_statistic": float(coefficient),
        "p_value": float(p_value),
        "alpha": float(alpha),
        "decision": decision,
        "interpretation": interpretation,
    }


def _frequency_data(series: pd.Series) -> list[dict[str, Any]]:
    counts = series.value_counts(dropna=False, sort=False)
    items = [
        {"value": _json_value(value), "count": int(count)}
        for value, count in counts.items()
    ]
    return sorted(items, key=lambda item: (item["value"] is None, str(item["value"])))


def _visualization_points(paired: pd.DataFrame) -> tuple[list[dict[str, float]], bool]:
    sampled = len(paired) > MAX_VISUALIZATION_POINTS
    if sampled:
        indices = np.linspace(0, len(paired) - 1, MAX_VISUALIZATION_POINTS, dtype=int)
        chart_pairs = paired.iloc[indices]
    else:
        chart_pairs = paired
    points = [
        {"x": float(row.x), "y": float(row.y)}
        for row in chart_pairs.itertuples(index=False)
    ]
    return points, sampled


def analyze_dataframe(
    df: pd.DataFrame,
    connectivity_column: str,
    learning_column: str,
    *,
    source_name: str,
) -> dict[str, Any]:
    """Validate selected variables and assemble a stable analysis response."""
    if df.empty or len(df.columns) == 0:
        raise AnalysisValidationError("The CSV contains no data rows or columns.")
    if not connectivity_column or not learning_column:
        raise AnalysisValidationError(
            "Both connectivity_column and learning_column are required."
        )
    if connectivity_column == learning_column:
        raise AnalysisValidationError("Select two different analysis columns.")

    missing_columns = [
        column
        for column in (connectivity_column, learning_column)
        if column not in df.columns
    ]
    if missing_columns:
        raise AnalysisValidationError(
            "Selected column(s) not found: " + ", ".join(missing_columns)
        )

    x, x_metadata = prepare_numeric_series(df[connectivity_column], connectivity_column)
    y, y_metadata = prepare_numeric_series(df[learning_column], learning_column)
    paired = _paired_values(x, y)
    valid_pairs = int(len(paired))
    if valid_pairs < MINIMUM_PAIRED_OBSERVATIONS:
        raise AnalysisValidationError(
            f"Analysis requires at least {MINIMUM_PAIRED_OBSERVATIONS} valid paired observations; "
            f"{valid_pairs} remain after missing/invalid values are removed."
        )
    if paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        raise AnalysisValidationError("Analysis requires two non-constant selected variables.")

    correlation = calculate_spearman(x, y)
    try:
        regression = calculate_regression(x, y)
    except AnalysisValidationError as error:
        regression = unavailable_regression(str(error))
    hypothesis_test = perform_hypothesis_test(correlation)
    points, sampled = _visualization_points(paired)

    duplicate_count = int(df.duplicated().sum())
    dropped_pairs = int(len(df) - valid_pairs)
    warnings: list[str] = [
        "Associations and regression estimates do not establish causation.",
        "Results describe the supplied sample and must not be generalized to every Indian student.",
        "Exploratory linear regression treats the selected numerical levels as equally spaced; this assumption requires care for ordinal ratings.",
    ]
    if duplicate_count:
        warnings.append(
            f"The dataset contains {duplicate_count} exact duplicate row(s); they were reported but retained."
        )
    if dropped_pairs:
        warnings.append(
            f"{dropped_pairs} row(s) were excluded from paired analysis because at least one selected value was missing or invalid."
        )
    tie_ratio = min(paired["x"].nunique(), paired["y"].nunique()) / valid_pairs
    if valid_pairs < 30 or tie_ratio <= 0.20:
        warnings.append(
            "The asymptotic Spearman p-value may be less reliable for small samples or extensively tied ranks."
        )
    if sampled:
        warnings.append(
            f"Visualization points were deterministically limited to {MAX_VISUALIZATION_POINTS}; all {valid_pairs} pairs were used for statistics."
        )
    if regression["status"] == "unavailable":
        warnings.append(f"Regression unavailable: {regression['reason']}")

    return {
        "dataset": {
            "source": source_name,
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
            "duplicate_row_count": duplicate_count,
        },
        "selected_variables": {
            "connectivity": {
                "column": connectivity_column,
                "processing": x_metadata,
            },
            "learning_outcome": {
                "column": learning_column,
                "processing": y_metadata,
            },
        },
        "sample_size": valid_pairs,
        "missing_data": {
            "total_rows": int(len(df)),
            "connectivity_missing_or_invalid": int(x.isna().sum()),
            "learning_missing_or_invalid": int(y.isna().sum()),
            "valid_pairs": valid_pairs,
            "excluded_from_paired_analysis": dropped_pairs,
        },
        "descriptive_statistics": {
            "connectivity": calculate_descriptive_statistics(x),
            "learning_outcome": calculate_descriptive_statistics(y),
        },
        "correlation": correlation,
        "regression": regression,
        "hypothesis_test": hypothesis_test,
        "visualization_data": {
            "scatter_points": points,
            "scatter_points_sampled": sampled,
            "scatter_point_limit": MAX_VISUALIZATION_POINTS,
            "regression_line": regression["line_coordinates"],
            "distributions": {
                "connectivity": _frequency_data(x),
                "learning_outcome": _frequency_data(y),
            },
        },
        "warnings": warnings,
    }
