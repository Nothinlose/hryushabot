import os
import asyncio
import re
import random
from dotenv import load_dotenv
from datetime import datetime
from telethon import TelegramClient, events
load_dotenv()

# настройки
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = 'hryakobot'
GAME_BOT_ID = 7553874114
COMMAND_TEXT = "хрю"
DEFAULT_COOLDOWN = 4 * 3600 

# стата
stats = {"khryas": 0, "cards": 0}
is_waiting = False

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def log(message, type="INFO"):
    prefix = {
        "INFO": "🔹",
        "SUCCESS": "✅",
        "WAIT": "⏳",
        "ERROR": "❌",
        "PIG": "🐷"
    }
    print(f"[{get_time()}] {prefix.get(type, '•')} {message}")

def parse_time_from_text(text):
    hours = 0
    minutes = 0
    seconds = 0
    h_match = re.search(r'(\d+)\s*ч\.', text)
    m_match = re.search(r'(\d+)\s*мин\.', text)
    s_match = re.search(r'(\d+)\s*сек\.', text)
    if h_match: hours = int(h_match.group(1))
    if m_match: minutes = int(m_match.group(1))
    if s_match: seconds = int(s_match.group(1))
    return (hours * 3600) + (minutes * 60) + seconds

async def wait_and_send(delay, chat_id, client):
    global is_waiting
    if is_waiting:
        return
    is_waiting = True

    jitter = random.randint(15, 60)
    total_wait = delay + jitter // 3600
    
    hours = total_wait // 3600
    minutes = (total_wait % 3600) // 60
    
    log(f"Засыпаю на {hours}ч. {minutes}мин. (рандомизация {jitter}с.)", "WAIT")
    funny_phrases = [
        "Пойду прилягу в лужу...",
        "Хрюша спит, и я посплю.",
        "Коплю силы для следующего хрюка.",
        "Ушел чистить копытца.",
    ]
    log(random.choice(funny_phrases), "PIG")
    
    await asyncio.sleep(total_wait)
    
    log(f"Я тут как тут! Отправляю '{COMMAND_TEXT}'", "PIG")
    await client.send_message(chat_id, COMMAND_TEXT)
    stats["khryas"] += 1
    is_waiting = False

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        # чек на то что пишет бот
        if GAME_BOT_ID and event.sender_id != GAME_BOT_ID:
            return

        text = event.raw_text
        chat_id = event.chat_id

        # лог
        log(f"Получено сообщение от игрового бота:", "INFO")

        if any(x in text for x in ["Подождите", "Хрюшу", "рядом", "Попробуйте", "Возвращайтесь"]):
            seconds = parse_time_from_text(text)
            log("Бот сказал: рано! Считаю сколько можно поотдыхать...", "INFO")
            if seconds > 0:
                asyncio.create_task(wait_and_send(seconds, chat_id, client))
            else:
                log("Не удалось понять время, попробую через стандартные 4 часа", "ERROR")
                asyncio.create_task(wait_and_send(DEFAULT_COOLDOWN, chat_id, client))

        elif "карточка" in text and "Новая" in text:
            # поиск карточки для лога
            card_name = "Неизвестная хрюша"
            match = re.search(r'«(.*?)»', text)
            if match:
                card_name = match.group(1)

            stats["cards"] += 1
            log(f"[ХРЯК НАЙДЕН!!] Получена карточка: {card_name} 🎉", "SUCCESS")
            log(f"Всего поймано хрюш за сессию: {stats['cards']}", "INFO")

            # 4 часа таймер после найденного хряка
            asyncio.create_task(wait_and_send(DEFAULT_COOLDOWN, chat_id, client))

    # статус
    @client.on(events.NewMessage(outgoing=True, pattern=r'\.статус'))
    async def status(event):
        status_msg = (
            f"🐷 **Хрякобот Статус**\n"
            f"--- --- ---\n"
            f"✅ Поймано карточек: {stats['cards']}\n"
            f"📤 Хрюкнул уже {stats['khryas']} раз\n"
            f"⏳ Жду новых свинок: {'Да' if is_waiting else 'Нет'}\n"
            f"made by nothinlose ❤️"
        )
        await event.edit(status_msg)

    @client.on(events.NewMessage(outgoing=True, pattern=r'\.хряк'))
    async def manual_start(event):
        await event.edit("Хрюша запусилась, хрю-хрю!")
        log("Ручной запуск цикла!", "PIG")
        await client.send_message(event.chat_id, COMMAND_TEXT)
        stats["khryas"] += 1

    log("Запуск клиента Telethon...", "INFO")
    await client.start()
    
    # привет
    print("-" * 65)
    log("Хрякобот Запустился", "SUCCESS")
    log("Команды: .хряк (запуск), .статус (проверка)         Made by nothinlose❤️", "INFO",)
    print("-" * 65)
    
    await client.run_until_disconnected()
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Бот выключен пользователем. Пока, фермер!", "INFO")
