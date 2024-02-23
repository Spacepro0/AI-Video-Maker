import sys
import os
from pathlib import Path
sys.path.insert(0, Path(__file__).parent.as_posix())
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.resize import resize
import tts
import random
import string

TEXT_CHAR_LIMIT = 20
TEXT_WORD_LIMIT = 10
TEXT_FONT = "Arial-Black"
TEXT_FONT_SIZE = 70
TEXT_COLOR = "white"
TEXT_STROKE_COLOR = "black"
TEXT_STROKE_WIDTH = 2
TEXT_INTERLINE = 20
VID_WIDTH = 1080
VID_HEIGHT = 1920


def split_words(text):
  words = text.split()
  for i in range(0, len(words), TEXT_WORD_LIMIT):
    yield ' '.join(words[i:i+TEXT_WORD_LIMIT])


def create_main_video(text: str, bg_paths: list[str]) -> str:
  video_duration = 0
  txt_clips = []
  split_text_lines = list(split_words(text))
  for line in split_text_lines:
    if line != '':
      txt_clip = TextClip(line, font='Helvetica-Bold', fontsize=TEXT_FONT_SIZE, color=TEXT_COLOR,
                          stroke_color=TEXT_STROKE_COLOR, stroke_width=TEXT_STROKE_WIDTH, interline=TEXT_INTERLINE, method="caption",
                          size=(VID_WIDTH / 1.5, None))
      txt_duration = tts.get_phrase_time(line)
      txt_clip = txt_clip.set_position('center')
      txt_clip = txt_clip.set_duration(txt_duration)
      txt_clip = txt_clip.set_start(video_duration)
      txt_clip.close()
      txt_clips.append(txt_clip)
      video_duration += txt_duration
  file_output_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
  tts.save_audio_to_file(text, f"./files/tmp/{file_output_name}.wav")
  audio_clip = AudioFileClip(f"./files/tmp/{file_output_name}.wav")
  bg_clips_list = []
  for path in bg_paths:
    bg_clips_list.append(resize(VideoFileClip(f"./files/bg/{path}.mp4").subclip(0, video_duration / len(bg_paths)), width=VID_WIDTH, height=VID_HEIGHT))
  bg_clip = concatenate_videoclips(bg_clips_list, method="compose")
  clip_list = [bg_clip] + txt_clips
  video = resize(CompositeVideoClip(clip_list, use_bgclip=True), width=VID_WIDTH, height=VID_HEIGHT)
  video = video.set_duration(video_duration)
  video = video.set_audio(audio_clip.subclip(0, audio_clip.duration - 0.05))
  video.write_videofile(f"./files/output/{file_output_name}.mp4")
  video.close()
  for folder in ["./files/bg", "./files/tmp"]:
    for filename in os.listdir(folder):
      file_path = os.path.join(folder, filename)
      os.unlink(file_path)
  return file_output_name
