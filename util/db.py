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


class Tables:
    def __init__(self, driver_config: ydb.DriverConfig | None = None):
        self.driver_config = driver_config or ydb.DriverConfig(
            **config,
            credentials=ydb.iam.ServiceAccountCredentials.from_file(
                os.getenv("SA_KEY_FILE"),
            ),
            root_certificates=ydb.load_ydb_root_certificate()
        )

    def set(self, user_id: int, table: str | TimeTable):
        with open("./util/queries/set.yql") as f:
            query = f.read()
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()
            compiled_query = session.prepare(query)
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


if __name__ == '__main__':
    tables = Tables()
    print(tables.get(188496541))
