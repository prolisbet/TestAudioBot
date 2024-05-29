import io
import requests
import telebot
import whisper
import sys
import os

# Добавляем путь к директории в sys.path
config_path = r'C:\Users\lizat\OneDrive\Documents\CONFIG'
if config_path not in sys.path:
    sys.path.append(config_path)

from config1 import BOT_TOKEN

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


# Загрузка голосового сообщения в оперативную память
def download_audio_file(file_id, bot_token=BOT_TOKEN):
    file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(file_url)
    file_path = response.json()['result']['file_path']
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    audio_response = requests.get(download_url)
    audio_data = io.BytesIO(audio_response.content)
    return audio_data


# Трансформация в текст
def audio_to_text(data):
    file_id = data['voice']['file_id']
    audio_data = download_audio_file(file_id)
    model = whisper.load_model("base")
    result = model.transcribe(audio_data)
    print(result['text'])
    return result['text']


# Обработчик голосовых сообщений
@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    try:
        text = audio_to_text(message.json)
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при обработке вашего голосового сообщения.")


# Запуск бота
bot.polling()
