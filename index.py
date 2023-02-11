def handler(event, context):
    resp = "OK"
    match event:
        case {"messages": [{"details": {"trigger_id": tid}}, *_]}:
            from send_next import send_next
            send_next()
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