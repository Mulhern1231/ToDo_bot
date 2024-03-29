import telebot
from telebot import types

import datetime
from datetime import timedelta
import pytz
import locale

import bd
import config

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import re
import dateparser

import math

import threading
import time


from dateparser import parse as dateparser_parse
from dateutil.relativedelta import relativedelta




def log_to_file(*messages, filename='log.txt'):
    # Join all messages into a single string
    message = ' '.join(map(str, messages))

    # Get the current time and format it
    current_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')

    # Print the message to the console
    print(message)

    # Write the message to the file, prefixing it with the current time
    with open(filename, 'a') as file:
        file.write(f'{current_time} - {message}\n')






TASKS_PER_PAGE = config.TASKS_PAGE
bot = telebot.TeleBot(config.TOKEN)


# functions
def date_format(date):
    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    return datetime.datetime.strftime(date, '%d.%m.%Y %H:%M')

def convert_timezone(time_first: str, timezone_first: str, timezone_second: str) -> str:
    datetime_first = datetime.datetime.strptime(
        time_first, "%Y-%m-%d %H:%M:%S")
    datetime_first = pytz.timezone(timezone_first).localize(datetime_first)
    datetime_second = datetime_first.astimezone(pytz.timezone(timezone_second))
    time_second = datetime_second.strftime("%Y-%m-%d %H:%M:%S")
    return time_second

def pluralize(n, forms):
    if (n%10==1 and n%100!=11):
        return forms[0]
    elif (n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20)):
        return forms[1]
    else:
        return forms[2]

def calculate_time_diff(start_date, end_date):
    difference = end_date - start_date

    # получим количество дней и секунд
    days, seconds = difference.days, difference.seconds

    # переводим секунды в часы
    hours = seconds // 3600

    # Отображаем разницу во времени
    if days > 0:
        return f"на {days} {pluralize(days, ['день', 'дня', 'дней'])}"
    elif hours > 0:
        return f"на {hours} {pluralize(hours, ['час', 'часа', 'часов'])}"
    
def normal_date(date):
    # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
    task_datetime = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    # Словари для перевода
    months = {
        "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
        "May": "мая", "June": "июня", "July": "июля", "August": "августа",
        "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
    }
    weekdays = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }

    formatted_datetime = task_datetime.strftime('%d %B %Y (%A) в %H:%M')
    time = task_datetime.strftime('в %H:%M')
    # Замена на русские названия
    for eng, rus in months.items():
        formatted_datetime = formatted_datetime.replace(eng, rus)
    for eng, rus in weekdays.items():
        formatted_datetime = formatted_datetime.replace(eng, rus)
    return formatted_datetime

def check_date_in_message(message):
    message = message.lower()

    date_formats = [
        r"\b(?:понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)\s*\d{1,2}(:\d{2})?\b",  # В/на (день недели) HH(:MM)
        r"\b(?:понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\s*\d{1,2}(:\d{2})?\b",  #(день недели) HH(:MM)
        r"\bчерез\s(?:\d+|один|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять)\s(?:дней|недель|месяцев|лет|дня|недели|неделю|месяц|года|год)(?:\s\d{2}:\d{2})?\b",
        r"\bзавтра \d{1,2}:\d{2}\b",
        r"\bсегодня \d{1,2}:\d{2}\b",  # завтра HH:MM
        r"\bпослезавтра \d{1,2}:\d{2}\b",  # послезавтра в HH:MM
        r"\b(завтра|послезавтра) \d{1,2}\b",  # NEW FORMAT
        r"\b\d{1,2}\.\d{1,2}\s \s\d{1,2}:\d{2}\b",  # NEW FORMAT
        r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s \s\d{1,2}:\d{2}\b",  # NEW FORMAT
        r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s\d{1,2}:\d{2}\b",  # DD (месяц словом) HH:MM
        r"\b\d{1,2}\.\d{1,2}\s\d{1,2}:\d{2}\b",  # DD.MM HH:MM
        r"\b\d{1,2}\.\d{1,2}\s\d{1,2}-\d{2}\b",  # DD.MM HH-MM
        r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b",  # DD (месяц словом)
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\s\d{1,2}:\d{2}\b", 
        r"\b\d{1,2}\.\d{1,2}\.\d{2}\s\d{1,2}:\d{2}\b", 
        r"\b\d{1,2}:\d{2}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{2}\b",
        r"\b\d{1,2}-\d{2}\b",
        r"\bзавтра\b",
        r"\bпослезавтра\b",
        r"\bчерез\s(?:неделю|месяц|год|полгода)\b",
        r"\b(?:понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\b",  # В понедельник, Во вторник, и т.д.
        r"\b(?:сегодня|завтра|послезавтра)\b",  # Сегодня, Завтра, Послезавтра
        r"\bчерез\s(?:\d+|один|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять)\s(?:дней|недель|месяцев|лет|дня|недели|неделю|месяц|года|год)\b",  # Через N дней/недель/месяцев/лет
        r"\bв\s\d{1,2}\b"  # В 15
    ]

    prepositions = ['в', 'на'] 

    for date_format in date_formats:
        match = re.search(date_format, message)
        if match:
            date_str = match.group(0)
            date_str_with_preposition = None
            
            if re.match(r"\b(?:понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье)\s*\d{1,2}(:\d{2})?\b", date_str):
                # Обработка дней недели и времени
                day_of_week_str, time_str = date_str.split()[0], date_str.split()[1]
                days_of_week = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
                days_shift = days_of_week.index(day_of_week_str) - datetime.datetime.today().weekday()
                if days_shift <= 0:
                    days_shift += 7
                hour, minute = int(time_str.split(':')[0]), int(time_str.split(':')[1]) if ':' in time_str else 0
                date_obj = (datetime.datetime.now() + datetime.timedelta(days=days_shift)).replace(hour=hour, minute=minute)
            elif re.match(r"\b(?:понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\s*\d{1,2}(:\d{2})?\b", date_str):
                # Обработка дней недели и времени без предлога
                day_of_week_str, time_str = date_str.split()[0], date_str.split()[1]
                days_of_week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
                days_shift = days_of_week.index(day_of_week_str) - datetime.datetime.today().weekday()
                if days_shift <= 0:
                    days_shift += 7
                hour, minute = int(time_str.split(':')[0]), int(time_str.split(':')[1]) if ':' in time_str else 0
                date_obj = (datetime.datetime.now() + datetime.timedelta(days=days_shift)).replace(hour=hour, minute=minute)
            elif re.match(r"\bзавтра \d{1,2}:\d{2}\b", date_str) or re.match(r"\b(завтра|послезавтра) \d{1,2}\b", date_str):
                # Обработка "завтра/послезавтра в HH" и "завтра/послезавтра на HH"
                date_obj = dateparser_parse(date_str.replace(' в ', ' ').replace(' на ', ' ') +":00")
                if date_obj is None:
                    continue
            elif re.match(r"\b\d{1,2}\.\d{1,2}\s\d{1,2}:\d{2}\b", date_str):
                # Обработка "DD.MM в HH:MM"
                date_obj = dateparser_parse(date_str)
                if date_obj is None:
                    continue
                if date_obj.year == 1900:
                    date_obj = date_obj.replace(year=datetime.datetime.now().year)
            elif re.match(r"\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s \s\d{1,2}:\d{2}\b", date_str):
                # Обработка "DD (месяц словом) в HH:MM"
                date_str = date_str.replace(' в ', ' ')
                date_obj = dateparser_parse(date_str)

                log_to_file(date_obj)
                if date_obj is None:
                    continue              
            elif date_str.startswith("завтра") and len(date_str.split(" ")) == 2:
                time_str = date_str.split(" ")[1]
                date_obj = datetime.datetime.now() + datetime.timedelta(days=1)
                date_obj = date_obj.replace(hour=int(time_str.split(':')[0]), minute=int(time_str.split(':')[1]))
            elif date_str.startswith("послезавтра") and len(date_str.split(" ")) == 2:
                time_str = date_str.split(" ")[1]
                date_obj = datetime.datetime.now() + datetime.timedelta(days=2)
                date_obj = date_obj.replace(hour=int(time_str.split(':')[0]), minute=int(time_str.split(':')[1]))
            elif date_str.startswith("сегодня") and len(date_str.split(" ")) == 2:
                time_str = date_str.split(" ")[1]
                date_obj = datetime.datetime.now()
                date_obj = date_obj.replace(hour=int(time_str.split(':')[0]), minute=int(time_str.split(':')[1]))
            elif date_str in ["завтра", "послезавтра", "сегодня"]:
                if date_str == "завтра":
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=1)
                elif date_str == "сегодня":
                    date_obj = datetime.datetime.now()
                else:
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=2)
            elif re.match(r"\b(?:понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\b", date_str):
                # Обработка дней недели
                day_of_week_str = date_str.split()[0]
                days_of_week = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
                days_shift = days_of_week.index(day_of_week_str) - datetime.datetime.today().weekday()
                if days_shift <= 0:
                    days_shift += 7
                date_obj = datetime.datetime.now() + datetime.timedelta(days=days_shift)
            elif re.match(r"\b(?:сегодня|завтра|послезавтра)\b", date_str):
                # Обработка "сегодня", "завтра", "послезавтра"
                if date_str == "сегодня":
                    date_obj = datetime.datetime.now()
                elif date_str == "завтра":
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=1)
                elif date_str == "послезавтра":
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=2)
            elif re.match(r"\bчерез\s(?:\d+|один|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять)\s(?:дней|недель|месяцев|лет|дня|недели|неделю|месяц|года|год)(?:\s\d{2}:\d{2})?\b", date_str):
                # Обработка "через N дней/недель/месяцев/лет HH:MM"
                time_shift_str = date_str.split()
                numbers = {'один': 1, 
                            'два': 2, 
                            'две': 2, 
                            'три': 3, 
                            'четыре': 4, 
                            'пять': 5, 
                            'шесть': 6,
                            'семь': 7,
                            'восемь': 8,
                            'девять': 9,
                            'десять': 10}
                time_shift = int(time_shift_str[1]) if time_shift_str[1].isdigit() else numbers[time_shift_str[1]]
                time_shift_units = {'день': 'days', 
                                    'дней': 'days', 
                                    'дня': 'days', 
                                    'недель': 'weeks', 
                                    'неделю': 'weeks', 
                                    'недели': 'weeks', 
                                    'месяцев': 'months', 
                                    'месяц': 'months', 
                                    'лет': 'years',
                                    'года': 'years',
                                    'год': 'years',}
                time_shift_unit = time_shift_units[time_shift_str[2]]

                if len(time_shift_str) > 3:  # Если указано время
                    time_str = time_shift_str[3]
                    hours, minutes = map(int, time_str.split(":"))
                else:  # Если время не указано, используется текущее время
                    now = datetime.datetime.now()
                    hours, minutes = now.hour, now.minute

                if time_shift_unit == 'days':
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=time_shift)
                elif time_shift_unit == 'weeks':
                    date_obj = datetime.datetime.now() + datetime.timedelta(weeks=time_shift)
                elif time_shift_unit == 'months':
                    date_obj = datetime.datetime.now() + relativedelta(months=time_shift)
                elif time_shift_unit == 'years':
                    date_obj = datetime.datetime.now() + relativedelta(years=time_shift)

                # Обновляем время в объекте datetime
                date_obj = date_obj.replace(hour=hours, minute=minutes)
            elif re.match(r"\bчерез\s(?:\d+|один|два|две|три|четыре|пять|шесть|семь|восемь|девять|десять)\s(?:дней|недель|месяцев|лет|дня|недели|неделю|месяц|года|год)\b", date_str):
                # Обработка "через N дней/недель/месяцев/лет"
                time_shift_str = date_str.split()
                numbers = {'один': 1, 
                            'два': 2, 
                            'две': 2, 
                            'три': 3, 
                            'четыре': 4, 
                            'пять': 5, 
                            'шесть': 6,
                            'семь': 7,
                            'восемь': 8,
                            'девять': 9,
                            'десять': 10}
                time_shift = int(time_shift_str[1]) if time_shift_str[1].isdigit() else numbers[time_shift_str[1]]
                time_shift_units = {'день': 'days', 
                                    'дней': 'days', 
                                    'дня': 'days', 
                                    'недель': 'weeks', 
                                    'неделю': 'weeks', 
                                    'недели': 'weeks', 
                                    'месяцев': 'months', 
                                    'месяц': 'months', 
                                    'лет': 'years',
                                    'года': 'years',
                                    'год': 'years',}
                time_shift_unit = time_shift_units[time_shift_str[2]]
                if time_shift_unit == 'days':
                    date_obj = datetime.datetime.now() + datetime.timedelta(days=time_shift)
                elif time_shift_unit == 'weeks':
                    date_obj = datetime.datetime.now() + datetime.timedelta(weeks=time_shift)
                elif time_shift_unit == 'months':
                    date_obj = (datetime.datetime.now() + relativedelta(months=time_shift)).date()
                elif time_shift_unit == 'years':
                    date_obj = (datetime.datetime.now() + relativedelta(years=time_shift)).date()
            elif re.match(r"\bчерез\s(?:неделю|месяц|год|полгода)\b", date_str):
                time_shift_str = date_str.split()[1]
                time_shift_units = {'неделю': 'weeks',
                                    'месяц': 'months',
                                    'год': 'years',
                                    'полгода': 'months'}
                time_shift = 6 if time_shift_str == 'полгода' else 1
                time_shift_unit = time_shift_units[time_shift_str]
                if time_shift_unit == 'weeks':
                    date_obj = datetime.datetime.now() + datetime.timedelta(weeks=time_shift)
                elif time_shift_unit == 'months':
                    date_obj = (datetime.datetime.now() + relativedelta(months=time_shift)).date()
                elif time_shift_unit == 'years':
                    date_obj = (datetime.datetime.now() + relativedelta(years=time_shift)).date()
            elif re.match(r"\bв\s\d{1,2}\b", date_str):
                # Обработка "В 15"
                hour_str = date_str.split()[1]
                date_obj = datetime.datetime.now().replace(hour=int(hour_str), minute=0)
                if date_obj < datetime.datetime.now():
                    date_obj += datetime.timedelta(days=1)
            else:
                date_obj = dateparser_parse(date_str)
                if date_obj is None:
                    continue
                if date_obj.year == 1900:
                    date_obj = date_obj.replace(year=datetime.datetime.now().year)
                if re.match(r"\b\d{1,2}:\d{2}\b", date_str):
                    if date_obj.time() < datetime.datetime.now().time():
                        date_obj = date_obj + datetime.timedelta(days=1)
                elif re.match(r"\b\d{1,2}-\d{2}\b", date_str):
                    time_str = date_str.replace('-', ':')
                    date_obj = dateparser_parse(time_str)
                    if date_obj.time() < datetime.datetime.now().time():
                        date_obj = date_obj + datetime.timedelta(days=1)

                # Check if the month has already passed
                if date_obj.month < datetime.datetime.now().month:
                    date_obj = date_obj + relativedelta(years=1)

            if date_obj:
                while date_obj < datetime.datetime.now():
                    date_obj = date_obj.replace(year = date_obj.year + 1)

                for preposition in prepositions:
                    preposition_with_space = ' ' + preposition + ' '
                    if preposition_with_space + date_str in message:
                        date_str_with_preposition = preposition_with_space + date_str
                        break

                if date_obj.time() == datetime.datetime.min.time():
                    current_time = datetime.datetime.now().time()
                    date_obj = datetime.datetime.combine(date_obj.date(), current_time)

                return date_str_with_preposition if date_str_with_preposition else date_str, date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return None, None

