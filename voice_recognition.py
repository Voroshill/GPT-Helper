import queue
import sys
import speech_recognition as sr
import keyboard
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# Определение горячих клавиш
START_RECORDING_KEY = 'R'
STOP_RECORDING_KEY = 'Q'
# Выход из программы голосом
EXIT_VOICE_COMMAND = "выключи"  # Команда для выхода из программы

# Глобальные переменные
driver = None
website_url = "https://felo.ai/ru/search"  # Укажите нужный URL
INPUT_FIELD_SELECTOR = 'textarea' # Укажите селектор для поля ввода
SEARCH_BUTTON_SELECTOR = 'button[type="submit"]'

q = queue.Queue()  # Очередь для получения текста
recording = False
driver_lock = threading.Lock()  # Блокировка для синхронизации доступа к драйверу браузера
exit_flag = False  # Флаг для обозначения того, что программа должна завершиться

def start_recording():
    global recording
    recording = True
    print(f"Запись начата. Нажмите '{START_RECORDING_KEY}' для остановки или скажите '{EXIT_VOICE_COMMAND}' для выхода.")
    threading.Thread(target=listen).start()  # Запускаем listen в отдельном потоке

def stop_recording():
    global recording
    recording = False
    print("Запись остановлена.")

def listen():
    global exit_flag  # Объявляем exit_flag как глобальную переменную
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        while recording and not exit_flag:
            print("Скажите что-нибудь...")
            audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio, language='ru-RU')
                print(f"Вы сказали: {text}")
                q.put(text)  # Добавляем текст в очередь

                # Проверяем, не была ли произнесена команда для выхода
                if EXIT_VOICE_COMMAND in text.lower():
                    print("Выход из программы...")
                    exit_flag = True  # Устанавливаем флаг для завершения программы

            except sr.UnknownValueError:
                print("Не удалось распознать звук.")
            except sr.RequestError as e:
                print(f"Ошибка сервиса распознавания: {e}")

def send_text_to_website():
    global driver
    while True:
        text = q.get()  # Получаем текст из очереди
        if text is None:
            break

        with driver_lock:  # Блокируем доступ к драйверу браузера
            if driver is None or not driver:
                # Создаем новый экземпляр драйвера для Яндекс.Браузера
                driver = webdriver.Chrome()  # Убедитесь, что драйвер установлен и доступен

            # Открываем указанный сайт
            driver.get(website_url)

            try:
                # Явное ожидание для поиска поля ввода и кнопки отправки/поиска
                input_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, INPUT_FIELD_SELECTOR))
                )
                search_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_BUTTON_SELECTOR))
                )

                # Убедимся, что поле ввода активно
                input_field.click()  # Кликаем по полю ввода, чтобы установить фокус
                input_field.clear()  # Очищаем поле ввода перед вставкой
                input_field.send_keys(text)  # Вставляем текст

                # Нажимаем кнопку отправки/поиска
                search_button.click()

                # После отправки запроса находим ссылку "Результаты поиска" и переходим по ней
                link = driver.find_element(By.LINK_TEXT, 'Результаты поиска')
                link.click()

                # Продолжаем работу с веб-сайтом после перехода по ссылке

            except Exception as e:
                print(f"Ошибка при взаимодействии с полем ввода или кнопкой отправки/поиска: {e}")

def close_driver():
    global driver
    with driver_lock:  # Блокируем доступ к драйверу браузера
        if driver is not None:
            driver.quit()
            driver = None

# Назначаем клавиши для управления записью
keyboard.add_hotkey(START_RECORDING_KEY, start_recording)
keyboard.add_hotkey(STOP_RECORDING_KEY, stop_recording)

print(f"Нажмите '{START_RECORDING_KEY}' для начала записи и '{STOP_RECORDING_KEY}' для остановки.")
threading.Thread(target=send_text_to_website).start()  # Запускаем send_text_to_website в отдельном потоке
keyboard.wait('esc')  # Ожидание нажатия клавиши Esc для завершения

# Устанавливаем флаг для завершения программы
exit_flag = True
# Отправляем None в очередь, чтобы▕