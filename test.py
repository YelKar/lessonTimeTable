from lesson_timetable import TimeTable

# bot = TeleBot("5246504083:AAHRNwVG1G3epaDPmRqfTLgnf5ycRyTOhD8")

with open("util/json_examples/example.json", encoding="utf-8") as f:
    print(table := TimeTable.de_json(f.read()))
    print(type(table))


from telebot import TeleBot, types


TeleBot.message_handler