def check_recurring_in_message(message):
    recurring_formats = ["каждый день", "каждую неделю", "каждый месяц",
                         "каждый понедельник", "каждый вторник", "каждую среду",
                         "каждый четверг", "каждую пятницу", "каждую субботу",
                         "каждое воскресенье"]
    for i in range(2, 31):
        recurring_formats.append(f"каждые {i} дня")  # for 2-4 days
        recurring_formats.append(f"каждые {i} дней")  # for 5-30 days
    for recurring_format in recurring_formats:
        if recurring_format in message.lower():
            return recurring_format
    return None

def get_next_weekday(weekday: int):
    """
    Get the next weekday from the current date.
    weekday -- int : a number representing a weekday where Monday is 0 and Sunday is 6
    """
    current_weekday = datetime.datetime.now().weekday()
    days_ahead = weekday - current_weekday
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return datetime.datetime.now() + timedelta(days=days_ahead)

def update_datetime_with_time(dt: datetime, time: str):
    """
    Update the time in the datetime object.
    dt -- datetime : datetime object to update
    time -- str : string with the time to set
    """
    time_obj = datetime.datetime.strptime(time, '%H:%M')
    return dt.replace(hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second)

def get_sorted_birthdays():
    users = bd.get_all_users()
    today = datetime.datetime.now()
    birthday_data = []
    for user in users:
        if user[4] == None:
            continue
        birth_date = datetime.datetime.strptime(
            user[4], '%d.%m.%Y')  # Формат даты 'день.месяц.год'
        age = today.year - birth_date.year - \
            ((today.month, today.day) < (birth_date.month, birth_date.day))
        if (birth_date.month, birth_date.day) >= (today.month, today.day):
            sort_order = 0
        else:
            sort_order = 1
        birthday_data.append((user[2], user[3], birth_date, age, sort_order))
    birthday_data.sort(key=lambda x: (x[4], x[2].month, x[2].day))
    return birthday_data

def get_next_birthday(birth_date):
    now = datetime.datetime.now()
    next_birthday = datetime.datetime(now.year, birth_date.month, birth_date.day)
    if now > next_birthday:
        next_birthday = datetime.datetime(now.year + 1, birth_date.month, birth_date.day)
    return next_birthday




# task functions
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Метод для добавления пользователя
    bd.add_user(message.chat.id, message.chat.username,
                message.chat.first_name, message.chat.last_name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Старт 🏄🏽‍♂️")
    markup.add(start_button)

    bot.send_message(
        message.chat.id,
        '*Workie_bot на связи* 👋\n'
        'Я твой личный помощник в Телеграм! Ты ставишь задачи себе и другим, '
        'а я контролирую их выполнение, предупреждаю о дедлайнах и напоминаю тебе о важном, '
        'чтобы ты всегда был в курсе своих дел. Давай начнем!',
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data == "send_location")
def ask_for_location(call):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True)
    location_button = types.KeyboardButton(
        'Отправить геопозицию 🌎', request_location=True)
    markup.add(location_button)
    bot.send_message(call.message.chat.id,
                     'Пожалуйста, отправьте свою геопозицию.', reply_markup=markup)
    bot.register_next_step_handler(call.message, location)


@bot.callback_query_handler(func=lambda call: call.data == "input_city")
def ask_for_city(call):
    a = telebot.types.ReplyKeyboardRemove()
    bot.send_message(call.message.chat.id,
                     'Пожалуйста, введите название своего города ✍️', reply_markup=a)
    bot.register_next_step_handler(call.message, city)


def city(message):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(message.text.strip())
    if location:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(
            lat=location.latitude, lng=location.longitude)
        bd.update_timezone(message.chat.id, timezone_str)
        if bd.get_user(message.chat.id)[6] is None:

            timezone_info = pytz.timezone(timezone_str)
            timezone_name = timezone_info.zone
            utc_offset = datetime.datetime.now(timezone_info).strftime('%z')
            utc_offset = str(utc_offset)[0] + str(int(utc_offset[1:3]))

            bot.send_message(message.chat.id, f"Часовой пояс установлен: {timezone_name} (UTC{str(utc_offset)})")
            sent = bot.send_message(
                message.chat.id, "☕️ Теперь напиши время когда ты хочешь получать список задач на день (например 12:00).")
            bot.register_next_step_handler(sent, update_morning_plan, True)
        else:
            timezone_info = pytz.timezone(timezone_str)
            timezone_name = timezone_info.zone
            utc_offset = datetime.datetime.now(timezone_info).strftime('%z')
            utc_offset = str(utc_offset)[0] + str(int(utc_offset[1:3]))

            bot.send_message(message.chat.id, f"Часовой пояс установлен: {timezone_name} (UTC{str(utc_offset)})", reply_markup=main_menu_markup())
    else:
        sent = bot.send_message(
            message.chat.id, 'Не удалось определить город. Пожалуйста, попробуйте снова.')
        bot.register_next_step_handler(sent, city)


@bot.message_handler(commands=['menu'])
def menu(message):
    bot.send_message(message.chat.id, 'Выберите действие:',
                     reply_markup=main_menu_markup())


