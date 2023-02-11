import json
from random import choice

from lesson_timetable.table import TimeTable


res = {}

for name in TimeTable._TimeTable__days[:-2]:
    day = []

    for i, t in enumerate(["8:25", "9:25", "10:20", "11:25", "12:20", "13:25", "14:30"], 1):
        day.append(
            [
                "",
                t,
                45,
                None,
                choice(list(range(300, 313)) + list(range(400, 413)))
            ]
        )
    res[name] = day


with open("util/default.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(res, ensure_ascii=False, indent=2))
