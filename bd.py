import sqlite3
import datetime
import config

import pytz
from pytz import timezone


def convert_timezone(time_first: str, timezone_first: str, timezone_second: str) -> str:
    datetime_first = datetime.strptime(time_first, "%Y-%m-%d %H:%M:%S")
    datetime_first = pytz.timezone(timezone_first).localize(datetime_first)
    datetime_second = datetime_first.astimezone(pytz.timezone(timezone_second))
    time_second = datetime_second.strftime("%Y-%m-%d %H:%M:%S")
    return time_second

bd_name = config.BDNAME

class Task:
    def __init__(self, user_id, text):
        self.user_id = user_id
        self.text = text
        self.deadline = None
        self.status = 'pending'  # pending, done, overdue
        self.file_id = None  # to store file_id
        self.timezone = None 
        self.user_id_added = None 
        self.new_date = None

    def set_deadline(self, date):
        self.deadline = date

    def set_file_id(self, file_id):
        self.file_id = file_id

    def set_timezone(self, timezone):
        self.timezone = timezone

    def set_status(self, status):
        self.status = status
    
    def set_user_id_added(self, user_id):
        self.user_id_added = user_id
    
    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_new_date(self, new_date):
        self.new_date = new_date
    
    def set_text(self, text):
        self.text = text

def add_task(task):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (user_id, task_text, deadline, status, file_id, timezone, user_id_added, new_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (task.user_id, task.text, task.deadline, task.status, task.file_id, task.timezone, task.user_id_added, task.new_date))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def delete_task(task_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def create_db():
    try:
        conn = sqlite3.connect(bd_name)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users
                        (user_id integer, username text, first_name text, last_name text, birth_date text, timezone text,
                        time_taks_1 text, time_task_2 text)
                    """)
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS tasks
                    (id integer primary key autoincrement, user_id integer, task_text text,
                    deadline text, status boolean, file_id text, timezone text, user_id_added integer, new_date text)
                """)

        cursor.close()
        conn.commit()
        conn.close()
    except:
        pass

def add_user(user_id, username, first_name, last_name, birth_date=None):
    conn = sqlite3.connect(bd_name)  
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if data is None:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)", 
                       (user_id, username, first_name, last_name, birth_date))
    else:
        cursor.execute("UPDATE users SET username=?, first_name=?, last_name=?, birth_date=? WHERE user_id=?",
                       (username, first_name, last_name, birth_date, user_id))

    conn.commit()
    cursor.close()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(bd_name)  # Замените 'my_database.db' на имя вашей базы данных
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")  # Замените 'users' на имя вашей таблицы пользователей
    users = cursor.fetchall()

    conn.close()
    return users



def get_user_id(username):
    conn = sqlite3.connect(bd_name)  
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE LOWER(username)=?", (username.lower(),))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if data:
        return data[0]
    else:
        return None



def get_tasks(user_id, status):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    current_time = datetime.datetime.now()
    if status == "overdue":
        cursor.execute('SELECT * FROM tasks WHERE user_id = ? AND status = ? AND deadline < ? ORDER BY datetime(deadline) ASC', (user_id, 'pending', current_time))
    else:
        cursor.execute('SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY datetime(deadline) ASC', (user_id, status))
    rows = cursor.fetchall()
    tasks = rows
    conn.close()
    return tasks


def get_all_tasks():
    conn = sqlite3.connect(bd_name)  # Замените 'my_database.db' на имя вашей базы данных
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")  # Замените 'users' на имя вашей таблицы пользователей
    users = cursor.fetchall()

    conn.close()
    return users

