import asyncio
import shelve
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import filters
from config import USER, BOT_TOKEN
from parser import Parser
from datetime import datetime, time

DB = shelve.open("database", writeback=True)

if DB.get("clients") is None:
    DB["clients"] = set()

message = datetime.today().date()

async def report_loop(bot: Bot) -> None:

    """Запускается каждые 10 минут и проверяет, корректна ли сумма денежных средств
     на счету chesnok (более 5 тыс.руб.),
     наличие СМС-оповещений за сегодняшний день"""
    while True:
        for login, password in USER.items():
            datetime_now = datetime.now()
            time_now = datetime_now.time()
            try:
                parser = Parser(user=login, password=password)
                await parser.login()
                value = await parser.get_balance()
                if time_now < time(hour=17, minute=0, second=0):
                    today_sms = await parser.check_sms()
                    message = parser.is_message(datetime_now.date())
                    if not today_sms and not message:
                        for client in DB["clients"]:
                            await bot.send_message(client, "За сегодняшний день сообщений не было")
                if isinstance(value, str):
                    for client in DB["clients"]:
                        await bot.send_message(client, value, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    if value < 5000:
                        for client in DB["clients"]:
                            await bot.send_message(client, f"Необходимо пополнить счёт ChesnokBet RUB."
                                                           f"Сумма денежных средств на счету ChesnokBet RUB: {value}."
                                                           f"Необходимо внести {5000-value}Р")
            except Exception as e:
                print(e)
        await asyncio.sleep(60 * 60)


async def start_handler(message: types.Message) -> None:
    """Приветствие нового пользователя и добавление его в базу."""
    DB["clients"].add(message.chat.id)
    await message.answer(
        f"Привет, {message.from_user.get_mention(as_html=True)} 👋!\nЕсли баланс ChesnokBet опустится ниже 5000Р - я пришлю уведомление!",
        parse_mode=types.ParseMode.HTML,
    )


async def exit_handler(message: types.Message) -> None:
    """Удаление пользователя из базы."""
    if message.chat.id in DB["clients"]:
        DB["clients"].remove(message.chat.id)
        await message.answer(
            f"Пользователь, {message.from_user.get_mention(as_html=True)} успешно отписался.",
            parse_mode=types.ParseMode.HTML,
        )
    else:
        await message.answer(
            f"Пользователь, {message.from_user.get_mention(as_html=True)} не был найден.",
            parse_mode=types.ParseMode.HTML,
        )


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    try:
        dispatcher = Dispatcher(bot=bot)
        dispatcher.register_message_handler(start_handler, commands={"start", "restart"})
        dispatcher.register_message_handler(exit_handler, commands={"exit"})
        asyncio.create_task(report_loop(bot))
        await dispatcher.start_polling()
    finally:
        DB.close()
        await bot.close()


if __name__ == '__main__':
    asyncio.run(main())