from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from google import genai
from time import sleep

client = genai.Client(api_key='AIzaSyCGxWwFCImAXXyJb0vLOpWkQbgc5_AERos')

driver = webdriver.Chrome()
wait = WebDriverWait(driver, timeout=9999)
driver.get('https://kahoot.it/')


def findgame(idgame):
    search_box = driver.find_element(By.NAME, 'gameId')
    search_box.send_keys(idgame)
    search_box.submit()

def nickname(user):
    search_box = driver.find_element(By.NAME, 'nickname')
    search_box.send_keys(user)
    search_box.submit()

def questions():
    question_elem = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-functional-selector="block-title"]'))
    )
    print("Вопрос", question_elem.text)

    answer_elements = driver.find_elements(By.CSS_SELECTOR, '[data-functional-selector^="question-choice-text-"]')
    answers = [el.text for el in answer_elements]
    print("Варианты ответов:", answers)
    return question_elem, answers


def title():
    match = re.search(r"(\d+)\s+of\s+(\d+)", driver.title)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        print("Текущий вопрос:", current)
        print("Всего вопросов:", total)


def askai(question_elem, answers):
    prompt = f"""
        Вопрос: {question_elem.text}
        Варианты ответов: {answers}
        Выбери правильный вариант и напиши только ВАРИАНТ ОТВЕТА без пояснений.
    """

    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=prompt,
    )
    a = response.text
    return a

print('Work!')

game = input("Input game id: ")
findgame(game)

user = input("Input nickname: ")
nickname(user)



while True:
    question_elem, answers = questions()
    print(askai(question_elem, answers))
    quit = input("Press enter to continue... or q to quit")
    if quit == 'q':
        break
