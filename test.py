from selenium import webdriver
from selenium.webdriver.common.by import By
from google import genai

driver = webdriver.Chrome()
driver.get('https://wayground.com/join?gc=193806&source=liveDashboard')


client = genai.Client(api_key='AIzaSyCGxWwFCImAXXyJb0vLOpWkQbgc5_AERos')

input("Нажми Enter, когда вопрос появился...")

def start():
    question = driver.find_element(By.CSS_SELECTOR, ".question-text").text
    answers = driver.find_elements(By.CSS_SELECTOR, "button.option")
    answers = [a.text for a in answers]
    return question, answers


while True:
    cmd = input("Enter — ответить, q — выйти: ")
    if cmd == 'q':
        break

    question, answers = start()

    print("Вопрос:", question)
    print("Варианты:", answers)

    prompt = f"""
    Вопрос: {question}
    Варианты ответов: {answers}
    Выбери правильный вариант и напиши только ВАРИАНТ ОТВЕТА без пояснений.
    """

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    print("Ответ ИИ:", response.text.strip())