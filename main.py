import logging
import requests
import io
import whisper
import time
import numpy as np
import ffmpeg
import telebot
import sys
import os

# Добавляем путь к директории в sys.path
config_path = r'C:\Users\lizat\OneDrive\Documents\CONFIG'
if config_path not in sys.path:
    sys.path.append(config_path)

from config1 import BOT_TOKEN

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


# Функция для скачивания голосового сообщения
def download_audio_file(file_id, bot_token=BOT_TOKEN):
    logging.info("Downloading audio file...")
    start_time = time.time()
    file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(file_url)
    if response.status_code != 200:
        logging.error(f"Failed to get file info: {response.content}")
        return None
    file_path = response.json()['result']['file_path']
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    audio_response = requests.get(download_url)
    if audio_response.status_code != 200:
        logging.error(f"Failed to download file: {audio_response.content}")
        return None
    audio_data = io.BytesIO(audio_response.content)
    end_time = time.time()
    logging.info(f"Audio file downloaded in {end_time - start_time} seconds.")
    return audio_data


# Функция для преобразования аудио в массив NumPy
def audio_to_numpy(audio_data):
    logging.info("Converting audio data to numpy array...")
    start_time = time.time()
    try:
        # Использование ffmpeg для декодирования байтового потока в массив NumPy
        audio_np, _ = (
            ffmpeg
            .input('pipe:0')
            .output('pipe:1', format='wav', acodec='pcm_s16le', ar='16000')
            .run(input=audio_data.read(), capture_stdout=True, capture_stderr=True)
        )

        with open("output.wav", "wb") as f:
            f.write(audio_np)
    except Exception as e:
        logging.error(f"FFmpeg error: {e}")
        return None
    audio_np = np.frombuffer(audio_np, np.int16).astype(np.float32)
    audio_np = audio_np / 32768.0  # Нормализация
    audio_np = audio_np.flatten()
    end_time = time.time()
    logging.info(f"Audio data converted to numpy array in {end_time - start_time} seconds.")
    return audio_np


# Функция для преобразования аудио в текст
def audio_to_text(file_id):
    logging.info("Converting audio to text...")
    start_time = time.time()
    audio_data = download_audio_file(file_id)
    if audio_data is None:
        logging.error("Failed to download audio file.")
        return None
    audio_np = audio_to_numpy(audio_data)
    if audio_np is None:
        logging.error("Failed to convert audio to numpy array.")
        return None
    try:
        result = model.transcribe(audio_np, language='ru')
    except Exception as e:
        logging.error(f"Whisper model error: {e}")
        return None
    end_time = time.time()
    logging.info(f"Audio converted to text in {end_time - start_time} seconds.")
    return result['text']


# Загрузка модели Whisper вне функций для улучшения производительности
model = whisper.load_model('base')  # Или 'base' 'medium' 'large'


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет! Отправьте мне голосовое сообщение, и я преобразую его в текст.')


# Обработчик голосового сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    try:
        start_time = time.time()
        file_id = message.voice.file_id
        text = audio_to_text(file_id)
        if text is None:
            bot.reply_to(message, 'Произошла ошибка при обработке вашего голосового сообщения.')
        else:
            bot.reply_to(message, f'Текст вашего сообщения: {text}')
        end_time = time.time()
        logging.info(f"Voice message processed in {end_time - start_time} seconds.")
    except Exception as e:
        logging.error(f"Error: {e}")
        bot.reply_to(message, 'Произошла ошибка при обработке вашего голосового сообщения.')



# Основная функция для запуска бота
def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()