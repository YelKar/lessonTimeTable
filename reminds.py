import json
import os
from datetime import datetime

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv("util/.env")

from telebot import TeleBot

from util.db import NextLesson, Tables, DB
from util.response import lesson
from util.const import moscow_timezone
from calendar import day_name
from lesson_timetable.table import TimeTable


tables = Tables()

bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")
db = NextLesson()


def send_next(*user_ids):
    if user_ids:
        rows = [
            {
                "id": user_id,
                "timetable": table,
                "last": None
             } for user_id, table in zip(user_ids, tables.get(*user_ids, res_type=list))
        ]
    else:
        rows = db.get()
    next_lesson = None
    for row in rows:
        user_id = row["id"]
        table = row["timetable"]
        last = row["last"]
        if table and (next_lesson := table.next()) and next_lesson.start > table.today().start:
            if next_lesson.to_json(is_short=True) == last:
                continue
            bot.send_message(
                user_id,
                lesson(
                    next_lesson,
                    "</u>{name} с {start} в {classroom} Кабинете<u>\n\n"
                    "Напоминание\nСледующий урок:\n"
                )
            )
            db.set_last(user_id, next_lesson)
        elif last:
            db.set_last(user_id, next_lesson)


def send_today_lessons():
    day_num = datetime.now(moscow_timezone).weekday()
    day = TimeTable.days_en[day_num].lower()
    day_ru = TimeTable.days_ru[day_num].title()
    resp = DB.sql_query(query_name="nextDay", day=day)
    template = (
        "<b><u>{day}</u></b>\n\n"
        "{lessons}"
    )
    for user in resp[0].rows:
        bot.send_message(
            user["id"],
            template.format(
                day=day_ru,
                lessons="\n".join(
                    [
                        f"{i}. {lesson_name}"
                        for i, lesson_name
                        in enumerate(
                            json.loads(user["lessons"]),
                            1
                        )
                    ]
                )
            )
        )


if __name__ == '__main__':
    # resp = DB.sql_query(query_name="nextDay")
    send_today_lessons()
