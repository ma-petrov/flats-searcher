from typing import Optional

from pandas import DataFrame, concat, read_csv


class BaseRepository:
    def insert(self, ids: list[str]):
        """Вставляет новые id квартир, проставляет статус is_sent - False."""

    def update_sent(self, ids: list[str]):
        """Обновляет все отправленные id в статус is_sent == True."""

    def get_not_sent(self) -> list[str | None]:
        """Возвращет все неотправленные id квартир."""


class PandasRepository(BaseRepository):
    def __init__(self, filename: Optional[str] = None):
        self.filename = filename or "repository.csv"

    def insert(self, ids: list[str]):
        if not ids:
            return
        
        data = self._load_data()
        data = concat([
            data,
            DataFrame({"id": ids, "is_sent": [False] * len(ids)})
        ])
        data.drop_duplicates(subset=["id"], inplace=True)
        data.to_csv(self.filename)

    def update_sent(self, ids: list[str]):
        if not ids:
            return

        data = self._load_data()
        data["is_sent"] = data.apply(
            lambda r: r.is_sent or r.id in ids, axis=1
        )
        data.to_csv(self.filename)

    def get_not_sent(self) -> list[str | None]:
        data = self._load_data()
        return list(data[data.is_sent.apply(lambda x: not x)].id)

    def _load_data(self) -> DataFrame:
        try:
            return read_csv(
                self.filename,
                index_col=[0],
                dtype={"id": str, "is_sent": bool}
            )
        except FileNotFoundError:
            return DataFrame(columns=["id", "is_sent"])
