import os

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv("util/.env")

from telebot import TeleBot

from util.db import Next
from util.response import lesson


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")
db = Next()


def send_next():
    # TODO создать историю, чтобы один урок не присылался два раза
    # TODO вынести название урока в начало сообщения
    # TODO добавить тестовые запросы помимо триггера
    next_lesson = None
    for row in db.get():
        user_id = row["id"]
        table = row["timetable"]
        if table and (next_lesson := table.next()) and next_lesson.start > table.today().start:
            bot.send_message(user_id, lesson(next_lesson, "Напоминание\nСледующий урок:\n"))


if __name__ == '__main__':
    send_next()
