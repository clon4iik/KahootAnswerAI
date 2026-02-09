from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from time import sleep
from google import genai
from google.genai import types
import os
import requests
from dotenv import load_dotenv

load_dotenv()

KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEY").split(",")]
KEY_INDEX = 0
client = genai.Client(api_key=KEYS[KEY_INDEX])


def switch_key():
    global KEY_INDEX, client

    KEY_INDEX += 1
    if KEY_INDEX >= len(KEYS):
        print("All keys dead")
        return False

    client = genai.Client(api_key=KEYS[KEY_INDEX])
    print("Switched key")
    return True


driver = webdriver.Chrome()
wait = WebDriverWait(driver, timeout=9999)
driver.get('https://kahoot.it/')


def findelementbyname(name):
    try:
        search = driver.find_element(By.NAME, f'{name}')
        return search
    except Exception as e:
        print(f"Error: {e}")


def findelementbycss(name):
    try:
        search = driver.find_element(By.CSS_SELECTOR, f'{name}')
        return search
    except Exception as e:
        print(f"Error: {e}")


def findgame(idgame):
    try:
        gamestart = findelementbyname('gameId')
        gamestart.clear()
        gamestart.send_keys(idgame)
        gamestart.submit()
    except Exception as e:
        print(f"Error: {e}")


def nickname(user):
    try:
        nick = findelementbyname('nickname')
        nick.clear()
        nick.send_keys(user)
        nick.submit()
    except Exception as e:
        print(f"Error: {e}")


def questions():
    try:
        question_elem = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-functional-selector="block-title"]')
            )
        )
        question_text = question_elem.text
        print("Вопрос:", question_text)

        answer_elements = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, '[data-functional-selector^="question-choice-text-"]')
            )
        )
        answers = [el.text for el in answer_elements]
        print("Варианты ответов:", answers)

        image_url = None
        images = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-functional-selector="media-container__media-image"]'
        )
        if images:
            image_url = images[0].get_attribute("src")
            print("Картинка вопроса:", image_url)
        else:
            print("Картинки нет")

        return question_text, answers, image_url

    except Exception as e:
        print(f"Error: {e}")
        return None


def title():
    match = re.search(r"(\d+)\s+of\s+(\d+)", driver.title)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        print("Текущий вопрос:", current)
        print("Всего вопросов:", total)


def askai(question_text, answers, image_url):
    try:
        prompt = f"""
        Вопрос: {question_text}
        Варианты ответов: {answers}
        Выбери правильный вариант и напиши только ВАРИАНТ ОТВЕТА.
        """

        content = [prompt]

        if image_url is not None:
            print(image_url)
            image_bytes = requests.get(image_url).content
            image = types.Part.from_bytes(
                data=image_bytes, mime_type="image/jpeg"
            )
            content.append(image)

        response = client.models.generate_content(
            model="gemini-3-flash-preview", contents=content,
        )
        return response.text

    except Exception as e:
        if "429" or "400" in str(e):
            print("Rate limit. Switching key...")
            if switch_key():
                return askai(question_text, answers, image_url)
            else:
                return None
        else:
            print(f"AI Error: {e}")
            return None


print('Work!')

game = input("Input game id: ")
findgame(game)
sleep(1)

while True:
    try:
        err = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-invalid="true"]'))
        )

        print("PIN НЕ принят:")

        game = input("Input game id: ")
        findgame(game)
    except Exception as e:
        print("PIN принят (ошибка не появилась)")
        break

user = input("Input nickname: ")
nickname(user)

while True:
    try:
        sleep(0.5)
        WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '[data-functional-selector="duplicate-name-error-notification"]')
            )
        )
        print("Duplicate name error")
        user = input("Input nickname again: ")
        nickname(user)

    except:
        print("Никакой ошибки дубля не появилось — ник принят")
        break

while True:
    question_elem, answers, image_url = questions()
    print(askai(question_elem, answers, image_url))
    quit = input("Press enter to continue... or q to quit")
    if quit == 'q':
        break
