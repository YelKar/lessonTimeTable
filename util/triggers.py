import os


class Triggers:
    remind_lesson: str = os.getenv("remind_lesson_trigger")
    remind_day: str = os.getenv("remind_day_trigger")
