"""Tests for DataFrame loading functionality."""

import pytest
from pathlib import Path
import pandas as pd


def test_dataframe_can_load_short_csv() -> None:
    """Test that the short CSV file can be loaded into a DataFrame."""
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "prosthetics_data_short.csv"

    # Verify file exists
    assert data_path.exists(), "prosthetics_data_short.csv should exist"

    # Load the DataFrame
    df = pd.read_csv(data_path)

    # Verify it has data
    assert len(df) > 0, "DataFrame should have rows"

    # Verify expected columns exist
    expected_columns = [
        "patient_id",
        "age",
        "gender",
        "amputation_level",
        "amputation_side",
        "foot_type",
        "knee_type",
        "hip_type",
        "fitting_date",
        "num_visits",
        "outcome_score",
        "satisfaction_rating",
    ]
    for col in expected_columns:
        assert col in df.columns, f"Column {col} should exist in DataFrame"


def test_dataframe_copy_preserves_data() -> None:
    """Test that copying the DataFrame preserves the original data."""
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / "data" / "prosthetics_data_short.csv"

    # Load the original DataFrame
    df_original = pd.read_csv(data_path)

    # Create a copy
    df_copy = df_original.copy()

    # Modify the copy
    if len(df_copy) > 0:
        df_copy.loc[0, "age"] = 999

    # Verify original is unchanged
    assert df_original.loc[0, "age"] != 999, "Original DataFrame should not be modified when copy is changed"
