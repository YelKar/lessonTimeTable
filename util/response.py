import json

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv(".env")
from lesson_timetable.days import Day as _Day
from lesson_timetable.lessons import Lesson as _Lesson
from lesson_timetable.table import TimeTable
from util.db import DB


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


def day_list(
        user_id: int,
        day_name: str,
        head: str | None = None
):
    resp = DB.sql_query(query_name="dayList", user_id=user_id, day=day_name)
    lessons = json.loads(resp[0].rows[0]['lessons'])
    day_ru = TimeTable.days_ru[TimeTable.days_en.index(day_name)]
    return (
        (f"<b><u>{head}</u></b>\n" if head else "") +
        f"<b><u>{day_ru}</u></b>\n\n" +
        "\n".join(
            [
                f"{i}. " + lesson_name
                for i, lesson_name
                in enumerate(lessons, 1)
            ]
        )
    )


def lesson(_lesson: _Lesson, head: str | None = None):
    # TODO Не отображать секунды
    # TODO Добавить строковые переменные
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
    from dotenv import load_dotenv
    # load_dotenv(".env")
    DB.route = "." + DB.route
    print(day_list(1884965431, day_name="monday"))
