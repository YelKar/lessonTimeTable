import json
from dataclasses import dataclass
from datetime import time, timedelta, timezone, datetime

from typing import Optional, Dict


@dataclass
class TimeTable:
    from .days import Day as __Day
    from .lessons import Lesson as __Lesson
    monday: Optional[__Day] = None
    tuesday: Optional[__Day] = None
    wednesday: Optional[__Day] = None
    thursday: Optional[__Day] = None
    friday: Optional[__Day] = None
    saturday: Optional[__Day] = None
    sunday: Optional[__Day] = None

    timezone: timezone = timezone(timedelta(hours=3))
    __days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    __days_ru = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье"
    ]

    def __post_init__(self):
        for name, day in self.dict.items():
            if not day.name:
                day.name = self.__days_ru[self.__days.index(name)]

    @property
    def dict(self):
        return {k: v for k, v in zip(self.__days, self.__dict__.values()) if v is not None}

    def __iter__(self):
        return iter(self.dict.values())

    def __getitem__(self, item: str | int):
        if isinstance(item, int):
            if item > 6:
                raise IndexError("there are only seven days in a week")
            return self[self.__days[item]]

        days = self.dict
        if item not in days:
            if item in self.__days:
                raise EmptyDayError(item)
            else:
                raise KeyError(item)

        return self.dict[item]

    def get(self, item, default=None) -> __Day:
        try:
            return self[item]
        except (EmptyDayError, KeyError):
            return default

    def now(self, now: datetime | None = None) -> __Lesson | None:
        now = now or datetime.now(self.timezone)
        today = self.today(now)
        if today is None:
            return
        return today.now(now.time())

    def next(self, now: datetime | None = None) -> __Lesson | None:
        now = now or datetime.now(self.timezone)
        today = self.today(now)
        if today is None:
            return
        return today.next(now.time())

    def today(self, now: datetime | None = None) -> __Day:
        now = now or datetime.now(self.timezone)
        return self.get(self.__days[now.weekday()])

    def tomorrow(self, now: datetime | None = None) -> __Day:
        now = now or datetime.now(self.timezone)
        return self.get(self.__days[(now.weekday() + 1) % 7])

    def next_workday(self, now: datetime | None = None) -> __Day:
        now = now or datetime.now(self.timezone)
        for add in range(1, 8):
            day = self.get(self.__days[(now.weekday() + add) % 7])
            if day:
                return day

    @classmethod
    def de_json(cls, json_table: Dict | str):
        if isinstance(json_table, str):
            try:
                json_table = json.loads(json_table)
            except json.JSONDecodeError as e:
                raise DecodeError(e.msg, e.doc, e.pos)

        for name, day in json_table.items():
            for i, lesson in enumerate(day):
                for _ in range(5 - len(lesson)):
                    lesson.append(None)
                lesson[1] = datetime.strptime(lesson[1], "%H:%M").time()
                day[i] = cls.__Lesson(
                    *lesson[:2],
                    lesson[3],
                    lesson[4],
                    lesson[2]
                )
            json_table[name] = cls.__Day(*day)
        return cls(**json_table)

    def to_json(self, indent: str | int | None = None) -> str:
        """return json of timetable
        format:
            {
                "<day>": [  // weekday
                    [
                        "<lesson_name>",
                        "<start_time>",
                        duration,  // int => minutes
                        "<teacher>",
                        classroom  // int
                    ]
                ]
            }
        """
        result: dict[str, list[list[int | str | None]]] = {}
        for name, day in self.dict.items():
            result[name] = [
                [
                    lesson.name,
                    lesson.start.strftime("%H:%M"),
                    lesson.duration.seconds // 60,
                    lesson.teacher,
                    lesson.classroom
                ]
                for lesson in day
            ]
        return json.dumps(result, ensure_ascii=False, indent=indent)


class EmptyDayError(Exception):
    def __init__(self, day):
        self.day = day

    def __str__(self):
        return f"day {self.day} is not specified"


class DecodeError(json.JSONDecodeError):
    pass


if __name__ == '__main__':
    from days import Day
    from lessons import Lesson

    tt = TimeTable(Day(
        Lesson("Икт", time(10, 20)),
        Lesson("Математика", time(11, 25)),
        Lesson("Икт", time(20)),
        Lesson("Икт", time(20, 55)),
        Lesson("Икт", time(8, 25), duration=timedelta(hours=1, minutes=45))
    ))

    tt.wednesday = Day(
        Lesson("Икт", time(10, 20)),
        Lesson("Математика", time(11, 25)),
        Lesson("Икт", time(20)),
        Lesson("Икт", time(20, 55)),
        Lesson("Икт", time(8, 25), duration=timedelta(hours=1, minutes=45))
    )

    for d in tt:
        print(d)

    print(tt["saturday"])
