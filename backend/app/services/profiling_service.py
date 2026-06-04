import io
import warnings

import pandas as pd

ID_LIKE_PATTERNS = ("id", "uuid", "guid", "key", "index")
MAX_VALUE_COUNTS_IN_PROFILE = 50
TEXT_LIKE_UNIQUE_RATIO = 0.5


def is_id_like_column(name: str) -> bool:
    lower = name.lower().strip()
    return lower in ID_LIKE_PATTERNS or lower.endswith("_id")


def is_junk_column(name: str, series: pd.Series, n_rows: int) -> bool:
    """CSV index (#, Unnamed: 0), ID-like names, near-unique numeric index columns."""
    stripped = str(name).strip()
    lower = stripped.lower()
    if stripped in ("", "#"):
        return True
    if lower.startswith("unnamed"):
        return True
    if is_id_like_column(name):
        return True
    if n_rows > 0 and pd.api.types.is_numeric_dtype(series):
        if series.nunique(dropna=True) >= max(n_rows * 0.95, max(n_rows - 1, 1)):
            return True
    return False


def _junk_reason(name: str, series: pd.Series, n_rows: int) -> str:
    if str(name).strip() == "#":
        return "CSV row index (#) — not used as a feature"
    if str(name).lower().startswith("unnamed"):
        return "pandas unnamed index column — not used as a feature"
    if is_id_like_column(name):
        return "ID-like column name"
    if n_rows > 0 and pd.api.types.is_numeric_dtype(series):
        if series.nunique(dropna=True) >= n_rows * 0.95:
            return "near-unique numeric column (likely row index)"
    return "excluded from features"


def read_csv_bytes(content: bytes) -> pd.DataFrame:
    """Parse CSV with encoding fallbacks; strip header whitespace; warn on bad lines."""
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            buf = io.BytesIO(content)
            with warnings.catch_warnings(record=True):
                df = pd.read_csv(buf, encoding=encoding, on_bad_lines="warn")
            df.columns = [str(c).strip() for c in df.columns]
            if df.shape[1] == 0:
                raise ValueError("CSV has no columns")
            return df
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except pd.errors.EmptyDataError as exc:
            raise ValueError("CSV file is empty") from exc
    if last_error:
        raise ValueError(f"Could not decode CSV: {last_error}") from last_error
    raise ValueError("Could not parse CSV")


def is_likely_text_column(series: pd.Series, n_rows: int) -> bool:
    if n_rows == 0:
        return False
    if not (series.dtype == "object" or str(series.dtype) == "string"):
        return False
    nunique = series.nunique(dropna=True)
    return nunique / n_rows >= TEXT_LIKE_UNIQUE_RATIO


def sanitize_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    n_rows = len(df)
    dropped: list[dict[str, str]] = []
    keep: list[str] = []
    for col in df.columns:
        if is_junk_column(col, df[col], n_rows):
            dropped.append({"column": str(col), "reason": _junk_reason(col, df[col], n_rows)})
        else:
            keep.append(col)
    if not keep:
        return df, dropped
    return df[keep], dropped


def load_csv_bytes(content: bytes) -> pd.DataFrame:
    """Read CSV and drop junk columns (same rules as profiling)."""
    df, _ = sanitize_dataframe(read_csv_bytes(content))
    return df


def build_profile(df: pd.DataFrame, dropped_columns: list[dict[str, str]] | None = None) -> dict:
    n_rows = len(df)
    column_stats = {}
    for col in df.columns:
        series = df[col]
        nunique = int(series.nunique(dropna=True))
        stat: dict = {
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "nunique": nunique,
            "is_constant": bool(nunique <= 1),
            "is_id_like": is_id_like_column(col),
            "is_likely_text": is_likely_text_column(series, n_rows),
        }
        if 0 < nunique <= MAX_VALUE_COUNTS_IN_PROFILE:
            stat["value_counts"] = {
                str(k): int(v) for k, v in series.value_counts(dropna=True).items()
            }
        column_stats[col] = stat

    readiness_warnings: list[str] = []
    dropped = dropped_columns or []
    for d in dropped:
        readiness_warnings.append(f"Removed column '{d['column']}': {d['reason']}")
    if df.shape[0] < 10:
        readiness_warnings.append("Very few rows; metrics may be unreliable.")
    if df.shape[1] < 2:
        readiness_warnings.append(
            "Need at least two columns after cleaning (features + target)."
        )

    ready_for_ml = bool(df.shape[0] >= 10 and df.shape[1] >= 2)

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {k: str(v) for k, v in df.dtypes.to_dict().items()},
        "missing": {k: int(v) for k, v in df.isnull().sum().to_dict().items()},
        "column_stats": column_stats,
        "sanitization": {
            "dropped_columns": dropped,
            "ready_for_ml": ready_for_ml,
            "warnings": readiness_warnings,
        },
    }