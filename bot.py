import os
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправьте мне ссылку на видео с YouTube, и я конвертирую его в аудио с качеством 320 kbps."
    )

def download_video(url: str, output_path: str) -> str:
    yt = YouTube(url)
    video_stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
    video_path = video_stream.download(output_path=output_path)
    return video_path

def convert_to_audio(video_path: str, output_path: str) -> str:
    audio_path = os.path.splitext(video_path)[0] + ".mp3"
    with VideoFileClip(video_path) as video:
        video.audio.write_audiofile(audio_path, bitrate="320k")
    return audio_path

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    output_dir = "downloads"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        await update.message.reply_text("Скачиваю видео...")
        video_path = download_video(url, output_dir)

        await update.message.reply_text("Конвертирую видео в аудио...")
        audio_path = convert_to_audio(video_path, output_dir)

        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio=InputFile(audio_file), filename=os.path.basename(audio_path))

        # Удаление временных файлов
        os.remove(video_path)
        os.remove(audio_path)
    except Exception as e:
        error_message = f"Произошла ошибка: {type(e).__name__} - {str(e)}"
        await update.message.reply_text(error_message)
        print(error_message)

def main():
    TOKEN = "7656921140:AAGf32V-nDeBVEvoldDorQWRdTDkK1Z0Zic"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_video))

    application.run_polling()

if __name__ == "__main__":
    main()
