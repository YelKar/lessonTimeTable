from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sized

from util.db import Tables
from lesson_timetable.table import TimeTable

tables = Tables()


def get_table(user_id: int) -> TimeTable:
    return tables.get(user_id)[0]["table"]


def set_table(user_id: int, table: TimeTable):
    tables.set(user_id, table)


def get_weekdays_kb(_table: TimeTable):
    keyboard = InlineKeyboardMarkup()
    for row in _chunks(list(_table.dict.items()), 2):
        keyboard.add(
            *(
                InlineKeyboardButton(day.name, callback_data=f"{name}_weekday")
                for name, day in row
            )
        )
    return keyboard


def _chunks(_iter: Sized, step: int):
    for i in range(0, len(_iter), step):
        yield _iter[i:i + step]


def kb_for_json_examples():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Скачать", callback_data="download_json_example")
    )
    return keyboard
