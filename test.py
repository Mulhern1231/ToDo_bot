import datetime
from datetime import timedelta

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
    


new_deadline = datetime.datetime.now() + datetime.timedelta(hours=20)
deadline = datetime.datetime.now()
print(calculate_time_diff(deadline, new_deadline))