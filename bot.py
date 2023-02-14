import json
import os
from datetime import datetime

from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InputFile

from util import response
from util.const import START, json_msg, json_for_msg, remind_doc
from util.db import Tables, Next
from util.tools import KeyBoard, default_table

from lesson_timetable.table import TimeTable, DecodeError


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")


tables = Tables()


@bot.message_handler(commands=["start", "help", "h"])
def start(message: Message):
    table = tables.get(message.from_user.id)
    if table is None:
        table = default_table()
        tables.set(message.from_user.id, table)
    kb = KeyBoard.weekdays(table)
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
                reply_markup=KeyBoard.json_examples()
            )


@bot.edited_message_handler(content_types=["document"],
                            func=lambda msg: msg.caption and "/load_table" in msg.caption)
@bot.message_handler(content_types=["document"],
                     func=lambda msg: msg.caption and "/load_table" in msg.caption)
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
    name = "_".join(call.data.split("_")[2:])
    bot.send_document(call.from_user.id, InputFile(f"./util/json_examples/{name}.json"))


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


@bot.message_handler(commands=["remind"])
def remind(message: Message):
    bot.send_message(
        message.chat.id,
        remind_doc,
        reply_markup=KeyBoard.send_next()
    )


@bot.callback_query_handler(lambda call: call.data.endswith("remind"))
def chose_send_next_mode(call: CallbackQuery):
    db = Next()
    chat_id = call.from_user.id
    match call.data.split("_")[0]:
        case "set":
            db.add(chat_id)
            bot.send_message(
                chat_id,
                "Теперь каждый час вам будут приходить напоминания "
                "о следующем уроке (Если он будет)"
            )
        case "unset":
            db.remove(chat_id)
            bot.send_message(chat_id, "Напоминания отключены")
        case "get":
            bot.send_message(
                chat_id,
                ["Напоминания отключены", "Напоминания включены"][db.is_set(chat_id)]
            )
        case "test":
            from send_next import send_next
            send_next(chat_id)
