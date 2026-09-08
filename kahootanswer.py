import os
import re
from time import sleep
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

KEY_FILE = "keys.txt"


def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    env_keys = os.getenv("OPENAI_API_KEYS")
    if env_keys:
        return [k.strip() for k in env_keys.split(",") if k.strip()]
    return []


KEYS = load_keys()


def call_openai_with_key_rotation(system_prompt, user_text, image_url=None):
    if not KEYS:
        print("Ошибка: Список API-ключей пуст (keys.txt).")
        return None

    content = [{"type": "text", "text": user_text}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    for key in KEYS:
        try:
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.0,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ошибка ключа {key[:8]}...: {e}. Переходим к следующему.")
            continue

    print("Все API-ключи недействительны или исчерпали лимит.")
    return None


def ask_choice(question_text, answers, image_url=None):
    system_prompt = (
        "Ты — изолированная функция-классификатор ответов для тестов.\n"
        "Верни ТОЛЬКО порядковый номер правильного ответа (число от 1 до 4).\n"
        "Правила:\n"
        "1. Вывод — СТРОГО одна цифра без текста и знаков препинания.\n"
        "2. Всегда выбирай наиболее вероятную цифру."
    )
    formatted_answers = "\n".join([f"{i + 1}. {ans}" for i, ans in enumerate(answers)])
    user_text = f"Вопрос: {question_text}\n\nВарианты ответов:\n{formatted_answers}"

    reply = call_openai_with_key_rotation(system_prompt, user_text, image_url)
    if reply:
        match = re.search(r'[1-4]', reply)
        if match:
            return int(match.group())
    return None


def ask_text(question_text, image_url=None):
    system_prompt = (
        "Ты — функция-автоответчик для текстовых вопросов.\n"
        "Дай краткий, предельно точный ответ (1-3 слова).\n"
        "Никаких вводных фраз, кавычек или точек на конце."
    )
    user_text = f"Вопрос: {question_text}"

    reply = call_openai_with_key_rotation(system_prompt, user_text, image_url)
    if reply:
        return reply.strip('"\'')
    return None


def process_question(driver, wait):
    try:
        # Получаем текст вопроса
        question_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-functional-selector="block-title"]'))
        )
        q_text = question_elem.text

        # Поиск картинки
        images = driver.find_elements(By.CSS_SELECTOR, '[data-functional-selector="media-container__media-image"]')
        q_img = images[0].get_attribute("src") if images else None

        # Проверяем, есть ли варианты ответов (множественный выбор)
        answer_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-functional-selector^="answer-"]')

        if answer_buttons:
            # Читаем текст вариантов ответов
            answer_elements = driver.find_elements(By.CSS_SELECTOR,
                                                   '[data-functional-selector^="question-choice-text-"]')
            answers = [el.text for el in answer_elements]

            print(f"\n[Выбор] Вопрос: {q_text}")
            print(f"Варианты: {answers}")

            choice_num = ask_choice(q_text, answers, q_img)
            if choice_num and choice_num <= len(answer_buttons):
                print(f"ИИ выбрал вариант {choice_num}: {answers[choice_num - 1]}")
                # Клик по соответствующей кнопке (индексация с 0)
                answer_buttons[choice_num - 1].click()
            else:
                print("Не удалось определить вариант ответа.")

        else:
            # Иначе ищем поле текстового ввода
            input_fields = driver.find_elements(By.CSS_SELECTOR, '[data-functional-selector="question-input"]')
            if input_fields:
                print(f"\n[Текст] Вопрос: {q_text}")
                ans_text = ask_text(q_text, q_img)
                if ans_text:
                    print(f"ИИ сгенерировал ответ: {ans_text}")
                    input_fields[0].send_keys(ans_text)
                    input_fields[0].submit()
                else:
                    print("Не удалось сгенерировать текстовый ответ.")
            else:
                print("Элементы управления ответом не найдены.")

    except Exception as e:
        print(f"Ошибка при обработке вопроса: {e}")


# --- Запуск браузера ---
driver = webdriver.Chrome()
wait = WebDriverWait(driver, timeout=15)
driver.get('https://kahoot.it/')

# Авторизация в сессии
game_id = input("PIN игры: ")
pin_input = wait.until(EC.presence_of_element_located((By.NAME, "gameId")))
pin_input.send_keys(game_id)
pin_input.submit()

nickname = input("Никнейм: ")
nick_input = wait.until(EC.presence_of_element_located((By.NAME, "nickname")))
nick_input.send_keys(nickname)
nick_input.submit()

print("\nУспешный вход. Нажимайте Enter для обработки каждого нового вопроса.")

while True:
    cmd = input("\nEnter = ответить | q = выход: ").strip().lower()
    if cmd == "q":
        break
    process_question(driver, wait)

driver.quit()