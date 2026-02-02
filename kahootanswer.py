from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from google import genai
from time import sleep

client = genai.Client(api_key='AIzaSyAyvD4A5pGKbDAGlKQ5LH6zVvBODX9n5-E')

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
    # Ждём появления текста вопроса
    question_elem = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[data-functional-selector="block-title"]')
        )
    )
    print("Вопрос:", question_elem.text)

    # Ждём варианты ответов
    answer_elements = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '[data-functional-selector^="question-choice-text-"]')
        )
    )
    answers = [el.text for el in answer_elements]
    print("Варианты ответов:", answers)

    # --- Поиск картинки вопроса ---
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

    # Возвращаем текст вопроса, варианты и URL картинки (если есть)
    return question_elem, answers, image_url


def title():
    match = re.search(r"(\d+)\s+of\s+(\d+)", driver.title)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        print("Текущий вопрос:", current)
        print("Всего вопросов:", total)


def askai(question_elem, answers, image_url):
    if image_url is None:
        prompt = f"""
            Вопрос: {question_elem.text}
            Варианты ответов: {answers}
            Выбери правильный вариант и напиши только ВАРИАНТ ОТВЕТА без пояснений.
        """
    else:
        prompt = f"""
             Вопрос: {question_elem.text + image_url} 
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
    question_elem, answers, image_url = questions()
    print(askai(question_elem, answers, image_url))
    quit = input("Press enter to continue... or q to quit")
    if quit == 'q':
        break
