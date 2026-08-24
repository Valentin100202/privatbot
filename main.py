import os
import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

BOT_TOKEN = "8586749392:AAEzj9IxSA8ZAjG2ymcaJLJOeDds_L5lt_8"
ADMIN_ID = 6490466863
CHANNEL_ID = -1004373427185

WEBHOOK_HOST = "https://твое-приложение.koyeb.app"
WEBHOOK_PATH = f"/bot/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

PORT = int(os.environ.get("PORT", 8000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📅 Месяц — 150 ⭐", callback_data="buy_month")],
            [types.InlineKeyboardButton(text="♾ Навсегда — 300 ⭐", callback_data="buy_forever")]
        ]
    )
    await message.answer(
        "👋 Привет! Выбери вариант доступа в наш приватный канал:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "buy_month")
async def process_buy_month(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="Доступ на месяц", amount=150)]
    await callback.message.answer_invoice(
        title="Доступ в приватный канал (1 месяц)",
        description="Подписка на закрытый канал на 30 дней.",
        payload="month_subscription",
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_forever")
async def process_buy_forever(callback: types.CallbackQuery):
    prices = [LabeledPrice(label="Доступ навсегда", amount=300)]
    await callback.message.answer_invoice(
        title="Доступ в приватный канал (Навсегда)",
        description="Пожизненный доступ в закрытый канал.",
        payload="forever_subscription",
        currency="XTR",
        prices=prices
    )
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment_info = message.successful_payment
    total_amount = payment_info.total_amount
    payload = message.successful_payment.invoice_payload
    
    tariff_name = "Месяц" if payload == "month_subscription" else "Навсегда"
    
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )
        
        await message.answer(
            f"✅ Оплата прошла успешно! Списано звезд: {total_amount} ⭐.\n\n"
            f"Вот твоя персональная ссылка для входа в канал:\n{invite_link.invite_link}\n\n"
            f"⚠️ *Ссылка действует только для 1 человека.*"
        )
    except Exception as e:
        await message.answer(
            f"✅ Оплата прошла успешно! Но произошла ошибка при авто-создании ссылки. Администратор уже оповещен."
        )
        print(f"Ошибка создания ссылки: {e}")
    
    user_identifier = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    await bot.send_message(
        ADMIN_ID,
        f"💰 Новая покупка!\n"
        f"👤 Пользователь: {user_identifier}\n"
        f"📦 Тариф: {tariff_name}\n"
        f"⭐ Сумма: {total_amount} звезд"
    )

async def on_startup(bot: Bot):
webhook_url = f"https://{os.getenv('WEBHOOK_HOST')}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)

def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    app = web.Application()
    
    dp.startup.register(on_startup)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
