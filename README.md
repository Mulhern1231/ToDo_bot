# ToDo_bot
ToDo_bot - это бот для Telegram, предназначенный для создания и отслеживания задач как для себя, так и для других пользователей. Он предоставляет удобный интерфейс для организации своих задач и совместной работы.

## Установка:

Следуйте этим шагам, чтобы установить и запустить ToDo_bot:

1) Клонирование репозитория с GitHub:
```sh
git clone https://github.com/Mulhern1231/ToDo_bot.git
```
2) Установка необходимых библиотек:
```sh
pip install -r requirements.txt
```
3) Запуск бота:
```sh
python main.py
```
## Обратите внимание:
Если бот запускается впервые, он может выдать ошибку о том, что отсутствует база данных. Это нормально. Просто перезапустите бота, и он создаст необходимую базу данных.

# Настройка:

Для настройки бота вам нужно будет изменить некоторые значения в файле `config.py`. Вот его содержимое и описание каждой переменной:

```python
# Название второго бота для помощи и предложений 
NAME_SECOND_BOT = '@ToDoTasks_new_bot_HELP'
# Название самого бота
NAME = "@ToDoTasks_new_bot"
# Заголовок бота
TITLE = "ToDoTasks"

# Настройки
# Имя файла базы данных
BDNAME = "tasks.db"
# Часовой пояс
TIMEZONE = "Europe/Moscow"
# Токен бота, полученный от @BotFather
TOKEN = "5615427718:AAH7ORN6QT1hY0s315BrPBMhAiPT7_WAnpg"

# Количество задач на одной странице
TASKS_PAGE = 10
```

## Описание переменных:

- `NAME_SECOND_BOT` - Это имя второго бота, который используется для помощи и предложений. Замените его на имя вашего бота.
- `NAME` - Имя вашего бота. Замените его на имя вашего бота.
- `TITLE` - Заголовок вашего бота.
- `BDNAME` - Это имя файла вашей базы данных. Вам не нужно его менять, если вы не хотите использовать другое имя для базы данных.
- `TIMEZONE` - Часовой пояс, в котором работает ваш бот. Замените его на ваш часовой пояс, если он отличается от указанного.
- `TOKEN` - Это токен вашего бота, который вы получите от @BotFather после создания бота.
- `TASKS_PAGE` - Количество задач, которые будут отображаться на одной странице. Вы можете изменить это число в зависимости от ваших предпочтений.