@bot.message_handler(func=lambda message: message.text == 'Старт 🏄🏽‍♂️')
def start_menu_2(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    location_button = types.InlineKeyboardButton(
        "Отправить геопозицию 🌎", callback_data="send_location")
    manual_input_button = types.InlineKeyboardButton(
        "Настроить вручную ✍️", callback_data="input_city")
    markup.add(location_button, manual_input_button)

    bot.send_message(
        message.chat.id,
        'Давай настроим твой часовой пояс.',
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda message: message.text == 'Задачи 🎯')
def tasks_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item3 = types.InlineKeyboardButton(
        'Личные задачи 👨‍💻', callback_data=f'my_tasks_{message.chat.id}')
    item4 = types.InlineKeyboardButton(
        'Задачи коллег 📚', callback_data=f'colleagues_tasks_{message.chat.id}')
    markup.add(item3, item4)

    bot.send_message(message.chat.id, 'Выберите тип задачи:',
                     reply_markup=markup)


def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item1 = types.KeyboardButton('Задачи 🎯')
    item2 = types.KeyboardButton('Настройки ⚙️')
    item3 = types.KeyboardButton('Справка 📄')
    markup.add(item1, item2, item3)
    return markup


@bot.message_handler(func=lambda message: message.text == 'Настройки ⚙️')
def settings_message(message):
    handle_settings(message)


@bot.message_handler(func=lambda message: message.text == 'Справка 📄')
def help_message(message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton(
        text="Как пользоваться Workie 🎮", callback_data="how_to_use")
    button2 = types.InlineKeyboardButton(
        text="Список дней рождений 🎂", callback_data=f"birthdays_list_{message.chat.id}")
    button3 = types.InlineKeyboardButton(
        text="Статистика Workie 🔍", callback_data="workie_stats")
    keyboard.add(button1, button2, button3)

    bot.send_message(
        message.chat.id, "Выберите одну из следующих опций:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Вернуться в главное меню')
def back_to_main(message):
    menu(message)


# @bot.message_handler(func=lambda message: message.text == 'Создать задачу для другого')
# def create_task_for_others_message(message):
#     create_task_for_others(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        log_to_file(call.data)
        # кнопки
        if call.data.startswith("my_tasks"):
            _, _, id = call.data.split("_")
            view_type_tasks(call, id)
        elif call.data == "create_personal_task":
            create_task(call.message)
        elif call.data.startswith("colleagues_tasks"):
            _, _, id = call.data.split("_")
            view_tasks_for_others(call, id=id)

        elif call.data == "how_to_use":
            bot.edit_message_text(chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f"<strong>🎮 Гайд по работе с Workie Bot</strong>\n"
                            "1. Чтобы поставить задачу себе, просто напиши <strong>текст + дата + время</strong>.\n"
                            "<em>Например: Сделать презентацию 23 июня 15:00;</em>\n"
                            "2. Чтобы поставить задачу коллеге, напиши <strong>@никнейм + текст + дата + время</strong>.\n"
                            "<em>Например: @xxx провести встречу завтра 13:45;</em>\n"
                            "3. Для удобства используй слова \"сегодня\", \"завтра\", \"послезавтра\" или конкретный день недели;\n"
                            "4. Чтобы создать повторяющуюся задачу, напиши <strong>текст + \"каждую неделю/месяц/среду\" + время</strong>.\n"
                            "<em>Например: Сделать платеж каждый месяц 12:30;</em>\n"
                            f"5. Свои идеи и предложения отправляйте сюда: {config.NAME_SECOND_BOT}.\n\n"
                            "Спасибо, что вы с Workie Bot!",
                        parse_mode='HTML',)

        elif call.data.startswith("birthdays_list"):
            _, _, id = call.data.split("_")
            show_birthdays(id)
        elif call.data == "workie_stats":
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="🔍 Статистика Workie_bot\n\n"
                                  f"▶️ Количество пользователей: {len(bd.get_all_users())}\n"
                                  f"▶️ Кол-во выполненных задач: {len(bd.get_completed_tasks_all())}\n\n"
                                  "<em>*Данные обновляются каждый 24 часа</em>",
                                  parse_mode='HTML')

        elif call.data == "change_timezone":
            handle_change_timezone(call.message)

        elif call.data == "profile":
            user_info = bd.get_user(call.message.chat.id)
            profile_info = f"🫰🏽 Настройка Личных данных \n\nИмя: {user_info[2]}\nФамилия: {user_info[3]}\nТелеграм @Ник: {user_info[1]}\nДень рождения: {user_info[4]}\n"
            markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton(
                "Имя 🖌", callback_data="editprof_first_name")
            item2 = types.InlineKeyboardButton(
                "Фамилия 🖍", callback_data="editprof_last_name")
            item3 = types.InlineKeyboardButton(
                "Ник 🔖", callback_data="editprof_nickname")
            item4 = types.InlineKeyboardButton(
                "ДР 🎂", callback_data="editprof_birth_date")
            markup.add(item1, item2, item3, item4)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, text=profile_info, reply_markup=markup)
        elif call.data.startswith("editprof_"):
            field = call.data.replace("editprof_", "")
            field_dict = {"first_name": "Имя", "last_name": "Фамилия",
                          "nickname": "Ник", "birth_date": "День рождения"}

            if field_dict[field] == "День рождения":
                text = f"Введите новое значение для поля {field_dict[field]} в формате дд.мм.гггг"
            else:
                text = f"Введите новое значение для поля {field_dict[field]}"
            
            a = telebot.types.ReplyKeyboardRemove()
            sent = bot.send_message(call.message.chat.id, text, reply_markup=a)
            bot.register_next_step_handler(sent, update_profile, field)

        elif call.data == "reports":
            markup = types.InlineKeyboardMarkup(row_width=1)
            item1 = types.InlineKeyboardButton(
                "Утренний план ☕️", callback_data="morning_plan")
            item2 = types.InlineKeyboardButton(
                "Вечерний отчет 🍾", callback_data="evening_report")
            markup.add(item1, item2)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выберите один из вариантов", reply_markup=markup)
        elif call.data == "morning_plan":
            sent = bot.send_message(
                call.message.chat.id, "☕️ Напиши время когда ты хочешь получать список задач на день.")
            bot.register_next_step_handler(sent, update_morning_plan)
        elif call.data == "evening_report":
            sent = bot.send_message(
                call.message.chat.id, "🍾 Напиши время для получения ежедневного отчета о проделанной работе за день.")
            bot.register_next_step_handler(sent, update_evening_report)

        elif call.data.startswith("viewdone_"):
            _, user, page = call.data.split("_")
            task_done(user, int(page))
        elif call.data.startswith("viewbirthdays_"):
            _, user, page = call.data.split("_")
            show_birthdays(user, int(page))

        # функции
        elif call.data.startswith("user_"):
            _, user, page, user_start = call.data.split("_")
            view_type_tasks_for_others(
                call.message, user, int(page), call, user_start)
        elif call.data.startswith("for_other|"):
            _, user, status, page, user_start = call.data.split("|")
            view_tasks_for_other_user(call.message, user, status, int(page), call, user_start)
        elif call.data.startswith("next_page"):
            _, _, current_page = call.data.split("_")
            current_page = int(current_page)
            view_tasks_for_others(call.message, current_page + 1)
        elif call.data.startswith("prev_page"):
            _, _, current_page = call.data.split("_")
            current_page = int(current_page)
            view_tasks_for_others(call.message, current_page - 1)
        elif call.data.startswith("back|"):
            _, page, id = call.data.split("|")
            view_tasks_for_others(call, int(page), id)
        elif call.data.startswith("backtask_"):
            chat_id = call.message.chat.id
            markup = types.InlineKeyboardMarkup(row_width=1)
            item3 = types.InlineKeyboardButton(
                'Личные задачи 👨‍💻', callback_data=f'my_tasks_{chat_id}')
            item4 = types.InlineKeyboardButton(
                'Задачи коллег 📚', callback_data=f'colleagues_tasks_{chat_id}')
            markup.add(item3, item4)

            bot.edit_message_text(chat_id=chat_id, 
                                  message_id=call.message.message_id, 
                                  text='Выберите тип задачи:', 
                                  reply_markup=markup)


        elif call.data.startswith("view_"):
            _, status, page = call.data.split("_")
            view_tasks(call.message, status, int(page))
        elif call.data.startswith("delete_mode_"):
            _, f1, status, page = call.data.split("_")
            view_tasks(call.message, status, int(page), delete_mode=True)
        elif call.data.startswith("delete_"):
            _, id, status, page, task_id = call.data.split("_")

            tasks = bd.get_tasks(int(id), status)
            page = int(page)
            task_id = int(task_id)

            if tasks:
                pages = math.ceil(len(tasks) / TASKS_PER_PAGE)
                tasks = tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]

            task_id = tasks[task_id][0]
            bd.delete_task(task_id)
            bot.answer_callback_query(call.id, "Задача удалена")
            view_tasks(call.message, status, int(page))
        elif call.data.startswith("edit_mode_"):
            _, f1, status, page = call.data.split("_")
            view_tasks(call.message, status, int(page), edit_mode=True)
        elif call.data.startswith("edit_"):
            _, id, status, page, task_id = call.data.split("_")

            tasks = bd.get_tasks(int(id), status)
            page = int(page)
            task_id = int(task_id)

            if tasks:
                pages = math.ceil(len(tasks) / TASKS_PER_PAGE)
                tasks = tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]

            task_id = tasks[task_id][0]
            bot.answer_callback_query(call.id, "Выберите что изменить")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "🕓  Изменить время задачи", callback_data=f"vi_edit_time_{task_id}"))
            markup.add(types.InlineKeyboardButton(
                "📝 Изменить текст задачи", callback_data=f"vi_edit_text_{task_id}"))
            bot.send_message(call.message.chat.id,
                             "Что вы хотите изменить?", reply_markup=markup)

        elif call.data.startswith("vi_edit_time_"):
            _, _, _, task_id = call.data.split("_")
            bot.send_message(call.message.chat.id,
                             "📅 Пожалуйста, напиши дату и время задачи.")
            bot.register_next_step_handler(
                call.message, change_task_time, task_id)
        elif call.data.startswith("vi_edit_text_"):
            _, _, _, task_id = call.data.split("_")
            bot.send_message(call.message.chat.id,
                             "Введите новый текст для задачи")
            bot.register_next_step_handler(
                call.message, change_task_text, task_id)

        elif call.data.startswith("re_edit_task"):
            _, _, _t, task_id = call.data.split("_")
            edit_task(call.message, task_id)
        elif call.data.startswith("re_canceled_task"):
            _, _, _t, task_id = call.data.split("_")
            delete_task(call.message, task_id)

        elif call.data.startswith("accept_"):
            task_id = int(call.data.split('_')[1])
            user_id = call.from_user.id  # Получаем ID пользователя

            if bd.is_user_in_db(user_id):
                bd.set_task_status(task_id, 'pending')
                bd.set_task_user_id(task_id, user_id)

                # Получаем информацию о задаче
                task = bd.get_task(task_id)

                user_timezone = bd.get_timezone_with_user_id(user_id)
                converted_time = convert_timezone(
                    task[3], task[6], user_timezone)

                bd.edit_task(task_id, converted_time)
                bd.edit_task_timezone(task_id, user_timezone)

                task_text = task[2]
                # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
                task_datetime = datetime.datetime.strptime(
                    task[3], "%Y-%m-%d %H:%M:%S")

                # Словари для перевода
                months = {
                    "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                    "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                    "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
                }
                weekdays = {
                    "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
                    "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
                }

                formatted_datetime = task_datetime.strftime(
                    '%d %B %Y (%A) в %H:%M')
                time = task_datetime.strftime('в %H:%M')
                # Замена на русские названия
                for eng, rus in months.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                for eng, rus in weekdays.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                if task[8] == None:
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                else:
                    if task[8].split()[0] != 'на':
                        time_req = str(task[8]) + ' ' + time
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                                            parse_mode='HTML')
                    else:
                        time_req = str(task[8])
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                            parse_mode='HTML')
                        
            else:
                username = call.from_user.username
                bot.send_message(
                    call.message.chat.id, f"К сожалению, я не могу найти @{username} в базе данных. Пожалуйста, войдите в {config.NAME} и выполните начальную настройку.")

        elif call.data.startswith("accepttask_"):
            _, task_id = call.data.split('_')

            task_id = int(task_id)

            bd.set_task_status(task_id, 'pending')

            # Создаем разметку с обеими кнопками
            markup_with_edit = types.InlineKeyboardMarkup()
            edit_btn = types.InlineKeyboardButton(
                'Изменить ✂️', callback_data=f're_edit_task_{task_id}')
            delete_btn = types.InlineKeyboardButton(
                'Отменить ❌', callback_data=f're_canceled_task_{task_id}')
            markup_with_edit.add(edit_btn, delete_btn)

            # Создаем разметку только с кнопкой "Отменить"
            markup_without_edit = types.InlineKeyboardMarkup()

            # Обновляем сообщение с новой разметкой и новым текстом
            task = bd.get_task(task_id)
            user_add = bd.get_user(task[7])

            input_format = '%Y-%m-%d %H:%M:%S'
            datetime_obj = datetime.datetime.strptime(task[3], input_format)

            # Now you can use strftime() on the datetime_obj
            time = datetime_obj.strftime('в %H:%M')
            if task[8]:
                time_req = '\n🔁 ' + str(task[8]) + ' ' + time
            else:
                time_req = ""

            new_message_text = f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(task[3]))}</b>\n✏️ {str(task[2])} {time_req}\n👤 @{str(user_add[1])}"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=new_message_text,
                parse_mode='HTML',
                reply_markup=markup_with_edit)

            # Запускаем отдельный поток, чтобы обновить разметку через 30 секунд
            def hide_edit_button():
                import time
                time.sleep(30)  # Wait for 30 seconds
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=markup_without_edit)
            
            threading.Thread(target=hide_edit_button).start()

        elif call.data.startswith("deadline|"):
            _, action, task_id = call.data.split("|")

            if action == "1hour":
                new_deadline = datetime.datetime.now() + datetime.timedelta(hours=1)
                bd.edit_task(task_id, new_deadline.strftime('%Y-%m-%d %H:%M:%S'))

                tas = bd.get_task(task_id)
                tas_str = tas[3]
                tas = datetime.datetime.strptime(tas_str, "%Y-%m-%d %H:%M:%S")

                # заменяем часы, минуты, секунды и микросекунды на 0 для tas и new_deadline_aa
                day = calculate_time_diff(tas, new_deadline)
                log_to_file(day)
                bd.edit_new_date(task_id, day)

                # Получаем информацию о задаче
                task = bd.get_task(task_id)
                task_text = task[2]
                # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
                task_datetime = datetime.datetime.strptime(
                    task[3], "%Y-%m-%d %H:%M:%S")

                # Словари для перевода
                months = {
                    "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                    "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                    "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
                }
                weekdays = {
                    "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
                    "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
                }

                formatted_datetime = task_datetime.strftime(
                    '%d %B %Y (%A) в %H:%M')
                time = task_datetime.strftime('в %H:%M')
                # Замена на русские названия
                for eng, rus in months.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                for eng, rus in weekdays.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                if task[8] == None:
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                else:
                    if task[8].split()[0] != 'на':
                        time_req = str(task[8]) + ' ' + time
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                                          parse_mode='HTML')
                    else:
                        time_req = str(task[8])
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                        

            elif action == "3hours":
                new_deadline = datetime.datetime.now() + datetime.timedelta(hours=3)
                bd.edit_task(task_id, new_deadline.strftime(
                    '%Y-%m-%d %H:%M:%S'))

                tas = bd.get_task(task_id)
                tas_str = tas[3]
                tas = datetime.datetime.strptime(tas_str, "%Y-%m-%d %H:%M:%S")

                # заменяем часы, минуты, секунды и микросекунды на 0 для tas и new_deadline_aa
                day = calculate_time_diff(tas, new_deadline)

                bd.edit_new_date(task_id, day)

                # Получаем информацию о задаче
                task = bd.get_task(task_id)
                task_text = task[2]
                # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
                task_datetime = datetime.datetime.strptime(
                    task[3], "%Y-%m-%d %H:%M:%S")

                # Словари для перевода
                months = {
                    "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                    "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                    "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
                }
                weekdays = {
                    "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
                    "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
                }

                formatted_datetime = task_datetime.strftime(
                    '%d %B %Y (%A) в %H:%M')
                time = task_datetime.strftime('в %H:%M')
                # Замена на русские названия
                for eng, rus in months.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                for eng, rus in weekdays.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                if task[8] == None:
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                else:
                    if task[8].split()[0] != 'на':
                        time_req = str(task[8]) + ' ' + time
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                                          parse_mode='HTML')
                    else:
                        time_req = str(task[8])
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')

            elif action == "tmrw":
                new_deadline = datetime.datetime.now() + datetime.timedelta(days=1)
                bd.edit_task(task_id, new_deadline.strftime(
                    '%Y-%m-%d %H:%M:%S'))

                tas = bd.get_task(task_id)
                tas_str = tas[3]
                tas = datetime.datetime.strptime(tas_str, "%Y-%m-%d %H:%M:%S")

                # заменяем часы, минуты, секунды и микросекунды на 0 для tas и new_deadline
                day = calculate_time_diff(tas, new_deadline)

                bd.edit_new_date(task_id, day)

                # Получаем информацию о задаче
                task = bd.get_task(task_id)
                task_text = task[2]
                # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
                task_datetime = datetime.datetime.strptime(
                    task[3], "%Y-%m-%d %H:%M:%S")

                # Словари для перевода
                months = {
                    "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                    "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                    "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
                }
                weekdays = {
                    "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
                    "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
                }

                formatted_datetime = task_datetime.strftime(
                    '%d %B %Y (%A) в %H:%M')
                time = task_datetime.strftime('в %H:%M')
                # Замена на русские названия
                for eng, rus in months.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                for eng, rus in weekdays.items():
                    formatted_datetime = formatted_datetime.replace(eng, rus)
                if task[8] == None:
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                else:
                    if task[8].split()[0] != 'на':
                        time_req = str(task[8]) + ' ' + time
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                                          parse_mode='HTML')
                    else:
                        time_req = str(task[8])
                        bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=f"⚡ Задача запланирована\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                                          parse_mode='HTML')
                        
            elif action == "other":
                msg = bot.send_message(
                    call.message.chat.id, '📅 Напиши дату и время нового дедлайна.')
                bot.register_next_step_handler(msg, edit_task_step, task_id, True)
            elif action == "done":
                bd.set_task_done(task_id)
                task = bd.get_task(task_id)
                bot.send_message(call.message.chat.id, f'✅ {task[2]}')

    except Exception as e:
        log_to_file(e, ' | call.data: ', call.data)


