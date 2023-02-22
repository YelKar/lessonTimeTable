import os
from typing import overload, Any

import ydb.iam
from ydb.convert import _ResultSet, ResultSets

from lesson_timetable.table import TimeTable


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv("./.env")


config = {
    "database": os.getenv("database"),
    "endpoint": os.getenv("endpoint"),
}


class DB:
    driver_config = ydb.DriverConfig(
        **config,
        credentials=ydb.iam.ServiceAccountCredentials.from_file(
            os.getenv("SA_KEY_FILE"),
        ),
        root_certificates=ydb.load_ydb_root_certificate()
    )
    route = "./util/queries/{name}.yql"

    @classmethod
    @overload
    def sql_query(cls, *, query: str) -> ResultSets: ...

    @classmethod
    @overload
    def sql_query(cls, *, query_name: str) -> ResultSets: ...

    @classmethod
    @overload
    def sql_query(cls, *, query: str, **params: Any) -> ResultSets: ...

    @classmethod
    @overload
    def sql_query(cls, *, query_name: str, **params: Any) -> ResultSets: ...

    @classmethod
    def sql_query(
            cls,
            *,
            query: str | None = None,
            query_name: str | None = None,
            **params
    ):
        if query_name is not None:
            query = cls.get_query(query_name)
        elif query is None:
            raise ValueError("missing query text")
        with ydb.Driver(cls.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            compiled_query = session.prepare(query) if params else query
            return session.transaction().execute(
                compiled_query,
                {
                    "$"+k: v for k, v in params.items()
                },
                commit_tx=True
            )

    def __init__(self, driver_config: ydb.DriverConfig | None = None):
        self.driver_config = driver_config or self.driver_config

    @classmethod
    def get_query(cls, name: str):
        with open(cls.route.format(name=name), "r", encoding="utf-8") as file:
            return file.read().strip()


class Tables(DB):
    def set(self, user_id: int, table: str | TimeTable):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            compiled_query = session.prepare(self.get_query("setTable"))
            session.transaction().execute(
                compiled_query,
                {
                    "$id": user_id,
                    "$json": table.to_json() if isinstance(table, TimeTable) else table
                },
                commit_tx=True
            )

    def get(self, *user_ids, res_type: type = TimeTable) -> TimeTable | str | list | None:
        query = f"SELECT timetable FROM `tables` WHERE id in {tuple(user_ids)}"
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            resp: list[_ResultSet] = session.transaction().execute(
                query,
                commit_tx=True
            )
            rows = resp[0].rows
            if res_type is list:
                if res_type is list:
                    rows = list(map(lambda row_: TimeTable.de_json(row_["timetable"]), rows))
                return rows or []

            if not rows:
                return None
            row = rows[0]
            table = row["timetable"]
        if res_type is TimeTable:
            return TimeTable.de_json(table)
        else:
            return table


class NextLesson(DB):
    path = "reminds/next_lesson"

    def get(self):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            resp: list[_ResultSet] = session.transaction().execute(
                self.get_query("sendNext"),
                commit_tx=True
            )[:2]
        for table, last in zip(resp[0].rows, resp[1].rows):
            yield dict(id=table["id"], timetable=TimeTable.de_json(table["timetable"]), last=last["last"])

    def add(self, user_id):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            session.transaction().execute(
                f"REPLACE INTO `{self.path}` (id) VALUES ({user_id});",
                commit_tx=True
            )

    def remove(self, *user_ids):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            session.transaction().execute(
                f"DELETE FROM `{self.path}` WHERE id in {tuple(user_ids)};",
                commit_tx=True
            )

    def is_set(self, user_id: int) -> bool:
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            resp: _ResultSet = session.transaction().execute(
                f"SELECT id FROM `{self.path}` WHERE id = {user_id};",
                commit_tx=True
            )[0]
            return resp.rows is not None

    def set_last(self, user_id, lesson):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            session.transaction().execute(
                session.prepare(
                    "DECLARE $json AS JSON;\n"
                    "DECLARE $id AS Uint64;\n"
                    f"REPLACE INTO `{self.path}` (id, last) VALUES ($id, $json);"
                ),
                {
                    "$id": user_id,
                    "$json": "null" if lesson is None else lesson.to_json(is_short=True),
                },
                commit_tx=True
            )


if __name__ == '__main__':
    from lesson_timetable.lessons import Lesson
    from datetime import time
    os.chdir("../")
    send_next = NextLesson()
    # print(*send_next.get(), sep="\n\n\n")
    print(send_next.is_set(1884965431))
    send_next.set_last(1884965431, Lesson("qwerty", time(22)))
