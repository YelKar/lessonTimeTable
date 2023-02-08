import os
import pickle

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

    def set(self, user_id: int, table: TimeTable | str):
        table_hex = pickle.dumps(table).hex() if isinstance(table, TimeTable) else table
        query = ("UPSERT INTO `tables` (id, timetable) "
                 "VALUES ({id}, \"{table}\");")
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            session.transaction().execute(
                query.format(id=user_id, table=table_hex),
                commit_tx=True
            )

    def get(self, *user_ids):
        if user_ids:
            query = "\n".join(f"SELECT id, timetable FROM `tables` WHERE id={user_id};" for user_id in user_ids)
        else:
            query = "SELECT id, timetable FROM `tables`"
        with ydb.Driver(self.driver_config) as driver:
            driver.wait(fail_fast=True, timeout=5)
            session = driver.table_client.session().create()

            resp: list[_ResultSet] = session.transaction().execute(
                query.format(id=1),
                commit_tx=True
            )
        result = []
        for r, user_id in zip(resp, user_ids):
            for row in r.rows:
                result.append(
                    dict(
                        user_id=row["id"],
                        table=pickle.loads(
                            bytes.fromhex(row["timetable"].decode())
                        )
                    )
                )
            if not r.rows:
                default_table = self.get(my_id)[0]["table"]
                self.set(user_id, default_table)
                result.append(dict(user_id=user_id, table=default_table))
        return result


if __name__ == '__main__':
    tables = Tables()
    print(tables.get(18849654, 1884965431))
