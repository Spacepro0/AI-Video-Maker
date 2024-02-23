import tiktokvoice
from mutagen.mp3 import MP3
import os

VOICE = "en_us_006"


def get_phrase_time(text):
  tiktokvoice.tts(text, VOICE, "./files/tmp/tmp-text.mp3")
  audio = MP3("./files/tmp/tmp-text.mp3")
  os.remove("./files/tmp/tmp-text.mp3")
  return audio.info.length - .1


def save_audio_to_file(text, filepath):
  tiktokvoice.tts(text, VOICE, filepath)
