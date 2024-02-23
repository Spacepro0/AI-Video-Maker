from flask import Flask, render_template, request, url_for, flash, redirect, send_file
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.support.wait import WebDriverWait
import json
import requests
from creator.video_creator import create_main_video
import time
from dotenv import load_dotenv
import os

load_dotenv()

FLASK_SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
GPT_EMAIL_LOGIN = os.environ["GPT_EMAIL_LOGIN"]
GPT_PASSWORD_LOGIN = os.environ["GPT_PASSWORD_LOGIN"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
DEBUG = (os.environ.get("DEBUG", "False").lower() in ["true", "1"])
STOCK_VIDEOS_AMOUNT = 4
WEB_DRIVER_TIMEOUT_TIME = 10
GPT_RESPONSE_DELAY = 7.5
MAX_RETRIES = 2

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY


@app.route("/", methods=('GET', 'POST'))
def index():
  if request.method == 'POST':
    prompt = request.form.get("prompt")
    print(request.form)
    print(prompt)
    for i in range(MAX_RETRIES):
      try:
        filename = create_video(prompt)
        flash("Sucessfully created video. Please download the file!", category="info")
        return redirect(url_for('index', filename=filename))
      except:
        if i == MAX_RETRIES:
          flash("Internal error. Please try again or refresh the page!", category="error")
          return redirect(url_for('index'))
        pass
  filename = request.args.get("filename")
  return render_template("index.html", filename=filename)


@app.route("/download/<filename>")
def download(filename):
  return send_file(f"files/output/{filename}.mp4", as_attachment=True)


def create_video(prompt: str) -> str:
  print("Generating script and video query terms with Chat GPT...")
  options = uc.ChromeOptions()
  driver = uc.Chrome(options=options, version_main=120, browser_executable_path="/usr/bin/chromium-browser")
  try:
    driver.minimize_window()
  except:
    pass
  driver.get('https://chat.openai.com/c/339d71e1-1d52-4ce5-81fa-a9d6f0ec87cf')
  driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[1]/div/div/button[1]').click()
  WebDriverWait(driver, WEB_DRIVER_TIMEOUT_TIME).until(lambda driver: driver.find_element(By.XPATH, '//*[@id="username"]')).send_keys(f"{GPT_EMAIL_LOGIN}\n")
  WebDriverWait(driver, WEB_DRIVER_TIMEOUT_TIME).until(lambda driver: driver.find_element(By.XPATH, '//*[@id="password"]')).send_keys(f"{GPT_PASSWORD_LOGIN}")
  driver.find_element(By.XPATH, "/html/body/div[1]/main/section/div/div/div/form/div[2]/button").click()
  script_prompt = f"""You are a presenter for a short YouTube video. You will write a script for one of your videos on a specific topic. Only include the monologue on the topic and nothing else. Your prompt is {prompt}. Include interesting and attention-drawing facts about your prompt. End the script with a question that loops back to the beginning and the beginning should answer the question. The monologue should take no longer to read than 30 seconds with a fast-paced voice."""
  prompt_input = WebDriverWait(driver, WEB_DRIVER_TIMEOUT_TIME*100).until(lambda driver: driver.find_element(By.XPATH, '//*[@id="prompt-textarea"]'))
  prompt_input.send_keys(script_prompt)
  driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[2]/main/div[2]/div[2]/form/div/div/div/button').click()
  time.sleep(GPT_RESPONSE_DELAY)
  script = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/main/div[2]/div[1]/div/div/div").find_elements(By.CLASS_NAME, 'w-full')[-1].find_element(By.TAG_NAME, 'p').text
  stock_videos_prompt = f"""Generate {STOCK_VIDEOS_AMOUNT} search terms for stock videos, depending on the subject of a video. Subject: {prompt} The search terms are to be returned as a JSON-Array of strings. Each serach term should consist of 1-3 words, always add the main subject of the video. Here is an example of a JSON-Array of strings: ["search term 1", "search term 2", "search term 3"] Obviously, the search terms should be rekated to the subject of the video. Only return the JSON-Array of strings. Do not return anything else! For context, here is the full text: {script}"""
  prompt_input.send_keys(stock_videos_prompt)
  driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div[2]/main/div[2]/div[2]/form/div/div/div/button').click()
  time.sleep(GPT_RESPONSE_DELAY)
  stock_footage_query_terms = json.loads(driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/main/div[2]/div[1]/div/div/div").find_elements(By.CLASS_NAME, 'w-full')[-1].find_element(By.TAG_NAME, 'p').text)
  driver.quit()
  download_stock_footage_videos(stock_footage_query_terms)
  return create_main_video(script, stock_footage_query_terms)


def download_stock_footage_videos(query_terms: list[str]):
  print("Downloading stock footage...")
  for query in query_terms:
    pexels_response: dict = requests.get("https://api.pexels.com/videos/search", {"query": query, "orientation": "portrait", "per_page": "1"}, headers={'Authorization': PEXELS_API_KEY}).json()
    vid_bytes = requests.get(pexels_response["videos"][0]["video_files"][0]["link"]).content
    with open(f"files/bg/{query}.mp4", "wb") as file:
      print(f"Downloading video - {query}")
      file.write(vid_bytes)
      file.close()


if __name__ == "__main__":
  app.run(debug=DEBUG)