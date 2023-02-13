import os

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv("util/.env")

from telebot import TeleBot

from util.db import Next
from util.response import lesson


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")
db = Next()


def send_next(*user_ids):
    # TODO создать историю, чтобы один урок не присылался два раза
    next_lesson = None
    for row in user_ids or db.get():
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
    send_next()
