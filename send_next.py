import os

from util.tools import get_table

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv("util/.env")

from telebot import TeleBot

from util.db import Tables
from util.response import lesson


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")
tables = Tables()


def send_next(user_ids: list[int]):
    for user_id in user_ids:
        table = get_table(user_id)
        if (next_lesson := table.next()).start > table.today().start:
            bot.send_message(user_id, lesson(next_lesson))


if __name__ == '__main__':
    send_next([1884965431])
