from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sized
from lesson_timetable.table import TimeTable


def default_table() -> TimeTable:
    with open("./util/default.json", "r", encoding="utf-8") as table:
        return TimeTable.de_json(table.read())


def _chunks(_iter: Sized, step: int):
    for i in range(0, len(_iter), step):
        yield _iter[i:i + step]


class KeyBoard:
    Inline = InlineKeyboardMarkup
    IButton = InlineKeyboardButton
    
    @classmethod
    def json_examples(cls):
        kb = cls.Inline()
        kb.add(
            cls.IButton(
                "Пример",
                callback_data="download_json_example"
            ),
        )
        kb.add(
            cls.IButton(
                "Мое расписание",
                callback_data="download_my_json"
            )
        )
        kb.add(
            cls.IButton(
                "Пример заполненного расписание",
                callback_data="download_json_full_example"
            )
        )
        return kb

    @classmethod
    def weekdays(cls, _table: TimeTable):
        kb = cls.Inline()
        for row in _chunks(list(_table.dict.items()), 2):
            kb.add(
                *(
                    cls.IButton(day.name, callback_data=f"{name}_weekday")
                    for name, day in row
                )
            )
        return kb

    @classmethod
    def send_next(cls):
        kb = cls.Inline()
        kb.add(
            cls.IButton("Включить", callback_data="set_remind"),
            cls.IButton("Выключить", callback_data="unset_remind"),
        )
        kb.add(
            cls.IButton("Проверить", callback_data="get_remind"),
            cls.IButton("Тест", callback_data="test_remind"),
        )
        return kb
