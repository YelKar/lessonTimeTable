from util.triggers import Triggers


def handler(event, context):
    resp = "OK"
    match event:
        case {"messages": [{"details": {"trigger_id": trigger_id}}, *_]}:
            match trigger_id:
                case Triggers.remind_lesson:
                    from reminds import send_next
                    send_next()
                case Triggers.remind_day:
                    from reminds import send_today_lessons
                    send_today_lessons()
        case "test_remind":
            from reminds import send_next
            from util.const import my_id
            send_next(my_id)
        case {"httpMethod": "POST", "body": str(msg_json)} if "message" in msg_json:
            from telebot.types import Update
            from bot import bot
            msg = Update.de_json(msg_json)
            bot.process_new_updates([msg])
        case None:
            print(resp := "<Empty request>")
    print(event)
    return {
        'statusCode': 200,
        'body': resp,
    }