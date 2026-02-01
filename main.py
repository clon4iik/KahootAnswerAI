import time
from google import genai
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import random
import string

client = genai.Client(api_key='AIzaSyCGxWwFCImAXXyJb0vLOpWkQbgc5_AERos')

driver = webdriver.Chrome()
driver.get('https://kahoot.it/')
search_box = driver.find_element(By.NAME,'gameId')
search_box.send_keys('688072')
search_box.submit()

input()

nick = string.ascii_lowercase

for i in nick:
    for nick in range(5):
        print(nick)

search_box = driver.find_element(By.NAME,'nickname')
search_box.send_keys('')
search_box.submit()

input()


title = driver.title
print("Название сайта:", title)

match = re.search(r"(\d+)\s+of\s+(\d+)", title)
if match:
    current = int(match.group(1))
    total = int(match.group(2))
    print("Текущий вопрос:", current)
    print("Всего вопросов:", total)


question_elem = driver.find_element(By.CSS_SELECTOR, '[data-functional-selector="block-title"]')
print(question_elem.text)

answer_elements = driver.find_elements(By.CSS_SELECTOR, '[data-functional-selector^="question-choice-text-"]')
answers = [el.text for el in answer_elements]
print("Варианты ответов:", answers)

prompt = f"""
    Вопрос: {question_elem.text}
    Варианты ответов: {answers}
    Выбери правильный вариант и напиши только ВАРИАНТ ОТВЕТА без пояснений.
"""

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents=prompt,
)

print(response.text)


input()