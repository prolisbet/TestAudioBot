import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import io
import whisper
import time
import numpy as np
import ffmpeg
import sys
import os

# Добавляем путь к директории в sys.path
config_path = r'C:\Users\lizat\OneDrive\Documents\CONFIG'
if config_path not in sys.path:
    sys.path.append(config_path)

from config1 import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Функция для скачивания голосового сообщения
def download_audio_file(file_id, bot_token=BOT_TOKEN):
    logging.info("Downloading audio file...")
    start_time = time.time()

    file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(file_url)
    file_path = response.json()['result']['file_path']
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    audio_response = requests.get(download_url)
    audio_data = io.BytesIO(audio_response.content)

    end_time = time.time()
    logging.info(f"Audio file downloaded in {end_time - start_time} seconds.")

    return audio_data


# Функция для преобразования аудио в массив NumPy
def audio_to_numpy(audio_data):
    logging.info("Converting audio data to numpy array...")
    start_time = time.time()

    # Использование ffmpeg для декодирования байтового потока в массив NumPy
    audio_np, _ = (
        ffmpeg
        .input('pipe:0')
        .output('pipe:1', format='wav')
        .run(input=audio_data.read(), capture_stdout=True, capture_stderr=True)
    )

    audio_np = np.frombuffer(audio_np, np.int16).astype(np.float32).flatten()

    end_time = time.time()
    logging.info(f"Audio data converted to numpy array in {end_time - start_time} seconds.")

    return audio_np


# Функция для преобразования аудио в текст
def audio_to_text(data):
    logging.info("Converting audio to text...")
    start_time = time.time()

    file_id = data['voice']['file_id']
    audio_data = download_audio_file(file_id)
    audio_np = audio_to_numpy(audio_data)
    model = whisper.load_model("base")
    result = model.transcribe(audio_np)

    end_time = time.time()
    logging.info(f"Audio converted to text in {end_time - start_time} seconds.")

    return result['text']


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Отправьте мне голосовое сообщение, и я преобразую его в текст.')


# Обработчик голосового сообщения
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_time = time.time()

        text = audio_to_text(update.message)
        await update.message.reply_text(f'Текст вашего сообщения: {text}')

        end_time = time.time()
        logging.info(f"Voice message processed in {end_time - start_time} seconds.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text('Произошла ошибка при обработке вашего голосового сообщения.')


# Основная функция для запуска бота
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
