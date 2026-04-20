from typing import Any

from pymysql import MySQLError

from app.core.database import Database
from app.core.errors import DataUnavailableError


class BaseRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        try:
            with self._database.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    return list(cursor.fetchall())
        except MySQLError as exc:
            raise DataUnavailableError() from exc
