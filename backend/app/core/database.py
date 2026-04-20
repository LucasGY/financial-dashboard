from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @contextmanager
    def connection(self) -> Iterator[pymysql.connections.Connection]:
        connection = pymysql.connect(
            host=self._settings.mariadb_host,
            port=self._settings.mariadb_port,
            user=self._settings.mariadb_user,
            password=self._settings.mariadb_password,
            database=self._settings.mariadb_database,
            cursorclass=DictCursor,
            autocommit=True,
        )
        try:
            yield connection
        finally:
            connection.close()