# просмотр задач коллег
def view_tasks_for_others(call, page=0, id=0):
    if id == 0:
        user_id = call.from_user.id
    else:
        user_id = id

    colleagues, total_colleagues = bd.get_colleagues(user_id, page)

    if 0 in colleagues:
        colleagues.remove(0)
    if int(user_id) in colleagues:
        colleagues.remove(int(user_id))

    if colleagues:
        markup = types.InlineKeyboardMarkup()
        for colleague in colleagues:
            if bd.get_user(colleague)[3]:
                name = str(bd.get_user(colleague)[2]) + " " + str(bd.get_user(colleague)[3])
            else:
                name = str(bd.get_user(colleague)[2])
            markup.add(types.InlineKeyboardButton(name, callback_data=f'user_{colleague}_{page}_{user_id}'))
        if page > 0:
            markup.add(types.InlineKeyboardButton(
                "<", callback_data=f"prev_page_{page}"))
        if (page + 1) * TASKS_PER_PAGE < total_colleagues:
            markup.add(types.InlineKeyboardButton(
                ">", callback_data=f"next_page_{page}"))

        # добавляем кнопку "<<Назад"
        markup.add(types.InlineKeyboardButton(
                "<< Назад", callback_data=f"backtask_{call.message.chat.id}"))

        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id,
            text=f"📚 Список ваших коллег", 
            reply_markup=markup)
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id,
            text="Нет задач для коллег")


def view_type_tasks_for_others(message, colleague_id, page=0, call=None, user_start=0):
    colleague_id = int(colleague_id)
    pending_tasks = bd.get_tasks_by_status_and_user_added(colleague_id, 'pending', user_id_added = call.message.chat.id)[1]
    overdue_tasks = bd.get_tasks_by_status_and_user_added(colleague_id, 'overdue', user_id_added = call.message.chat.id)[1]

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(f'Активные ({pending_tasks})', callback_data=f'for_other|{colleague_id}|pending|{page}|{user_start}'),
               types.InlineKeyboardButton(f'Просроченные ({overdue_tasks})', callback_data=f'for_other|{colleague_id}|overdue|{page}|{user_start}'))

    if call:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id, text="Выберите тип задач для просмотра:")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        bot.send_message(
            message.chat.id, "Выберите тип задач для просмотра:", reply_markup=markup)


def view_tasks_for_other_user(message, colleague_id, status, page=0, call=None, user_start=0):
    colleague_id = int(colleague_id)
    user_id = call.message.chat.id
    log_to_file(colleague_id, user_id)
    tasks, total_tasks = bd.get_tasks_by_status_and_user_added(colleague_id, status, user_id, page)

    # Получите часовой пояс пользователя и коллеги
    user_timezone = bd.get_timezone_with_user_id(user_start)

    if tasks:
        pages = math.ceil(total_tasks / TASKS_PER_PAGE)
        text = " 💥 Активные задачи" if status == 'pending' else " ⏰ Просроченные задачи"
        text += f" @ {bd.get_user(colleague_id)[2]} "
        text += str(bd.get_user(colleague_id)[3]) if bd.get_user(colleague_id)[3] else ""

        task_index = page * TASKS_PER_PAGE  # Начальный индекс задачи на текущей странице

        for idx, task in enumerate(tasks, start=task_index + 1):
            # Преобразование времени задачи в часовой пояс пользователя
            converted_time = convert_timezone(task[3], task[6], user_timezone)

            log_to_file(task[3], task[6], user_timezone, converted_time)

            if task[8] == None:
                text += f"\n\n{idx}) 🔔 {normal_date(converted_time)}\n✏️ {task[2]}"
            else:
                task_datetime = datetime.datetime.strptime(
                    converted_time, "%Y-%m-%d %H:%M:%S")
                time = task_datetime.strftime('в %H:%M')
                if task[8].split()[0] != 'на':
                    time_req = str(task[8]) + ' ' + time
                    text += f"\n\n{idx}) 🔔 {normal_date(converted_time)}\n✏️ {task[2]}\n🔁 {time_req}"
                else:
                    time_req = str(task[8])
                    text += f"\n\n{idx}) 🔔 {normal_date(converted_time)}\n✏️ {task[2]}\n🔃 {time_req}"
                
            text += "\n- - - - - - - - - - - - - - - - - - - - - - - -"

        markup = types.InlineKeyboardMarkup()
        buttons = []
        if page > 0:
            buttons.append(types.InlineKeyboardButton(
                "<", callback_data=f'for_other|{colleague_id}|{status}|{page-1}|{user_start}'))
        if page < pages - 1:
            buttons.append(types.InlineKeyboardButton(
                ">", callback_data=f'for_other|{colleague_id}|{status}|{page+1}|{user_start}'))
        buttons.append(types.InlineKeyboardButton(
            "<< Назад", callback_data=f'back|{page}|{user_start}'))
        markup.add(*buttons)

        if call:  # Используйте call.message.chat.id и call.message.message_id для редактирования уже отправленного сообщения
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:  # В случае первого сообщения используйте send_message как обычно
            bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У этого пользователя нет задач.")



# Просмотр задач
def view_type_tasks(call, id):
    user_id = id
    pending_tasks = len(bd.get_tasks(user_id, 'pending'))
    overdue_tasks = len(bd.get_tasks(user_id, 'overdue'))

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(f'Активные ({pending_tasks})', callback_data='view_pending_0'),
               types.InlineKeyboardButton(f'Просроченные ({overdue_tasks})', callback_data='view_overdue_0'))
    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id,
        text="Выберите тип задач для просмотра:", 
        reply_markup=markup)


