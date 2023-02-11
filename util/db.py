import os

import ydb.iam
from ydb.convert import _ResultSet

from lesson_timetable.table import TimeTable


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv("./.env")


config = {
    "database": os.getenv("database"),
    "endpoint": os.getenv("endpoint"),
}

my_id = 1884965431


class DB:
    def __init__(self, driver_config: ydb.DriverConfig | None = None):
        self.driver_config = driver_config or ydb.DriverConfig(
            **config,
            credentials=ydb.iam.ServiceAccountCredentials.from_file(
                os.getenv("SA_KEY_FILE"),
            ),
            root_certificates=ydb.load_ydb_root_certificate()
        )
        self.route = "./util/queries/{name}.yql"

    def query(self, name: str):
        with open(self.route.format(name=name), "r", encoding="utf-8") as file:
            return file.read().strip()


class Tables(DB):
    def set(self, user_id: int, table: str | TimeTable):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            compiled_query = session.prepare(self.query("setTable"))
            session.transaction().execute(
                compiled_query,
                {
                    "$id": user_id,
                    "$json": table.to_json() if isinstance(table, TimeTable) else table
                },
                commit_tx=True
            )

    def get(self, user_id, res_type: type = TimeTable) -> TimeTable | str | None:
        query = "SELECT timetable FROM `tables` WHERE id={id}"
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            resp: list[_ResultSet] = session.transaction().execute(
                query.format(id=user_id),
                commit_tx=True
            )
            rows = resp[0].rows
            if not rows:
                return None
            row = rows[0]
            table = row["timetable"]
        if res_type is TimeTable:
            return TimeTable.de_json(table)
        else:
            return table


class Next(DB):
    def get(self):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            resp: _ResultSet = session.transaction().execute(
                self.query("sendNext"),
                commit_tx=True
            )[0]
        for row in resp.rows:
            yield dict(id=row["id"], timetable=TimeTable.de_json(row["timetable"]))

    def add(self, user_id):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            session.transaction().execute(
                f"REPLACE INTO `send_next` (id) VALUES ({user_id});",
                commit_tx=True
            )

    def remove(self, *user_ids):
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            session.transaction().execute(
                f"DELETE FROM `send_next` WHERE id in {tuple(user_ids)};",
                commit_tx=True
            )


if __name__ == '__main__':
    os.chdir("../")
    send_next = Next()
    # print(*send_next.get(), sep="\n\n\n")
    print(*send_next.get())
