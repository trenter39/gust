import asyncio, requests, os, logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from sclib import SoundcloudAPI, Track
from pytube import YouTube
from io import BytesIO 

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

api = SoundcloudAPI()

@dp.message(F.text.contains('youtube.com') | F.text.contains('youtu.be'))
async def downloadMusicYouTube(message: types.Message):
    url = message.text.strip()
    download_message = await message.reply("Downloading from YouTube. Please wait...")
    try:
        yt = YouTube(url)
        title = yt.title
        artist = yt.author
        thumb = yt.thumbnail_url
        stream = yt.streams.get_by_itag('251')
        await bot.edit_message_text(chat_id=download_message.chat.id, message_id=download_message.message_id, text="Fetching track...")
        file_bytes = BytesIO()
        stream.stream_to_buffer(file_bytes)
        file_bytes.seek(0)
        await bot.edit_message_text(chat_id=download_message.chat.id, message_id=download_message.message_id, text="Uploading...")
        response = requests.post(
            f'https://api.telegram.org/bot{TOKEN}/sendAudio',
            files={'audio': (f'{artist} - {title}.mp3', file_bytes, 'audio/mpeg'),
                   'thumb': ('album_artwork.jpg', thumb, 'image/jpeg')},
            data={
                'chat_id': message.chat.id,
                'title': title,
                'performer': artist,
                'caption': f"<a href='{thumb}'>Cover</a>\n{artist} - {title}\n@gustmusicbot",
                'parse_mode': "HTML",
                'reply_to_message_id': message.message_id
            }
        )
        await bot.delete_message(chat_id=download_message.chat.id, message_id=download_message.message_id)
    except Exception as e:
        await message.reply(f"Failed to download track from YouTube or queue is currently full. {e}")

@dp.message(F.text.contains("soundcloud.com"))
async def downloadMusicSoundCloud(message: types.Message):
    url = message.text.strip()
    if url.find("on.soundcloud.com") != -1:
        response = requests.head(url, allow_redirects=True)
        url = response.url
    if "sets" in url.split("?")[0]:
        await message.reply("This bot doesn't work on albums/playlists. Send me a link to a single track")
        return
    download_message = await message.reply("Downloading from SoundCloud. Please wait...")
    try:
        track = api.resolve(url)
        assert type(track) is Track
        if track:
            await bot.edit_message_text(chat_id=download_message.chat.id, message_id=download_message.message_id, text="Fetching track...")
            file_bytes = BytesIO()
            track.write_mp3_to(file_bytes)
            file_bytes.seek(0)
            thumb = track.artwork_url[:-9] + "original.jpg"
            await bot.edit_message_text(chat_id=download_message.chat.id, message_id=download_message.message_id, text="Uploading...")
            response = requests.post(
                f'https://api.telegram.org/bot{TOKEN}/sendAudio',
                files={'audio': (f"{track.artist} - {track.title}.mp3", file_bytes, 'audio/mpeg'),
                       'thumb': ('thumb.jpg', thumb, 'image/jpeg')},
                data={
                    'chat_id': message.chat.id,
                    'title': track.title,
                    'performer': track.artist,
                    'caption' : f"<a href='{thumb}'>Cover</a>\n{track.artist} - {track.title}\n@gustmusicbot",
                    'parse_mode': "HTML",
                    'reply_to_message_id': message.message_id
                }
            )
            await bot.delete_message(chat_id=download_message.chat.id, message_id=download_message.message_id)
    except Exception as e:
        await message.reply(f"Failed to download track from SoundCloud or queue is currently full.")
            

@dp.message(CommandStart())
async def startMessage(message: types.Message):
    await message.answer("""Hi, user! Send me an url from [youtube.com] or [soundcloud.com] and I will respond with attached audio file.
Bot works automaticaly in private messages, but in groups you need to start downloading by sending command /get.
If you don't understand something, see /help""")
    
@dp.message(Command("help"))
async def helpMessage(message: types.Message):
    await message.answer("""Please provide the URL of the song, and the bot will proceed to download it for you.
If an issue arises, please ensure that the URL is correct and the song is accessible before attempting to send the message again.""")

@dp.message(Command("get"))
async def getMessage(message: types.Message):
    await message.answer("Send me url now.", reply_markup=types.ForceReply())

@dp.message(F.text)
async def defaultMessage(message: types.Message):
    await message.reply("There's an unsupported link to download something. If there is some other text, please remove everything else and send message again")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())