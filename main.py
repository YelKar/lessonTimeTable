def start():
    import dotenv
    dotenv.load_dotenv("util/.env")
    from bot import bot
    bot.infinity_polling()


start()
