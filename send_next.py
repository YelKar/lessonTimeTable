import os

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv("util/.env")

from telebot import TeleBot

from util.db import Next, Tables
from util.response import lesson


tables = Tables()

bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")
db = Next()


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


if __name__ == '__main__':
    from util.const import my_id
    send_next(my_id)
