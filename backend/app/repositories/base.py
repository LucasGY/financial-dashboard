from time import sleep
from typing import Any

from pymysql import MySQLError

from app.core.database import Database
from app.core.errors import DataUnavailableError


class BaseRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        last_error: MySQLError | None = None
        for attempt in range(3):
            try:
                with self._database.connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(query, params)
                        return list(cursor.fetchall())
            except MySQLError as exc:
                last_error = exc
                if attempt < 2:
                    sleep(0.2 * (attempt + 1))
        raise DataUnavailableError() from last_error
