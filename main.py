import asyncio
import shelve

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import handler

from config import USER, BOT_TOKEN
from parser import Parser

from datetime import datetime, date, time

DB = shelve.open("database", writeback=True)

if DB.get("clients") is None:
    DB["clients"] = set()


async def report_loop(bot: Bot) -> None:
    """Запускается каждые 10 минут и проверяет корректна(более 5т.р.) ли сумма денежных средств на счету chesnok"""
    while True:
        for login, password in USER.items():
            datetime_now = datetime.now()
            time_now = datetime_now.time()
            message = True
            try:
                parser = Parser(user=login, password=password)
                await parser.login()
                value = await parser.get_balance()
                today_sms = await parser.checkSms()
                if time_now > datetime.strptime("17:00:00", "%H:%M:%S").time():
                    check_date_func = await parser.check_date()
                    message = check_date_func()
                if time_now > datetime.strptime("17:00:00", "%H:%M:%S").time() and not today_sms and not message:
                    for client in DB["clients"]:
                        await bot.send_message(client, f"За сегодняшний день сообщений не было")
                    message = True
                if isinstance(value, str):
                    for client in DB["clients"]:
                        await bot.send_message(client, value, parse_mode=types.ParseMode.MARKDOWN)
                else:
                    if value < 5000:
                        for client in DB["clients"]:
                            await bot.send_message(client, f"Необходимо пополнить счёт ChesnokBet RUB.\nСумма денежных средств на счету ChesnokBet RUB: {value}.\nНеобходимо внести от {5000-value}Р")
            except Exception as e:
                print(e)

        await asyncio.sleep(60*60)

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