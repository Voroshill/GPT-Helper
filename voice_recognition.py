import queue
import speech_recognition as sr
import keyboard
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# Определение горячих клавиш
START_RECORDING_KEY = 'R'
STOP_RECORDING_KEY = 'Tab'

# Глобальные переменные
driver = None
website_url = "https://felo.ai/ru/search"
INPUT_FIELD_SELECTOR = 'textarea'
recording = False
driver_lock = threading.Lock()
exit_flag = False

def start_recording():
    global recording
    recording = True
    print(f"Запись начата. Нажмите '{STOP_RECORDING_KEY}' для остановки.")
    threading.Thread(target=listen).start()

def stop_recording():
    global recording
    recording = False
    print("Запись остановлена. Завершение записи через 1 секунду...")
    time.sleep(1)  # Задержка на 1 секунду для завершения записи

def listen():
    global exit_flag
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Скажите что-нибудь...")

        while recording and not exit_flag:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio, language='ru-RU')
                print(f"Вы сказали: {text}")
                insert_text_into_field(text)

            except sr.UnknownValueError:
                print("Не удалось распознать звук. Пожалуйста, попробуйте снова.")
            except sr.RequestError as e:
                print(f"Ошибка сервиса распознавания: {e}")
            except sr.WaitTimeoutError:
                # Игнорируем таймаут, если ничего не было сказано
                pass

def insert_text_into_field(text):
    global driver

    with driver_lock:
        if driver is None:
            start_driver()

        try:
            input_field = WebDriverWait(driver, 5).until(  # Уменьшено время ожидания
                EC.visibility_of_element_located((By.CSS_SELECTOR, INPUT_FIELD_SELECTOR))
            )
            input_field.clear()
            input_field.send_keys(text)
            input_field.send_keys(Keys.ENTER)

        except WebDriverException:
            print("Браузер был закрыт. Перезапуск браузера...")
            driver.quit()
            driver = None
            time.sleep(1)  # Задержка перед перезапуском
            start_driver()
            insert_text_into_field(text)  # Повторяем вставку текста после перезапуска

        except NoSuchElementException:
            print("Поле ввода не найдено. Возможно, страница не загрузилась.")
            driver.quit()
            driver = None
            time.sleep(1)  # Задержка перед перезапуском
            start_driver()
            insert_text_into_field(text)  # Повторяем вставку текста после перезапуска

        except Exception as e:
            print(f"Ошибка при взаимодействии с полем ввода: {e}")

def start_driver():
    global driver
    driver = webdriver.Chrome()
    driver.get(website_url)

keyboard.add_hotkey(START_RECORDING_KEY, start_recording)
keyboard.add_hotkey(STOP_RECORDING_KEY, stop_recording)

print(f"Нажмите '{START_RECORDING_KEY}' для начала записи и '{STOP_RECORDING_KEY}' для остановки.")

try:
    keyboard.wait('esc')
except KeyboardInterrupt:
    print("Программа остановлена пользователем.")
finally:
    exit_flag = True
    if driver is not None:
        driver.quit()
    print("Завершение программы.")