def view_tasks(message, status, page=0, delete_mode=False, edit_mode=False, id=None):
    if id:
        chat_id = id
    else:
        chat_id = message.chat.id

    tasks = bd.get_tasks(chat_id, status)

    if tasks:
        pages = math.ceil(len(tasks) / TASKS_PER_PAGE)
        tasks = tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]

        text = "💥 Активные задачи" if status == 'pending' else "⏰ Просроченные задачи"

        for idx, task in enumerate(tasks, start=1 + page * TASKS_PER_PAGE):
            if task[8] == None:
                text += f"\n\n{idx}) 🔔 {normal_date(task[3])}\n✏️ {task[2]}"
            else:
                task_datetime = datetime.datetime.strptime(
                    task[3], "%Y-%m-%d %H:%M:%S")
                time = task_datetime.strftime('в %H:%M')

                if task[8].split()[0] != 'на':
                    time_req = str(task[8]) + ' ' + time
                    text += f"\n\n{idx}) 🔔 {normal_date(task[3])}\n✏️ {task[2]}\n🔁 {time_req}"
                else:
                    time_req = str(task[8])
                    text += f"\n\n{idx}) 🔔 {normal_date(task[3])}\n✏️ {task[2]}"
            if task[1] != task[7]:
                text += f"\n👤 @{bd.get_user(task[7])[1]}"

                
            text += "\n- - - - - - - - - - - - - - - - - - - - - - - -"

        markup = types.InlineKeyboardMarkup()
        buttons = []
        if delete_mode:
            for idx in range(len(tasks)):
                buttons.append(types.InlineKeyboardButton(
                    str(idx+1 + page * TASKS_PER_PAGE), callback_data=f'delete_{chat_id}_{status}_{page}_{idx}'))
            buttons.append(types.InlineKeyboardButton(
                "<< Назад", callback_data=f'view_{status}_{page}'))
        elif edit_mode:
            for idx in range(len(tasks)):
                buttons.append(types.InlineKeyboardButton(
                    str(idx+1 + page * TASKS_PER_PAGE), callback_data=f'edit_{chat_id}_{status}_{page}_{idx}'))
            buttons.append(types.InlineKeyboardButton(
                "<< Назад", callback_data=f'view_{status}_{page}'))
        else:
            if page > 0:
                buttons.append(types.InlineKeyboardButton(
                    "<", callback_data=f'view_{status}_{page-1}'))
            if page < pages - 1:
                buttons.append(types.InlineKeyboardButton(
                    ">", callback_data=f'view_{status}_{page+1}'))
            markup.add(*buttons)  # Add navigation buttons to markup

            buttons = []  # Start new row
            buttons.append(types.InlineKeyboardButton(
                "❌ Удалить №", callback_data=f'delete_mode_{status}_{page}'))
            buttons.append(types.InlineKeyboardButton(
                "✂️ Изменить №", callback_data=f'edit_mode_{status}_{page}'))
        markup.add(*buttons)
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Задач не найдено")



def change_task_time(message, task_id):
    chat_id = message.chat.id
    current_time = datetime.datetime.now()

    # Use check_date_in_message to parse the time from the message
    date_str, task_date_str = check_date_in_message(message.text)

    if task_date_str:
        try:
            task_date = datetime.datetime.strptime(
                task_date_str, "%Y-%m-%d %H:%M:%S")
            if task_date < current_time:
                raise ValueError('Время уже прошло.')
        except ValueError:
            bot.send_message(
                chat_id, 'Произошла ошибка при анализе даты. Попробуйте еще раз.')
            msg = bot.send_message(
                chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
            bot.register_next_step_handler(msg, change_task_time, task_id)
            return
    else:
        bot.send_message(chat_id, 'Неверный формат даты. Попробуйте еще раз.')
        msg = bot.send_message(
            chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
        bot.register_next_step_handler(msg, change_task_time, task_id)
        return

    tas = bd.get_task(task_id)
    tas_str = tas[3]
    tas = datetime.datetime.strptime(tas_str, "%Y-%m-%d %H:%M:%S")

    # заменяем часы, минуты, секунды и микросекунды на 0 для tas и task_date
    day = calculate_time_diff(tas, task_date)

    bd.edit_new_date(task_id, day)

    bd.edit_task(int(task_id), task_date)
    bot.send_message(chat_id, "Время задачи изменено")


def change_task_text(message, task_id):
    new_text = message.text
    bd.edit_task_text(int(task_id), new_text)
    bot.send_message(message.chat.id, "Текст задачи изменён")


# просмотр выполненных задач
def task_done(user_id, page=0):
    tasks = bd.get_completed_tasks(user_id)
    if not tasks:
        bot.send_message(user_id, "Выполненных задач не найдено")
    else:
        pages = math.ceil(len(tasks) / TASKS_PER_PAGE)
        log_to_file(page*TASKS_PER_PAGE)
        log_to_file((page+1)*TASKS_PER_PAGE)
        log_to_file(len(tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]))

        message = "🍾 Выполненные задачи за сегодня\n\n"
        for idx, task in enumerate(tasks[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]):
            message += f"{idx+1}) 🔔 {task[3]} \n✅ {task[2]}\n- - - - - - - - - - - - - - - - - - - - - - - -\n"

        if len(tasks) > TASKS_PER_PAGE:
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = []
            if page > 0:
                buttons.append(types.InlineKeyboardButton(
                    "<", callback_data=f'viewdone_{user_id}_{page-1}'))
            if page < pages - 1:
                buttons.append(types.InlineKeyboardButton(
                    ">", callback_data=f'viewdone_{user_id}_{page+1}'))
            markup.add(*buttons)
            bot.send_message(user_id, message, reply_markup=markup)
        else:
            bot.send_message(user_id, message)


# Cоздание задачи
def create_task(message):
    a = telebot.types.ReplyKeyboardRemove()
    msg = bot.send_message(
        message.chat.id, "Отправьте текст задачи", reply_markup=a)
    bot.register_next_step_handler(msg, process_task_step)


def create_task_for_others(message):
    msg = bot.send_message(
        message.chat.id, "Введите имя пользователя (никнейм), для которого вы хотите создать задачу")
    bot.register_next_step_handler(msg, process_user_step)


def process_user_step(message):
    try:
        username = message.text
        user_id = bd.get_user_id(username)
        if user_id is None:
            bot.reply_to(message, 'Пользователь не найден')
            return
        task = bd.Task(user_id, None)

        msg = bot.send_message(message.chat.id, "Отправьте текст задачи")
        bot.register_next_step_handler(msg, process_task_step, task)
    except Exception as e:
        log_to_file(e)
        bot.reply_to(message, 'oooops')


def process_task_step(message, task=None):
    try:
        chat_id = task.user_id_added

        if task.text is None:
            task_text = message.text
        else:
            task_text = task.text

        if task.deadline == None:
            task_date_str, task_date = check_date_in_message(task_text)
            # Check for recurring task information in the text

            if task_date is None:
                bot.send_message(
                    chat_id, 'Некорректный формат даты. Попробуйте еще раз.')
                msg = bot.send_message(
                    chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
                bot.register_next_step_handler(msg, process_date_step, task)
                return

            task_date_obj = datetime.datetime.strptime(task_date, "%Y-%m-%d %H:%M:%S")
            task.set_deadline(task_date)


            # Remove date from the task text
            task_text = task_text.replace(task_date_str, "")
            task.text = task_text.strip()

        recurring_task = check_recurring_in_message(task_text)
        log_to_file(recurring_task, task_text)
        if recurring_task is not None:
            task_text = task_text.replace(recurring_task, '')
            task.text = task_text.strip()
            recurring_task = recurring_task.split(' ')
        if recurring_task is not None:
            task.set_new_date(' '.join(recurring_task))
        
        # Directly proceed to save the task in the database
        task.timezone = bd.get_timezone_with_user_id(chat_id)
        taskID = bd.add_task(task)

        markup = types.InlineKeyboardMarkup()
        edit_btn = types.InlineKeyboardButton(
            'Изменить ✂️', callback_data=f're_edit_task_{taskID}')
        delete_btn = types.InlineKeyboardButton(
            'Отменить ❌', callback_data=f're_canceled_task_{taskID}')
        markup.add(edit_btn, delete_btn)

        if task.user_id != chat_id:
            def hide_edit_button(chat_id, message_id, markup):
                import time
                time.sleep(30)  # Wait for 30 seconds
                bot.edit_message_reply_markup(chat_id, message_id=message_id)


            time = task.deadline.strftime('в %H:%M')
            if task.new_date:
                time_req = '\n🔁 ' + str(task.new_date) + ' ' + time
            else:
                time_req = ""

            sent_message = bot.send_message(chat_id,
                            text=f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(task.deadline))} </b>\n✏️ {str(task.text)} {time_req} \n👤 @{str(bd.get_user(task.user_id)[1])}",
                            parse_mode='HTML',
                            reply_markup=markup)
        
            threading.Thread(target=hide_edit_button, args=(chat_id, sent_message.message_id, markup)).start()
        else:
            def hide_edit_button(chat_id, message_id, markup):
                import time
                time.sleep(30)  # Wait for 30 seconds
                bot.edit_message_reply_markup(chat_id, message_id=message_id)


            time = task.deadline.strftime('в %H:%M')
            if task.new_date:
                time_req = '\n🔁 ' + str(task.new_date) + ' ' + time
            else:
                time_req = ""

            sent_message = bot.send_message(chat_id,
                            text=f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(task.deadline))} </b>\n✏️ {str(task.text)} {time_req}",
                            parse_mode='HTML',
                            reply_markup=markup)
    
            threading.Thread(target=hide_edit_button, args=(chat_id, sent_message.message_id, markup)).start()

        # If the task is not for the sender
        if task.user_id != chat_id:
            try:
                timezone_first = str(task.timezone)
                time_first = str(task.deadline)
                timezone_second = bd.get_timezone_with_user_id(task.user_id)
                time_second = str(convert_timezone(
                    time_first, timezone_first, timezone_second))
            except Exception as e:
                log_to_file(e)
                time_second = task.deadline

            markup = types.InlineKeyboardMarkup()
            accept = types.InlineKeyboardButton('Принять задачу 🤝', callback_data=f'accepttask_{taskID}')
            markup.add(accept)

            time = task.deadline.strftime('в %H:%M')
            if task.new_date:
                time_req = '\n🔁 ' + str(task.new_date) + ' ' + time
            else:
                time_req = ""

            bot.send_message(task.user_id,
                             text=f"от @{bd.get_user(chat_id)[1]}\n\n🔔 <b>{normal_date(str(time_second))} </b>\n✏️ {str(task.text)} {time_req}",
                             parse_mode='HTML',
                             reply_markup=markup)

        bot.send_message(chat_id, 'Выберите действие:',
                         reply_markup=main_menu_markup())
    except Exception as e:
        log_to_file(e)
        bot.reply_to(message, 'oooops')


