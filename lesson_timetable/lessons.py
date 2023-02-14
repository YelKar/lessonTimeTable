import json
from datetime import time, timedelta, datetime
from typing import Self


class Lesson:
    def __init__(
            self,
            name: str,
            start: time,
            teacher=None,
            classroom: int | None = None,
            duration: timedelta | int | None = None
    ):
        if isinstance(duration, int):
            self.duration = timedelta(minutes=duration)
        else:
            self.duration = duration or timedelta(minutes=45)
        self.name: str = name
        self.start: time = start
        self.stop: time = (datetime.combine(datetime.now(), self.start) + self.duration).time()
        self.teacher: str = teacher
        self.classroom: int = classroom

    def to_json(self, is_short: bool = False, _type: type = list):
        start = self.start.strftime("%H:%M")
        duration = self.duration.seconds // 60
        if _type is list:
            res = [
                self.name,
                start,
                duration
            ]
            if not is_short:
                res.append(self.teacher)
                res.append(self.classroom)
        elif _type is dict:
            res = {
                "name": self.name,
                "start": start,
                "duration": duration,
            }
            if not is_short:
                res.update({
                    "teacher": self.teacher,
                    "classroom": self.classroom
                })
        else:
            return None
        return json.dumps(res, ensure_ascii=False)

    def __repr__(self):
        return f"<Lesson {self}>"

    def __str__(self):
        return f"{self.name}({self.start} - {self.stop})"

    def __lt__(self, other: Self):
        return self.start < other.start

    def __gt__(self, other: Self):
        return self.start > other.start

    def __getitem__(self, key):
        return eval(f"self.{key}")


if __name__ == '__main__':
    lesson = Lesson("Икт", time(10, 20))
    print(lesson.to_json(is_short=True))
