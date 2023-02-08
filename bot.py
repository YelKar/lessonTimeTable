import json
import os
from datetime import datetime

from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InputFile

from util import response
from util.const import START, json_msg, json_for_msg
from util.tools import get_weekdays_kb, get_table, set_table, kb_for_json_examples

from lesson_timetable.table import TimeTable


bot = TeleBot(os.getenv("TOKEN"), parse_mode="HTML")


@bot.message_handler(commands=["start", "help", "h"])
def start(message: Message):
    kb = get_weekdays_kb(get_table(message.from_user.id))
    bot.send_message(message.chat.id, START, reply_markup=kb)


@bot.message_handler(commands=["now"])
def current_lesson(message: Message):
    table = get_table(message.from_user.id)
    now = datetime.now(table.timezone)
    today = table.today(now)
    if today and now.time() > today.end:
        bot.reply_to(message, "Уроки закончились")
    elif today is None:
        bot.reply_to(message, "Сегодня нет уроков")
    elif (curr_lesson := today.now(now.time())) is None:
        bot.reply_to(
            message,
            response.lesson(
                today.next(now.time()),
                "Перемена\nСледующий урок:\n"
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
    table = get_table(message.from_user.id)
    now = datetime.now(table.timezone)
    if not (today := table.today(now)):
        bot.reply_to(message, "Сегодня нет уроков")
    elif resp := response.lesson(today.next(now.time()), "Следующий урок:\n"):
        bot.reply_to(message, resp)
    elif today.now(now.time()):
        bot.reply_to(message, "Идет последний урок")
    else:
        bot.reply_to(message, "Уроки закончились")


@bot.message_handler(commands=["today"])
def lessons_today(message: Message):
    table = get_table(message.from_user.id)
    now = datetime.now(table.timezone)
    today = table.today(now)
    if today:
        resp = response.day(today, "Сегодня:")
        bot.reply_to(message, resp)
    else:
        bot.reply_to(message, "Сегодня нет уроков")


@bot.message_handler(commands=["tomorrow"])
def lessons_tomorrow(message: Message):
    table = get_table(message.from_user.id)
    now = datetime.now(table.timezone)
    tmr = table.tomorrow(now)
    if not tmr:
        resp = response.day(table.next_workday(now), "Завтра уроков не будет.\nСледующий рабочий день:")
    else:
        resp = response.day(tmr, "Уроки на завтра:")
    bot.reply_to(message, resp)


@bot.message_handler(commands=["dayend"])
def until_day_end(message: Message):
    table = get_table(message.from_user.id)
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
    table = get_table(message.from_user.id)
    bot.reply_to(message, response.week(table))


@bot.message_handler(commands=["load_table"])
def load_json(message: Message):
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
    table = TimeTable.de_json(bot.download_file(file_obj.file_path).decode())

    set_table(message.from_user.id, table)


@bot.callback_query_handler(lambda call: call.data.endswith("weekday"))
def weekday_callback(call: CallbackQuery):
    day = call.data.split("_")[0]
    table = get_table(call.from_user.id)
    bot.send_message(call.from_user.id, response.day(table[day]))


@bot.callback_query_handler(lambda call: call.data.startswith("download_json"))
def download_json_examples(call: CallbackQuery):
    bot.send_document(call.from_user.id, InputFile("./util/json_examples/example.json"))
