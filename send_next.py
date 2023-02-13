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
    # TODO создать историю, чтобы один урок не присылался два раза
    if user_ids:
        rows = [
            {
                "id": user_id,
                "timetable": table
             } for user_id, table in zip(user_ids, tables.get(*user_ids, res_type=list))
        ]
    else:
        rows = db.get()
    next_lesson = None
    for row in rows:
        user_id = row["id"]
        table = row["timetable"]
        if table and (next_lesson := table.next()) and next_lesson.start > table.today().start:
            bot.send_message(
                user_id,
                lesson(
                    next_lesson,
                    "</u>{name} с {start} в {classroom} Кабинете<u>\n\n"
                    "Напоминание\nСледующий урок:\n"
                )
            )


if __name__ == '__main__':
    from util.const import my_id
    send_next(my_id)
