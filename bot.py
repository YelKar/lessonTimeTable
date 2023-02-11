import json
import os
from datetime import datetime

from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InputFile

from util import response
from util.const import START, json_msg, json_for_msg
from util.db import Tables, Next
from util.tools import get_weekdays_kb, kb_for_json_examples, default_table

from lesson_timetable.table import TimeTable, DecodeError


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")


tables = Tables()


@bot.message_handler(commands=["start", "help", "h"])
def start(message: Message):
    table = tables.get(message.from_user.id)
    if table is None:
        table = default_table()
        tables.set(message.from_user.id, table)
    kb = get_weekdays_kb(table)
    bot.send_message(message.chat.id, START, reply_markup=kb)


@bot.message_handler(commands=["now"])
def current_lesson(message: Message):
    table = tables.get(message.from_user.id)
    now = datetime.now(table.timezone)
    today = table.today(now)
    if today is None:
        bot.reply_to(message, "Сегодня нет уроков")
    elif (now_time := now.time()) > today.end:
        bot.reply_to(message, "Уроки закончились")
    elif now_time < today.start:
        bot.reply_to(
            message,
            response.lesson(
                today.next(now_time),
                "Уроки ещё не начались\n"
                "Первый урок:\n"
            )
        )
    elif (curr_lesson := today.now(now.time())) is None:
        bot.reply_to(
            message,
            response.lesson(
                today.next(now_time),
                "Перемена\n"
                "Следующий урок:\n"
            )
        )
    else:
        bot.reply_to(
            message,
            response.lesson(
                curr_lesson,
                "Сейчас идет:\n"
            )
        )


@bot.message_handler(commands=["next"])
def next_lesson(message: Message):
    table = tables.get(message.from_user.id)
    now = datetime.now(table.timezone)
    if not (today := table.today(now)):
        bot.reply_to(message, "Сегодня нет уроков")
    elif next_ := today.next(now := now.time()):
        bot.reply_to(message, response.lesson(next_, "Следующий урок:\n"))
    elif today.now(now):
        bot.reply_to(message, "Идет последний урок")
    else:
        bot.reply_to(message, "Уроки закончились")


@bot.message_handler(commands=["today"])
def lessons_today(message: Message):
    table = tables.get(message.from_user.id)
    now = datetime.now(table.timezone)
    today = table.today(now)
    if today:
        resp = response.day(today, "Сегодня:")
        bot.reply_to(message, resp)
    else:
        bot.reply_to(message, "Сегодня нет уроков")


@bot.message_handler(commands=["tomorrow"])
def lessons_tomorrow(message: Message):
    table = tables.get(message.from_user.id)
    now = datetime.now(table.timezone)
    tmr = table.tomorrow(now)
    if not tmr:
        resp = response.day(table.next_workday(now), "Завтра уроков не будет.\nСледующий рабочий день:")
    else:
        resp = response.day(tmr, "Уроки на завтра:")
    bot.reply_to(message, resp)


@bot.message_handler(commands=["dayend"])
def until_day_end(message: Message):
    table = tables.get(message.from_user.id)
    now = datetime.now(table.timezone)
    today = table.today(now)
    if not today:
        bot.reply_to(message, "Сегодня нет уроков")
    elif not (lessons := today[now.time():]):
        bot.reply_to(message, "На сегодня уроки завершились")
    else:
        bot.reply_to(message, response.day(lessons, f"Сегодня осталось {len(lessons)} уроков:\n"))


@bot.message_handler(commands=["week", "table"])
def week(message: Message):
    table = tables.get(message.from_user.id)
    bot.reply_to(message, response.week(table))


@bot.message_handler(commands=["load_table"])
def load_json(message: Message):
    match message.text.split()[1:]:
        case [mode, "default"]:
            with open("./util/default.json", "r", encoding="utf-8") as def_table:
                match mode:
                    case "get":
                        bot.send_document(message.from_user.id, def_table)
                    case "set":
                        tables.set(message.from_user.id, def_table.read().strip())
        case ["get", "my"]:
            download_my_json(message)
        case _:
            bot.send_message(
                message.chat.id,
                json_msg.format(
                    json=json.dumps(
                        json_for_msg,
                        indent=2,
                        ensure_ascii=False
                    )
                ),
                reply_markup=kb_for_json_examples()
            )


@bot.message_handler(content_types=["document"], func=lambda msg: "/load_table" in msg.caption)
def load_table(message: Message):
    file_id = message.document.file_id
    file_obj = bot.get_file(file_id)
    table_json = bot.download_file(file_obj.file_path).decode()

    try:
        table = TimeTable.de_json(table_json)
    except DecodeError:
        bot.reply_to(message, "Неверный JSON файл")
    else:
        tables.set(message.from_user.id, table)
        bot.reply_to(message, "Расписание установлено")


@bot.callback_query_handler(lambda call: call.data.endswith("weekday"))
def weekday_callback(call: CallbackQuery):
    day = call.data.split("_")[0]
    table = tables.get(call.from_user.id)
    bot.send_message(call.from_user.id, response.day(table[day]))


@bot.callback_query_handler(lambda call: call.data.startswith("download_json"))
def download_json_examples(call: CallbackQuery):
    bot.send_document(call.from_user.id, InputFile("./util/json_examples/example.json"))


@bot.callback_query_handler(lambda call: call.data == "download_my_json")
def download_my_json(call: CallbackQuery | Message):
    table = tables.get(call.from_user.id)
    bot.send_document(call.from_user.id, type(
        "json_file", (),
        {
            "name": "table.json",
            "read": lambda *_: table.to_json(indent=2)
        }
    )())


@bot.message_handler(commands=["send_next"])
def set_send_next(message: Message):
    db = Next()
    db.add(message.chat.id)

    bot.reply_to(message, "Теперь каждый час вам будут приходить напоминания о следующем уроке (Если он будет)")


@bot.message_handler(commands=["not_send_next"])
def unset_send_next(message: Message):
    db = Next()
    db.remove(message.chat.id)

    bot.reply_to(message, "Напоминания отключены")
