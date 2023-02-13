from datetime import time

from lesson_timetable.days import Day as _Day
from lesson_timetable.lessons import Lesson as _Lesson
from lesson_timetable.table import TimeTable


def week(_table: TimeTable, head: str | None = None):
    return (
        (f"<b><u>{head}</u></b>\n" if head else "") +
        f"<code>{'_' * 20}</code>\n\n".join(map(day, _table))
    )


def day(_day: _Day, head: str | None = None):
    lessons = "\n".join(map(lesson, _day))
    return (
        (f"<b><u>{head}</u></b>\n" if head else "") +
        (f"<b><u>{_day.name}:</u></b>\n" if isinstance(_day, _Day) and _day.name else '') +
        f"\n{lessons}"
    )


def lesson(_lesson: _Lesson, head: str | None = None):
    # Не отображать секунды
    # Добавить строковые переменные
    if not _lesson:
        return ""
    res = {
        k: (v if v is not None else "____")
        for k, v in _lesson.__dict__.items()
    }
    return (
        (f"<b><u>{head}</u></b>\n" if head else "") +
        ("<u>{name}</u>\n" if _lesson.name else "Название не указано\n") +
        "{start} - {stop}\n" +
        ("{teacher}\n" if _lesson.teacher else "") +
        ("Кабинет: {classroom}\n" if _lesson.classroom else "")
    ).format(**res)


if __name__ == '__main__':
    from gen_table import table
    print(table.next_workday()[:time(23)])
