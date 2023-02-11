from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sized
from lesson_timetable.table import TimeTable


def default_table() -> TimeTable:
    with open("./util/default.json", "r", encoding="utf-8") as table:
        return TimeTable.de_json(table.read())


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
        InlineKeyboardButton("Пример", callback_data="download_json_example"),
    )
    keyboard.add(
        InlineKeyboardButton(
            "Скачать мое расписание",
            callback_data="download_my_json"
        )
    )
    return keyboard
