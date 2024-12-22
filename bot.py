import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import uuid

bot = telebot.TeleBot("8035020430:AAH5o2TGs9gjjABdIIdiJ1QxW1ayYIo_lNA")
url_store = {}


@bot.message_handler(commands=["start"])
def send_hello(message: Message):
    """прінтить повідомлення при команді /start"""
    bot.reply_to(message, "Hello, this bot is for my GoIteens project.\n")


@bot.message_handler(func=lambda message: "tiktok.com" in message.text or "youtube.com" in message.text) #силки які сприймає бот
def handle_video_request(message: Message):
    """вибір формату завантажування"""
    url = message.text.strip()
    bot.send_message(message.chat.id, "Choose format", reply_markup=create_format_buttons(url))


def create_format_buttons(url):
    """створення кнопок для формата"""
    unique_id = str(uuid.uuid4())
    url_store[unique_id] = url
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Video", callback_data=f"video|{unique_id}"),
        InlineKeyboardButton("Audio", callback_data=f"audio|{unique_id}")
    )
    return markup


@bot.callback_query_handler(func=lambda call: True)
def handle_format_selection(call):
    """початок завантаження відео або аудіо"""
    try:
        action, unique_id = call.data.split("|")
        url = url_store.get(unique_id)
        if not url: #якщо силка не та шо тре
            bot.send_message(call.message.chat.id, "Error: URL not found.")
            return

        bot.answer_callback_query(call.id)

        if action == "video":
            bot.send_message(call.message.chat.id, "Starting to download video...")
            download_and_send_media(call.message.chat.id, url, media_type='video')
        elif action == "audio":
            bot.send_message(call.message.chat.id, "Starting to download audio...")
            download_and_send_media(call.message.chat.id, url, media_type='audio')
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error processing request: {str(e)}")


def download_and_send_media(chat_id, url, media_type='video'):
    """власне саме завантаження і відсилання відео або аудіо"""
    ydl_opts = {
        'format': 'best[ext=mp4]/best[ext=webm]' if media_type == 'video' else 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: #скачування
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_size = os.path.getsize(filename) #ліміт на розмір файлу
        if file_size > 50 * 1024 * 1024:
            bot.send_message(chat_id, "Error: File is too large to be sent via Telegram (limit: 50 MB).")
            os.remove(filename) #видалення файлу після відправки
            return

        with open(filename, 'rb') as file: #надсилання завантаженого відео або аудіо
            if media_type == "video":
                bot.send_video(chat_id, file, caption='This is your video :)')
            else:
                bot.send_audio(chat_id, file, caption='This is your audio :)')

        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")


if __name__ == "__main__":
    if not os.path.exists("downloads"): #тимчасове зберігання файлу (74)
        os.makedirs('downloads')

    print("Bot started")
    bot.infinity_polling()
