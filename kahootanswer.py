
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import re
import time
import base64
from dotenv import load_dotenv  # Добавили импорт

load_dotenv()  # Подгружает переменные из файла .env в окружение

# Теперь os.getenv автоматически заберет ключ из .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def ask_choice(question_text, answers, image_data=None):
    system_prompt = (
        "Ты — функция-классификатор ответов.\n"
        "Верни ТОЛЬКО порядковый номер правильного ответа (число от 1 до 4).\n"
        "Никакого текста, знаков препинания или пояснений."
    )
    formatted_answers = "\n".join([f"{i+1}. {ans}" for i, ans in enumerate(answers)])
    user_text = f"Вопрос: {question_text}\n\nВарианты ответов:\n{formatted_answers}"

    content = [{"type": "text", "text": user_text}]
    if image_data:
        content.append({"type": "image_url", "image_url": {"url": image_data}})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.0,
            max_tokens=400,
            timeout=5,
        )
        match = re.findall(r"[1-4]", response.choices[0].message.content)
        return int(match[0]) if match else None
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None


def ask_text(question_text, image_data=None):
    system_prompt = (
        "Ты — автоответчик для текстовых вопросов.\n"
        "Дай краткий ответ (1-3 слова) без вводных фраз, кавычек и точек."
    )
    content = [{"type": "text", "text": f"Вопрос: {question_text}"}]
    if image_data:
        content.append({"type": "image_url", "image_url": {"url": image_data}})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.0,
            max_tokens=20,
            timeout=5,
        )
        return response.choices[0].message.content.strip().strip("\"'")
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None


def get_element_base64(element):
    """Делает скриншот элемента прямо из памяти браузера и переводит в base64."""
    try:
        img_bytes = element.screenshot_as_png
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"
    except Exception as e:
        print(f"Ошибка при снимке изображения: {e}")
        return None


# --- Инициализация браузера ---
driver = webdriver.Chrome()
wait = WebDriverWait(driver, timeout=15)
driver.get("https://kahoot.it/")

# 1. Вход по PIN
game_id = input("Input game PIN: ")
pin_input = wait.until(EC.presence_of_element_located((By.NAME, "gameId")))
pin_input.clear()
pin_input.send_keys(game_id)
pin_input.submit()

# Проверка неверного PIN
while True:
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-invalid="true"]'))
        )
        print("PIN не принят.")
        game_id = input("Input game PIN again: ")
        pin_input = driver.find_element(By.NAME, "gameId")
        pin_input.clear()
        pin_input.send_keys(game_id)
        pin_input.submit()
    except Exception:
        break

# 2. Ввод никнейма
nickname = input("Input nickname: ")
nick_input = wait.until(EC.presence_of_element_located((By.NAME, "nickname")))
nick_input.clear()
nick_input.send_keys(nickname)
nick_input.submit()

# Проверка дублирования ника
while True:
    try:
        WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    '[data-functional-selector="duplicate-name-error-notification"]',
                )
            )
        )
        print("Никнейм занят.")
        nickname = input("Input nickname again: ")
        nick_input = driver.find_element(By.NAME, "nickname")
        nick_input.clear()
        nick_input.send_keys(nickname)
        nick_input.submit()
    except Exception:
        break

print("\n--- Бот работает в режиме подсказчика с поддержкой скриншотов ---")

# 3. Мониторинг вопросов
last_question = ""

try:
    while True:
        try:
            question_elements = driver.find_elements(
                By.CSS_SELECTOR, '[data-functional-selector="block-title"]'
            )

            if question_elements:
                q_text = question_elements[0].text.strip()

                if q_text and q_text != last_question:
                    last_question = q_text

                    # Безопасный захват изображения в формате base64
                    images = driver.find_elements(
                        By.CSS_SELECTOR,
                        '[data-functional-selector="media-container__media-image"]',
                    )
                    q_img_data = get_element_base64(images[0]) if images else None

                    answer_elements = driver.find_elements(
                        By.CSS_SELECTOR,
                        '[data-functional-selector^="question-choice-text-"]',
                    )

                    if answer_elements:
                        answers = [el.text for el in answer_elements]
                        print(f"\nВопрос: {q_text}")
                        print(f"Варианты: {answers}")

                        choice_num = ask_choice(q_text, answers, q_img_data)
                        if choice_num and choice_num <= len(answers):
                            print(
                                f"👉 ПОДСКАЗКА: Вариант {choice_num} — {answers[choice_num - 1]}"
                            )
                    else:
                        input_fields = driver.find_elements(
                            By.CSS_SELECTOR,
                            '[data-functional-selector="question-input"]',
                        )
                        if input_fields:
                            print(f"\nТекстовый вопрос: {q_text}")
                            ans_text = ask_text(q_text, q_img_data)
                            if ans_text:
                                print(f"👉 ПОДСКАЗКА: {ans_text}")
        except Exception:
            pass

        time.sleep(0.8)

except KeyboardInterrupt:
    print("\nЗавершение работы...")
finally:
    driver.quit()