def process_date_step(message, task):
    try:
        chat_id = message.chat.id
        current_time = datetime.datetime.now()

        date_str, task_date_str = check_date_in_message(message.text)
        if not date_str:
            raise ValueError("Неизвестный формат даты!")

        task_date = datetime.datetime.strptime(
            task_date_str, "%Y-%m-%d %H:%M:%S")

        if task_date < current_time:
            bot.send_message(
                chat_id, 'Дата/время уже прошли. Попробуйте еще раз.')
            msg = bot.send_message(
                chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
            bot.register_next_step_handler(msg, process_date_step, task)
            return

        task.deadline = task_date
        if task.new_date:
            task_date_obj = update_datetime_with_time(
                task_date, task.new_date.split()[-1])
            task.deadline = task_date_obj

        # Directly proceed to save the task in the database
        task.timezone = bd.get_timezone_with_user_id(chat_id)
        taskID = bd.add_task(task)

        markup = types.InlineKeyboardMarkup()
        edit_btn = types.InlineKeyboardButton(
            'Изменить ✂️', callback_data=f're_edit_task_{taskID}')
        delete_btn = types.InlineKeyboardButton(
            'Отменить ❌', callback_data=f're_canceled_task_{taskID}')
        markup.add(edit_btn, delete_btn)


        def hide_edit_button(chat_id, message_id, markup):
            time.sleep(30)  # Wait for 30 seconds
            markup = types.InlineKeyboardMarkup()
            bot.edit_message_reply_markup(chat_id, message_id=message_id, reply_markup=markup)

        sent_message = bot.send_message(chat_id,
                         text=f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(task.deadline))} </b>\n✏️ {str(task.text)}",
                         parse_mode='HTML',
                         reply_markup=markup)
    
        threading.Thread(target=hide_edit_button, args=(chat_id, sent_message.message_id, markup)).start()

        

        bot.send_message(chat_id, 'Выберите действие:',
                         reply_markup=main_menu_markup())
    except Exception as e:
        log_to_file(e)
        bot.reply_to(message, 'Ой, что-то пошло не так...')
        msg = bot.send_message(
            chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
        bot.register_next_step_handler(msg, process_date_step, task)


def process_file_step(message, task):
    try:
        user_id_id = message.from_user.id
        chat_id = message.chat.id
        if message.text == 'Да':
            bot.send_message(chat_id, 'Пожалуйста, отправьте файлы.')
            bot.register_next_step_handler(message, save_file_id, task)
        elif message.text == 'Нет':
            task.timezone = bd.get_timezone_with_user_id(user_id_id)
            taskID = bd.add_task(task)

            markup = types.InlineKeyboardMarkup()
            edit_btn = types.InlineKeyboardButton(
                'Изменить ✂️', callback_data=f're_edit_task_{taskID}')
            delete_btn = types.InlineKeyboardButton(
                'Отменить ❌', callback_data=f're_canceled_task_{taskID}')
            markup.add(edit_btn, delete_btn)



            def hide_edit_button(chat_id, message_id, markup):
                time.sleep(30)  # Wait for 30 seconds
                markup = types.InlineKeyboardMarkup()
                bot.edit_message_reply_markup(chat_id, message_id=message_id, reply_markup=markup)

            sent_message = bot.send_message(chat_id,
                             text=f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(task.deadline))} </b>\n✏️ {str(task.text)}",
                             parse_mode='HTML',
                             reply_markup=markup)
        
            threading.Thread(target=hide_edit_button, args=(chat_id, sent_message.message_id, markup)).start()


            

            # If the task is not for the sender
            if task.user_id != chat_id:
                try:
                    timezone_first = str(task.timezone)
                    time_first = str(task.deadline)
                    timezone_second = bd.get_timezone_with_user_id(
                        task.user_id)
                    time_second = str(convert_timezone(
                        time_first, timezone_first, timezone_second))
                except Exception as e:
                    log_to_file(e)
                    time_second = task.deadline

                bot.send_message(task.user_id,
                                 text=f"⚡ Задача запланирована\n\n🔔 <b>{normal_date(str(time_second))} </b>\n✏️ {str(task.text)}",
                                 parse_mode='HTML',
                                 reply_markup=markup)

            bot.send_message(message.chat.id, 'Выберите действие',
                             reply_markup=main_menu_markup())

    except Exception as e:
        log_to_file(e)
        bot.reply_to(message, 'oooops')


def save_file_id(message, task):
    try:
        chat_id = message.chat.id
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        task.file_id = message.document.file_id

        with open('documents/' + str(file_info.file_path), 'wb') as new_file:
            new_file.write(downloaded_file)

        task.timezone = bd.get_timezone_with_user_id(task.user_id)
        bd.add_task(task)
        bot.send_message(chat_id,
                         text=f"⚡ Задача запланирована\n\n🔔 <b>{str(task.deadline)} </b>\n✏️ {str(task.text)}",
                         parse_mode='HTML',
                         reply_markup=main_menu_markup())

    except Exception as e:
        log_to_file(e)
        bot.reply_to(message, 'oooops')


def attach_file_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Да', 'Нет')
    return markup


def edit_task(message, task_id):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
    bot.register_next_step_handler(msg, edit_task_step, task_id, False)


