from datetime import time, datetime, timedelta
from .lessons import Lesson as _Lesson


class Day(dict):
    def __init__(self, *lessons: _Lesson, name=None):
        super().__init__()
        self.name = name

        for lesson in sorted(lessons, key=lambda x: x.start):
            self.__iadd__(lesson)

    def __iter__(self):
        return iter(sorted(self.values(), key=lambda x: x.start))

    def __getitem__(self, item: time | int | slice):
        match item:
            case time():
                for (start, stop), lesson in self.items():
                    if start <= item <= stop:
                        return lesson

            case int(num):
                lessons = sorted(self.values())
                lessons_count = len(lessons)
                if 0 <= num < lessons_count:
                    return lessons[num]

                raise IndexError(f"in this day only {lessons_count} lessons")

            case slice(start=start, stop=stop):
                if isinstance(start, time):
                    lesson = self.now(start) or self.next(start)
                    if not lesson:
                        start = len(self)
                    else:
                        start = self.lesson_id(lesson.start)

                if isinstance(stop, time):
                    lesson = self.now(stop) or self.next(stop)
                    stop = self.lesson_id(lesson.start) if lesson else None

                return sorted(self.values())[start:stop]

        raise KeyError(item)

    def __iadd__(self, lesson):
        self[lesson.start:lesson.stop] = lesson
        return self

    def __setitem__(self, key, value):
        match key:
            case slice(start=start, stop=stop):
                key = start, stop
        super().__setitem__(key, value)

    def __repr__(self):
        res = [f"({lesson.start} - {lesson.stop}): {repr(lesson)}" for lesson in self.values()]
        return f"<Day {{{', '.join(res)}}}>"

    def lesson_id(self, t: time):
        lesson = self.get(t)
        if lesson is None:
            return
        return sorted(self.values()).index(lesson)

    def now(self, now: time | None = None) -> _Lesson | None:
        now = now or datetime.now().time()
        return self.get(now)

    def next(self, now: time | None = None) -> _Lesson | None:
        now = now or datetime.now().time()
        for lesson in self:
            if lesson.start >= now:
                return lesson

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    @property
    def end(self) -> time:
        last = sorted(self.keys(), key=lambda x: x[1])[-1]
        return last[1]

    @property
    def start(self) -> time:
        first = sorted(self.keys(), key=lambda x: x[0])[0]
        return first[0]


if __name__ == '__main__':
    print(*(day := Day(
        _Lesson("Икт", time(10, 20)),
        _Lesson("Математика", time(11, 25)),
        _Lesson("Икт", time(20)),
        _Lesson("Икт", time(20, 55)),
        _Lesson("Икт", time(8, 25), duration=timedelta(hours=1, minutes=45))
    )).items(), sep="\n", end="\n\n")
    print(day.now())
    print(day.next())
    print(day.end)