def get_task(task_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    task_data = cursor.fetchone()
    conn.close()
    return task_data

def edit_task(task_id, new_deadline):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET deadline = ? WHERE id = ?', (new_deadline, task_id))
    conn.commit()
    conn.close()

def edit_task_text(task_id, new_text):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET task_text = ? WHERE id = ?', (new_text, task_id))
    conn.commit()
    conn.close()

def edit_new_date(task_id, new_date):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET new_date = ? WHERE id = ?', (new_date, task_id))
    conn.commit()
    conn.close()

def edit_task_timezone(task_id, new_timezone):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET timezone = ? WHERE id = ?', (new_timezone, task_id))
    conn.commit()
    conn.close()

def set_task_done(task_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status = "done" WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def get_timezone_with_user_id(user_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
    user_timezone = cursor.fetchone()[0]
    conn.close()
    return user_timezone

def update_timezone(user_id, timezone):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET timezone = ? WHERE user_id = ?', (timezone, user_id))
    conn.commit()
    conn.close()

def get_local_time(user_id):
    conn = sqlite3.connect(bd_name)  
    cursor = conn.cursor()
    cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
    user_timezone = cursor.fetchone()[0]
    if user_timezone:
        tz = timezone(user_timezone)
    else:
        tz = timezone('UTC')
    local_time = datetime.now(tz)
    return local_time

def is_user_in_db(user_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def set_task_status(task_id, status):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    conn.commit()
    conn.close()

def set_task_user_id(task_id, user_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET user_id = ? WHERE id = ?', (user_id, task_id))
    conn.commit()
    conn.close()

def get_tasks_by_user_id_added(user_id_added):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id_added = ?", (user_id_added,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_user(user_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def get_colleagues(user_id, page=0, items_per_page=10):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM tasks WHERE user_id_added = ?", (user_id,))
    all_colleagues = [item[0] for item in cursor.fetchall()]
    colleagues = all_colleagues[page*items_per_page:(page+1)*items_per_page]
    cursor.close()
    conn.close()
    return colleagues, len(all_colleagues)


def get_colleagues_list(user_id):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    
    # Get colleagues who you gave tasks to
    cursor.execute("SELECT DISTINCT user_id FROM tasks WHERE user_id_added = ?", (user_id,))
    colleagues_you_gave_tasks_to = [i[0] for i in cursor.fetchall()]

    # Get colleagues who gave you tasks
    cursor.execute("SELECT DISTINCT user_id_added FROM tasks WHERE user_id = ?", (user_id,))
    colleagues_who_gave_you_tasks = [i[0] for i in cursor.fetchall()]

    cursor.close()
    conn.close()
    
    # Combine both lists and remove duplicates by converting it to a set, then back to a list
    all_colleagues = list(set(colleagues_you_gave_tasks_to + colleagues_who_gave_you_tasks))
    
    return all_colleagues

def get_tasks_by_status(user_id, status, page=0, tasks_per_page=config.TASKS_PAGE):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=? AND status=? ORDER BY datetime(deadline) ASC", (user_id, status))
    all_tasks = cursor.fetchall()
    tasks = all_tasks[page*tasks_per_page:(page+1)*tasks_per_page]
    cursor.close()
    conn.close()
    return tasks, len(all_tasks)


def get_tasks_by_status_and_user_added(user_id, status, user_id_added, page=0, tasks_per_page=config.TASKS_PAGE):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id=? AND status=? AND user_id_added=? ORDER BY datetime(deadline) ASC", (user_id, status, user_id_added))
    all_tasks = cursor.fetchall()
    tasks = all_tasks[page * tasks_per_page:(page + 1) * tasks_per_page]
    cursor.close()
    conn.close()
    return tasks, len(all_tasks)


def get_due_tasks():
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('SELECT * FROM tasks WHERE deadline <= ? AND status != "done"', (now,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_done_recurring_tasks():
    try:
        conn = sqlite3.connect(bd_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE new_date IS NOT NULL AND status="done"')
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    except:
        return None
    
def update_user_first_name(user_id, first_name):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
    conn.commit()
    conn.close()

def update_user_last_name(user_id, last_name):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_name = ? WHERE user_id = ?", (last_name, user_id))
    conn.commit()
    conn.close()

def update_user_nickname(user_id, nickname):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (nickname, user_id))
    conn.commit()
    conn.close()

def update_user_birth_date(user_id, birth_date):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET birth_date = ? WHERE user_id = ?", (birth_date, user_id))
    conn.commit()
    conn.close()


def update_user_time_task_1(user_id, time):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET time_taks_1 = ? WHERE user_id = ?", (time, user_id))
    conn.commit()
    conn.close()

def update_user_time_task_2(user_id, time):
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET time_task_2 = ? WHERE user_id = ?", (time, user_id))
    conn.commit()
    conn.close()

def get_completed_tasks(user_id):
    # Get current date and format it as a string
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()

    # Include date in SQL query
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND status = 'done' AND date(deadline) = ?", (user_id, today))
    completed_tasks = cursor.fetchall()

    conn.close()
    return completed_tasks

def get_completed_tasks_all():
    conn = sqlite3.connect(bd_name)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks")
    completed_tasks = cursor.fetchall()

    conn.close()
    return completed_tasks