def edit_task_step(message, task_id, remake = True):
    chat_id = message.chat.id

    current_time = datetime.datetime.now()
    date_str, task_date_str = check_date_in_message(message.text)
    if task_date_str:
        try:
            task_date = datetime.datetime.strptime(
                task_date_str, "%Y-%m-%d %H:%M:%S")
            if task_date < current_time:
                bot.send_message(
                    chat_id, 'Время уже прошло. Попробуйте еще раз.')
                msg = bot.send_message(
                    chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
                bot.register_next_step_handler(msg, process_date_step, task_id)
                return
        except ValueError:
            bot.send_message(
                chat_id, 'Произошла ошибка при анализе даты. Попробуйте еще раз.')
            msg = bot.send_message(
                chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
            bot.register_next_step_handler(msg, process_date_step, task_id)
            return
    else:
        bot.send_message(chat_id, 'Неверный формат даты. Попробуйте еще раз.')
        msg = bot.send_message(chat_id, '📅 Пожалуйста, напиши дату и время задачи.')
        bot.register_next_step_handler(msg, process_date_step, task_id)
        return

    tas = bd.get_task(task_id)
    tas_str = tas[3]
    tas = datetime.datetime.strptime(tas_str, "%Y-%m-%d %H:%M:%S")

    # заменяем часы, минуты, секунды и микросекунды на 0 для tas и task_date
    day = calculate_time_diff(tas, task_date)

    bd.edit_task(task_id, task_date)
    bd.edit_new_date(task_id, day)

    # Получаем информацию о задаче
    task = bd.get_task(task_id)
    task_text = task[2]
    # Предполагается, что формат даты в БД "%Y-%m-%d %H:%M:%S"
    task_datetime = datetime.datetime.strptime(task[3], "%Y-%m-%d %H:%M:%S")

    # Словари для перевода
    months = {
        "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
        "May": "мая", "June": "июня", "July": "июля", "August": "августа",
        "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
    }
    weekdays = {
        "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
        "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
    }

    formatted_datetime = task_datetime.strftime('%d %B %Y (%A) в %H:%M')
    time = task_datetime.strftime('в %H:%M')
    # Замена на русские названия
    for eng, rus in months.items():
        formatted_datetime = formatted_datetime.replace(eng, rus)
    for eng, rus in weekdays.items():
        formatted_datetime = formatted_datetime.replace(eng, rus)
    if task[8] == None:
        if remake == True:
            bot.send_message(chat_id=message.chat.id,
                            text=f"⏳ Задача отложена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                            parse_mode='HTML')
        else:
            bot.send_message(chat_id=message.chat.id,
                            text=f"✂️ Задача изменена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}",
                            parse_mode='HTML')
    else:

        if task[8].split()[0] != 'на':
            time_req = str(task[8]) + ' ' + time
            if remake == True:
                bot.send_message(chat_id=message.chat.id,
                            text=f"⏳ Задача отложена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                            parse_mode='HTML')
            else:
                bot.send_message(chat_id=message.chat.id,
                                text=f"✂️ Задача изменена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔁 {time_req}",
                                parse_mode='HTML')
        else:
            time_req = str(task[8])
            if remake == True:
                bot.send_message(chat_id=message.chat.id,
                            text=f"⏳ Задача отложена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔃 {time_req}",
                            parse_mode='HTML')
            else:
                bot.send_message(chat_id=message.chat.id,
                                text=f"✂️ Задача изменена\n\n🔔 <b>{str(formatted_datetime)} </b>\n✏️ {str(task_text)}\n🔃 {time_req}",
                                parse_mode='HTML')
            
        
        


def delete_task(message, task_id):
    chat_id = message.chat.id
    task = bd.get_task(task_id)
    bd.delete_task(task_id)

    task_id, _, description, task_time, _, _, timezone, _, _ = task

    cancel_message = f"❌ Задача отменена\n\n<s><b>🔔 {normal_date(str(task_time))}</b>\n✏️ {description}</s>"
    bot.send_message(chat_id, cancel_message, parse_mode='HTML')


# Перехват в чатах для создания задачи
@bot.message_handler(content_types=['text'])
def handle_task(message):
    try:
        if bd.is_user_in_db(message.from_user.id):
            if config.NAME in message.text:
                task_text = message.text.replace(config.NAME, '')
                task_datetime_str = message.textrecurring_task

                # Parsing the date and time string into a datetime object
                task_datetime_str, task_datetime = check_date_in_message(
                    task_datetime_str)

                if task_datetime is not None:
                    task_text = task_text.replace(task_datetime_str, '')

                # Checking for recurring task information in the text
                recurring_task = check_recurring_in_message(task_text)
                if recurring_task is not None:
                    task_text = task_text.replace(recurring_task, '')
                    recurring_task = recurring_task.split(' ')

                    if recurring_task[0] == 'каждый':
                        if recurring_task[1] in ['день', 'неделю', 'месяц']:
                            if task_datetime is None:
                                # If no date/time was specified, use the current date/time
                                task_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        else:  # If a weekday is specified
                            weekdays = ['понедельник', 'вторник', 'среду',
                                        'четверг', 'пятницу', 'субботу', 'воскресенье']
                            if recurring_task[1] in weekdays:
                                weekday_number = weekdays.index(
                                    recurring_task[1])
                                next_weekday = get_next_weekday(weekday_number)
                                if task_datetime is None:
                                    # If no date/time was specified, use the next occurrence of the weekday
                                    task_datetime = next_weekday.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                else:  # If a time was specified, update the time in the next weekday
                                    task_datetime_obj = datetime.datetime.strptime(
                                        task_datetime, "%Y-%m-%d %H:%M:%S")
                                    task_datetime_obj = update_datetime_with_time(
                                        next_weekday, task_datetime_obj.strftime('%H:%M'))
                                    task_datetime = task_datetime_obj.strftime(
                                        "%Y-%m-%d %H:%M:%S")

                if task_datetime is None:
                    bot.send_message(message.from_user.id, 'Некорректный формат даты. Попробуйте еще раз.')
                    return

                task_datetime = datetime.datetime.strptime(
                    task_datetime, '%Y-%m-%d %H:%M:%S')
                task_datetime_old = task_datetime
                now = datetime.datetime.now()

                if task_datetime < now:
                    task_datetime = now + datetime.timedelta(days=1)
                    task_datetime = task_datetime.replace(
                        hour=task_datetime_old.hour, minute=task_datetime_old.minute)

                task_datetime = task_datetime.strftime("%Y-%m-%d %H:%M:%S")

                # Create a task and add it to the database
                task = bd.Task(0, task_text)
                task.set_deadline(task_datetime)
                task.set_status("Wait")
                task.set_timezone(
                    bd.get_timezone_with_user_id(message.from_user.id))
                task.set_user_id_added(message.from_user.id)
                if recurring_task is not None:
                    task.set_new_date(' '.join(recurring_task))
                task_id = bd.add_task(task)

                # Создание inline-кнопки для подтверждения задачи
                markup = types.InlineKeyboardMarkup()
                accept_button = types.InlineKeyboardButton(
                    'Принять задачу 🤝', callback_data=f'accept_{task_id}')
                markup.add(accept_button)

                # Отправка сообщения с кнопкой
                task_datetime_obj = datetime.datetime.strptime(
                    task_datetime, "%Y-%m-%d %H:%M:%S")
                mon = task_datetime_obj.strftime('%A')
                months = {
                    "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                    "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                    "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
                }
                for eng, rus in months.items():
                    mon = mon.replace(eng, rus)
                bot.send_message(
                    message.chat.id, f"от {config.NAME}\n\n🔔 {task_datetime_obj.strftime('%d.%m.%Y %H:%M')} ({mon})\n✏️ {task_text}", reply_markup=markup)
            else:
                task_text = message.text

                
                match = re.search(r'@(\w+)', task_text)

                if match:
                    username = match.group(1)
                    task_text = task_text.replace('@' + username, '').strip()
                    user_id = bd.get_user_id(username)

                    if user_id is None:
                        bot.reply_to(message, 'Пользователь не найден')
                        return
                    task = bd.Task(user_id, None)
                    task.status = "Wait"
                else:
                    chat_id = message.chat.id
                    task = bd.Task(chat_id, None)


                recurring_task = check_recurring_in_message(task_text)
                if recurring_task is not None:
                    recurring_task = recurring_task.split(' ')
                    task.new_date = ' '.join(recurring_task)

                    recurring_task = ' '.join(recurring_task)
                    days = ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]
                    for day in days:
                        recurring_task = recurring_task.replace(day, "")
                    task_text = task_text.replace(recurring_task, '')
                    
                log_to_file(task_text)
                date_str, task_date_str = check_date_in_message(task_text)
                if date_str:
                    task.text = task_text.replace(date_str, "")
                else:
                    task.text = task_text
                log_to_file(task_date_str)
                
                task.set_user_id_added(message.from_user.id)

                if task_date_str is None:
                    bot.send_message(message.from_user.id, '📅 Пожалуйста, напиши дату и время задачи.')
                    bot.register_next_step_handler(message, handle_date, task)
                else:
                    task_date = datetime.datetime.strptime(
                        task_date_str, "%Y-%m-%d %H:%M:%S")
                    task.set_deadline(task_date)
                    process_task_step(message, task)
        else:
            username = message.from_user.username
            bot.send_message(
                message.from_user.id, f"К сожалению, я не могу найти @{username} в базе данных. Пожалуйста, войдите в {config.NAME} и выполните начальную настройку.")
    except Exception as e:
        log_to_file(e)


def handle_date(message, task):
    date_str, task_date_str = check_date_in_message( str(task.text) + " " + str(message.text))

    log_to_file(str(task.text) + " " + str(message.text), " / ", date_str, " / ", task_date_str)
    
    # Если дата не найдена, просим пользователя указать ее еще раз
    if task_date_str:
        task_date = datetime.datetime.strptime(task_date_str, "%Y-%m-%d %H:%M:%S")
        task.deadline = task_date
        process_task_step(message, task)
    else:
        bot.send_message(message.from_user.id, '📅 Пожалуйста, напиши дату и время задачи.')
        bot.register_next_step_handler(message, handle_date, task)
        


# Настройки
def handle_settings(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton(
        "Сменить часовой пояс 🌓", callback_data="change_timezone")
    item2 = types.InlineKeyboardButton(
        "Личные данные 🫰🏽", callback_data="profile")
    item3 = types.InlineKeyboardButton("Отчеты 📊", callback_data="reports")
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, 'Выберите настройку:',
                     reply_markup=markup)

# Обновления профиля


def update_profile(message, field):
    text = message.text
    if field == "first_name":
        bd.update_user_first_name(message.chat.id, text)
        bot.send_message(message.chat.id, "Данные успешно обновлены!")
    elif field == "last_name":
        bd.update_user_last_name(message.chat.id, text)
        bot.send_message(message.chat.id, "Данные успешно обновлены!")
    elif field == "nickname":
        bd.update_user_nickname(message.chat.id, text)
        bot.send_message(message.chat.id, "Данные успешно обновлены!")
    elif field == "birth_date":
        # Поиск даты в формате dd.mm.yyyy
        date_match = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', text)
        if date_match:
            # Преобразование найденного текста в объект datetime
            date_obj = datetime.datetime.strptime(date_match.group(), '%d.%m.%Y')
            bd.update_user_birth_date(message.chat.id, date_obj.strftime("%d.%m.%Y"))
            bot.send_message(message.chat.id, "Данные успешно обновлены!", reply_markup=main_menu_markup())
        else:
            sent = bot.send_message(message.chat.id, "📅 Пожалуйста, напиши дату рождения в формате dd.mm.yyyy.")
            bot.register_next_step_handler(sent, update_profile, "birth_date")



# Отчеты
def update_morning_plan(message, new=False):
    time_str, time_obj_str = check_date_in_message(message.text)
    if time_obj_str:
        time_obj = datetime.datetime.strptime(
            time_obj_str, "%Y-%m-%d %H:%M:%S")
        user_timezone = bd.get_timezone_with_user_id(message.chat.id)
        server_timezone = config.TIMEZONE
        converted_time = convert_timezone(
            time_obj_str, user_timezone, server_timezone)
        bd.update_user_time_task_1(message.chat.id, converted_time)

        if bd.get_user(message.chat.id)[7] is None:
            new = True

        if new == False:
            bot.send_message(
                message.chat.id, f"☕️ Договорились! Я буду отправлять твой ежедневный список задач в {time_obj.strftime('%H:%M')}.")
        else:
            sent = bot.send_message(
                message.chat.id, "🍾 И последнее! Когда ты хочешь получать ежедневный отчет о проделанной работе за день? (например 21:00)")
            bot.register_next_step_handler(sent, update_evening_report, True)
    else:
        if new:
            sent = bot.send_message(
                message.chat.id, "Не удалось найти время в вашем сообщении. Пожалуйста, введите время в формате HH:MM")
            bot.register_next_step_handler(sent, update_morning_plan, True)
        else:
            sent = bot.send_message(
                message.chat.id, "Не удалось найти время в вашем сообщении. Пожалуйста, введите время в формате HH:MM")
            bot.register_next_step_handler(sent, update_morning_plan)


def update_evening_report(message, new=False):
    time_str, time_obj_str = check_date_in_message(message.text)
    if time_obj_str:
        time_obj = datetime.datetime.strptime(
            time_obj_str, "%Y-%m-%d %H:%M:%S")
        user_timezone = bd.get_timezone_with_user_id(message.chat.id)
        server_timezone = config.TIMEZONE
        converted_time = convert_timezone(
            time_obj_str, user_timezone, server_timezone)
        bd.update_user_time_task_2(message.chat.id, converted_time)
        if new == False:
            bot.send_message(
                message.chat.id, f"🍾 Хороший план! Теперь я буду отправлять отчет о выполненных задачах в {time_obj.strftime('%H:%M')}.")
        else:
            bot.send_message(
                message.chat.id, "💫 Отлично! Теперь я полностью готов к работе!")
            bot.send_message(chat_id=message.chat.id,
                             text=f"<strong>🎮 Гайд по работе с Workie Bot</strong>\n"
                                    "1. Чтобы поставить задачу себе, просто напиши <strong>текст + дата + время</strong>.\n"
                                    "<em>Например: Сделать презентацию 23 июня 15:00;</em>\n"
                                    "2. Чтобы поставить задачу коллеге, напиши <strong>@никнейм + текст + дата + время</strong>.\n"
                                    "<em>Например: @xxx провести встречу завтра 13:45;</em>\n"
                                    "3. Для удобства используй слова \"сегодня\", \"завтра\", \"послезавтра\" или конкретный день недели;\n"
                                    "4. Чтобы создать повторяющуюся задачу, напиши <strong>текст + \"каждую неделю/месяц/среду\" + время</strong>.\n"
                                    "<em>Например: Сделать платеж каждый месяц 12:30;</em>\n"
                                    f"5. Свои идеи и предложения отправляйте сюда: {config.NAME_SECOND_BOT}.\n\n"
                                    "Спасибо, что вы с Workie Bot!",
                             parse_mode='HTML',
                             reply_markup=main_menu_markup())
    else:
        if new:
            sent = bot.send_message(
                message.chat.id, "Не удалось найти время в вашем сообщении. Пожалуйста, введите время в формате HH:MM")
            bot.register_next_step_handler(sent, update_evening_report, True)
        else:
            sent = bot.send_message(
                message.chat.id, "Не удалось найти время в вашем сообщении. Пожалуйста, введите время в формате HH:MM")
            bot.register_next_step_handler(sent, update_evening_report)


# часовой пояс
@bot.message_handler(func=lambda message: message.text == 'Сменить временную зону')
def handle_change_timezone(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    location_button = types.InlineKeyboardButton(
        "Отправить геопозицию 🌎", callback_data="send_location")
    manual_input_button = types.InlineKeyboardButton(
        "Настроить вручную ✍️", callback_data="input_city")
    markup.add(location_button, manual_input_button)

    bot.send_message(
        message.chat.id, "Пожалуйста, отправьте свою геопозицию.", reply_markup=markup)


@bot.message_handler(content_types=["location"])
def location(message):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(
        lat=message.location.latitude, lng=message.location.longitude)
    bd.update_timezone(message.chat.id, timezone_str)

    if bd.get_user(message.chat.id)[6] is None:
        a = telebot.types.ReplyKeyboardRemove()

        timezone_info = pytz.timezone(timezone_str)
        timezone_name = timezone_info.zone
        utc_offset = datetime.datetime.now(timezone_info).strftime('%z')
        utc_offset = str(utc_offset)[0] + str(int(utc_offset[1:3]))

        bot.send_message(message.chat.id, f"Часовой пояс установлен: {timezone_name} (UTC{str(utc_offset)})", reply_markup=a)

        sent = bot.send_message(
            message.chat.id, "☕️ Теперь напиши время когда ты хочешь получать список  задач на день (например 12:00).")
        bot.register_next_step_handler(sent, update_morning_plan, True)
    else:
        timezone_info = pytz.timezone(timezone_str)
        timezone_name = timezone_info.zone
        utc_offset = datetime.datetime.now(timezone_info).strftime('%z')
        utc_offset = str(utc_offset)[0] + str(int(utc_offset[1:3]))

        bot.send_message(message.chat.id, f"Часовой пояс установлен: {timezone_name} (UTC{str(utc_offset)})", reply_markup=main_menu_markup())


# Справка

def show_birthdays(user_id, page=0):
    import bd
    colleague_ids = bd.get_colleagues_list(user_id)  # Get the list of colleague IDs

    birthdays = []  # We'll store colleague birthdays here

    for cid in colleague_ids:
        # Skip the current user
        if cid == user_id:
            continue

        user_data = bd.get_user(cid)
        if user_data and user_data[4]:  # Check if user and birth_date exists
            birthdays.append(user_data)

    # Sort birthdays using the helper function
    birthdays = sorted(birthdays, key=lambda x: get_next_birthday(datetime.datetime.strptime(x[4], "%d.%m.%Y")))

    if not birthdays:
        bot.send_message(user_id, "Дни рождения не найдены")
    else:
        pages = math.ceil(len(birthdays) / TASKS_PER_PAGE)
        message = "🎂 Дни рождения\n\n"
        for idx, bd in enumerate(birthdays[page*TASKS_PER_PAGE:(page+1)*TASKS_PER_PAGE]):
            birth_date = datetime.datetime.strptime(bd[4], "%d.%m.%Y")  # Convert string to datetime object
            mon = birth_date.strftime('%B')
            months = {
                "January": "января", "February": "февраля", "March": "марта", "April": "апреля",
                "May": "мая", "June": "июня", "July": "июля", "August": "августа",
                "September": "сентября", "October": "октября", "November": "ноября", "December": "декабря"
            }
            for eng, rus in months.items():
                mon = mon.replace(eng, rus)

            today = datetime.datetime.now()
            age = today.year - birth_date.year

            # Check if birthday has passed this year and adjust age
            if (today.month, today.day) > (birth_date.month, birth_date.day):
                age += 1
            
            if bd[3]:
                message += f"{bd[2]} {bd[3]}: <strong>{birth_date.day} {mon} {birth_date.year} ({age}) </strong>\n\n"
            else:
                message += f"{bd[2]}: <strong>{birth_date.day} {mon} {birth_date.year} ({age}) </strong>\n\n"


        if len(birthdays) > TASKS_PER_PAGE:
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = []
            if page > 0:
                buttons.append(types.InlineKeyboardButton(
                    "<", callback_data=f'viewbirthdays_{user_id}_{page-1}'))
            if page < pages - 1:
                buttons.append(types.InlineKeyboardButton(
                    ">", callback_data=f'viewbirthdays_{user_id}_{page+1}'))
            markup.add(*buttons)
            bot.send_message(user_id, message, reply_markup=markup, parse_mode='HTML')
        else:
            bot.send_message(user_id, message, parse_mode='HTML')


def polling():
    while True:
        try:
            bd.create_db()
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            log_to_file(f"Ошибка: {e}. Перезапуск...")
            continue


def send_task_notification():
    while True:
        try:
            tasks = bd.get_due_tasks()

            messages_to_remove_markup = []
            if not tasks:
                log_to_file("send_task_notification: Нет задач")
            for task in tasks:
                task_id, user_id, task_text, deadline, _, _, task_timezone, _, _ = task

                # Convert the deadline from the task's timezone to server's timezone
                server_timezone = config.TIMEZONE
                converted_deadline = convert_timezone(deadline, task_timezone, server_timezone)
                converted_time_datetime = datetime.datetime.strptime(converted_deadline, "%Y-%m-%d %H:%M:%S")

                now = datetime.datetime.now()

                # Check if the current time is within the required range
                log_to_file("send_task_notification: ", converted_time_datetime, "------------", now, "------------", converted_time_datetime <= now )
                if converted_time_datetime <= now :
                    log_to_file(f"send_task_notification: {task}")
                    task_id, user_id, task_text, deadline, _, _, task_timezone, _, _ = task

                    markup = types.InlineKeyboardMarkup(row_width=2)
                    one_hour = types.InlineKeyboardButton(
                        "1 час", callback_data=f'deadline|1hour|{task_id}')
                    three_hours = types.InlineKeyboardButton(
                        "3 часа", callback_data=f'deadline|3hours|{task_id}')
                    tomorrow = types.InlineKeyboardButton(
                        "Завтра", callback_data=f'deadline|tmrw|{task_id}')
                    other_time = types.InlineKeyboardButton(
                        "Другое время", callback_data=f'deadline|other|{task_id}')
                    done = types.InlineKeyboardButton(
                        "✅ Готово", callback_data=f'deadline|done|{task_id}')
                    markup.add(one_hour, three_hours, tomorrow, other_time, done)

                    msg = bot.send_message(user_id, f"🔥 {task_text}", reply_markup=markup)
                    messages_to_remove_markup.append((user_id, msg.message_id))

            time.sleep(900)

            # remove buttons from the message
            new_markup = types.InlineKeyboardMarkup()  # create empty markup
            for user_id, message_id in messages_to_remove_markup:
                try:
                    bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=new_markup)
                except Exception as e:
                    log_to_file(f"Couldn't update message {message_id} for user {user_id}. Error: {e}")
        except Exception as e:
            continue


def create_new_recurring_task():
    while True:
        tasks = bd.get_done_recurring_tasks()
        for task in tasks:
            log_to_file(task[0])
            task_id, user_id, task_text, deadline, _, file_id, timezone, user_id_added, new_date = task

            if new_date.split()[0] == "на":
                continue

            new_task = bd.Task(user_id, task_text)
            new_task.set_file_id(file_id)
            new_task.set_timezone(timezone)
            new_task.set_user_id_added(user_id_added)
            new_task.set_new_date(new_date)

            if new_date.lower().startswith('каждый день'):
                new_deadline = datetime.datetime.strptime(
                    deadline, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)
            elif new_date.lower().startswith('каждую неделю'):
                new_deadline = datetime.datetime.strptime(
                    deadline, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(weeks=1)
            elif new_date.lower().startswith('каждый месяц'):
                new_deadline = datetime.datetime.strptime(
                    deadline, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(weeks=4)
            else:
                for i in range(2, 31):
                    if new_date.lower().startswith(f'каждые {i} дня') or new_date.lower().startswith(f'каждые {i} дней'):
                        new_deadline = datetime.datetime.strptime(
                            deadline, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=i)
                        break
                else:
                    # If it's a day of the week, find out the next date this day will occur
                    days = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
                    for i, day in enumerate(days):
                        if new_date.lower().startswith('каждый ' + day):
                            today = datetime.datetime.today()
                            next_day = today + datetime.timedelta((i - today.weekday() + 7) % 7)
                            new_deadline = datetime.datetime.combine(next_day, datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S").time())
                        elif new_date.lower().startswith('каждую ' + day):
                            today = datetime.datetime.today()
                            next_day = today + datetime.timedelta((i - today.weekday() + 7) % 7)
                            new_deadline = datetime.datetime.combine(next_day, datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S").time())

            new_task.set_deadline(new_deadline.strftime("%Y-%m-%d %H:%M:%S"))
            bd.add_task(new_task)
            bd.delete_task(task_id)
        time.sleep(20)

def send_daily_task_summary():
    while True:
        # предположим, что эта функция возвращает всех пользователей из вашей базы данных
        users = bd.get_all_users()
        for user in users:
            # предположим, что get_all_users возвращает пользователя с полем time_task_2
            user_id, _, _, _, _, timezone, time_taks_1, time_taks_2 = user

            try:

                server_timezone = config.TIMEZONE
                converted_time_datetime = datetime.datetime.strptime(time_taks_1, "%Y-%m-%d %H:%M:%S")
                now = datetime.datetime.now()

                log_to_file('send_daily_task_summary (mor): ',converted_time_datetime - datetime.timedelta(seconds=25), "------------", now, "------------", converted_time_datetime + datetime.timedelta(seconds=25))
                log_to_file('send_daily_task_summary (mor): ', converted_time_datetime - datetime.timedelta(seconds=25) <= now <= converted_time_datetime + datetime.timedelta(seconds=25))
                if converted_time_datetime - datetime.timedelta(seconds=25) <= now <= converted_time_datetime + datetime.timedelta(seconds=25):
                    view_tasks(None, status='pending', id=user_id)

                    ### оповещения о днях рождения
                    colleague_ids = bd.get_colleagues_list(user_id) # Get the list of colleague IDs
                    today = datetime.datetime.now()

                    for cid in colleague_ids:
                        user_data = bd.get_user(cid)
                        if user_data and user_data[4]: # Check if user and birth_date exists
                            birth_date = datetime.datetime.strptime(user_data[4], "%Y-%m-%d")
                            # Check if today is the birthday
                            if birth_date.day == today.day and birth_date.month == today.month:
                                age = today.year - birth_date.year
                                if user_data[3]:
                                    bot.send_message(user_id, f"Сегодня у {user_data[2]} {user_data[3]} день рождения! Исполняется {age} лет.")
                                else:
                                    bot.send_message(user_id, f"Сегодня у {user_data[2]} день рождения! Исполняется {age} лет.")
            except Exception as e:
                log_to_file("Утрений план: ERROR: send_daily_task_summary." + str(e))
                pass

            try:
                server_timezone = config.TIMEZONE
                converted_time_datetime = datetime.datetime.strptime(time_taks_2, "%Y-%m-%d %H:%M:%S")

                now = datetime.datetime.now()

                if (converted_time_datetime - datetime.timedelta(seconds=25)).time() <= now.time() <= (converted_time_datetime + datetime.timedelta(seconds=25)).time():
                    task_done(user_id, page=0)
            except Exception as e:
                log_to_file("Вечерений план: ERROR: send_daily_task_summary." + str(e))
                pass
        time.sleep(60)

def send_task_notification_60s():
    def remove_markup_after_15(messages_to_remove_markup):
        time.sleep(900)
        new_markup = types.InlineKeyboardMarkup()  # create empty markup
        for user_id, message_id in messages_to_remove_markup:
            try:
                bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=new_markup)
            except Exception as e:
                log_to_file(f"Couldn't update message {message_id} for user {user_id}. Error: {e}")

    messages_to_remove_markup = []

    while True:
        tasks = bd.get_all_tasks()
        for task in tasks:
            task_id, user_id, task_text, deadline, _, _, task_timezone, _, _ = task

            # Convert the deadline from the task's timezone to server's timezone
            server_timezone = config.TIMEZONE
            converted_deadline = convert_timezone(deadline, task_timezone, server_timezone)
            converted_time_datetime = datetime.datetime.strptime(converted_deadline, "%Y-%m-%d %H:%M:%S")

            now = datetime.datetime.now()

            # Check if the current time is within the required range
            log_to_file("send_task_notification_60s: ", converted_time_datetime - datetime.timedelta(seconds=25), "------------", now, "------------", converted_time_datetime + datetime.timedelta(seconds=25), '------------', converted_time_datetime - datetime.timedelta(seconds=25) <= now <= converted_time_datetime + datetime.timedelta(seconds=25))
            if converted_time_datetime - datetime.timedelta(seconds=25) <= now <= converted_time_datetime + datetime.timedelta(seconds=25):
                markup = types.InlineKeyboardMarkup(row_width=2)
                one_hour = types.InlineKeyboardButton("1 час", callback_data=f'deadline|1hour|{task_id}')
                three_hours = types.InlineKeyboardButton("3 часа", callback_data=f'deadline|3hours|{task_id}')
                tomorrow = types.InlineKeyboardButton("Завтра", callback_data=f'deadline|tmrw|{task_id}')
                other_time = types.InlineKeyboardButton("Другое время", callback_data=f'deadline|other|{task_id}')
                done = types.InlineKeyboardButton("✅ Готово", callback_data=f'deadline|done|{task_id}')
                markup.add(one_hour, three_hours, tomorrow, other_time, done)

                msg = bot.send_message(user_id, f"🔥 {task_text}", reply_markup=markup)
                

                messages_to_remove_markup.append((user_id, msg.message_id))

        if messages_to_remove_markup:
            log_to_file("send_task_notification_60s: ", ' '.join(messages_to_remove_markup))
            thread = threading.Thread(target=remove_markup_after_15, args=(messages_to_remove_markup,))
            thread.start()

        # Sleep for 60 seconds (1 minute) before checking again
        time.sleep(60)


if __name__ == '__main__':
    thread1 = threading.Thread(target=polling)
    thread2 = threading.Thread(target=send_task_notification)
    thread3 = threading.Thread(target=create_new_recurring_task)
    thread4 = threading.Thread(target=send_daily_task_summary)
    thread5 = threading.Thread(target=send_task_notification_60s)

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()

    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    thread5.join()
