from contextlib import suppress
import os
import pytest
from pandas import DataFrame, read_csv

from repository import PandasRepository


REPOSITORY_FILE = "repository.csv"


def dataframes_are_equal(a: DataFrame, b: DataFrame):
    assert list(a.columns) == list(b.columns), (
        "Columns are different "
        f"columns left: {list(a.columns)} "
        f"columns right: {list(b.columns)} "
    )

    for c in a.columns:
        assert list(a[c]) == list(b[c]), (
            f"Column {c} is not equal "
            f"columns left: {a[c]} "
            f"columns right: {b[c]} "
        )


def get_actual() -> DataFrame:
    return read_csv(
        "repository.csv",
        index_col=[0],
        dtype={"id": str, "is_sent": bool}
    )


@pytest.fixture
def clear_context():
    with suppress(FileNotFoundError):
        os.remove(REPOSITORY_FILE)
    yield
    with suppress(FileNotFoundError):
        os.remove(REPOSITORY_FILE)


@pytest.fixture
def repository() -> PandasRepository:
    return PandasRepository()


@pytest.fixture
def initial_dataframe() -> DataFrame:
    return DataFrame({
        "id": ["0", "1"],
        "is_sent": [False, False]
    })


@pytest.fixture
def updated_dataframe() -> DataFrame:
    return DataFrame({
        "id": ["0", "1", "2"],
        "is_sent": [False, False, False],
    })


@pytest.fixture
def partialy_sent_dataframe() -> DataFrame:
    return DataFrame({
        "id": ["0", "1", "2"],
        "is_sent": [True, True, False],
    })


@pytest.fixture
def sent_dataframe() -> DataFrame:
    return DataFrame({
        "id": ["0", "1", "2"],
        "is_sent": [True, True, True],
    })


def test_insert__no_file(
    clear_context,
    repository: PandasRepository,
    initial_dataframe: DataFrame,
):
    repository.insert(["0", "1"])
    dataframes_are_equal(get_actual(), initial_dataframe)


def test_insert__unique_ids(
    clear_context,
    repository: PandasRepository,
    updated_dataframe: DataFrame,
):
    repository.insert(["0", "1"])
    repository.insert(["1", "1", "1", "1", "1", "2"])
    dataframes_are_equal(get_actual(), updated_dataframe)


def test_get_not_sent(
    clear_context,
    repository: PandasRepository,
    updated_dataframe: DataFrame,
):
    repository.insert(["0", "1", "2"])
    assert repository.get_not_sent() == ["0", "1", "2"]


def test_update_not_sent__partialy(
    clear_context,
    repository: PandasRepository,
    partialy_sent_dataframe: DataFrame,
):
    repository.insert(["0", "1", "2"])
    repository.update_sent(["0", "1"])
    dataframes_are_equal(get_actual(), partialy_sent_dataframe)


def test_update_not_sent__all(
    clear_context,
    repository: PandasRepository,
    sent_dataframe: DataFrame,
):
    repository.insert(["0", "1", "2"])
    repository.update_sent(["0", "1", "2"])
    dataframes_are_equal(get_actual(), sent_dataframe)


def test_update_not_sent__do_not_change_already_sent_status(
    clear_context,
    repository: PandasRepository,
):
    repository.insert(["0", "1", "2"])

    repository.update_sent(["0", "1"])
    dataframes_are_equal(
        get_actual(),
        DataFrame({
            "id": ["0", "1", "2"],
            "is_sent": [True, True, False],
        }),
    )

    repository.update_sent(["2"])
    dataframes_are_equal(
        get_actual(),
        DataFrame({
            "id": ["0", "1", "2"],
            "is_sent": [True, True, True],
        }),
    )
