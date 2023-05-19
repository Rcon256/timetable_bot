import telebot
from threading import Thread
import schedule
import time
import datetime
from datetime import date, timedelta
import requests
import json
import configparser
from telebot import types
import logging
logging.basicConfig(filename='log_bot.log', encoding='utf-8', level=logging.INFO)
# create logger
logger = logging.getLogger('log_bot')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
# ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

config = configparser.ConfigParser()
config.sections()
config.read('settings.ini')
HOST = config['MAIN']['HOST'];
API = config['MAIN']['API'];
wDay = ['Понедельник',
        'Вторник',
        'Среда',
        'Четверг',
        'Пятница',
        'Суббота',
        'Воскресенье']

bot = telebot.TeleBot('')
klasses = []
teachers = []
cabs = []

configCache = configparser.ConfigParser()
configCache.read('cache.ini')
def getActiveKlasses():
    myresult = requests.get(f"http://{str(HOST)}/api/getactiveklasses")
    myresult = json.loads(myresult.text)
    global klasses
    klasses = myresult
    logger.info(f"{str(datetime.datetime.now())} - Классы загружены")
def getActiveTeachers():
    myresult = requests.get(f"http://{str(HOST)}/api/getactiveteachers")
    myresult = json.loads(myresult.text)
    global teachers
    teachers = myresult
    logger.info(f"{str(datetime.datetime.now())} - Учителя загружены")
def getActiveCabs():
    myresult = requests.get(f"http://{str(HOST)}/api/getactivecabs")
    myresult = json.loads(myresult.text)
    global cabs
    cabs = myresult
    logger.info(f"{str(datetime.datetime.now())} - Кабинеты загружены")

def send_repls():
    while(True):
        myresult = requests.get(f"http://{str(HOST)}/api/getsend")
        myresult = json.loads(myresult.text)
        logger.info(f"{str(datetime.datetime.now())} - Проверка наличия замещений")
        # print(myresult)
        for x in myresult:
            logger.info(f"{str(datetime.datetime.now())} - Замещения найдены")
            if (x['send']==0):
                myresult2 = requests.get(f"http://{str(HOST)}/api/getsubs?teacher="+str('teacher')+"&klass="+str('klass'))
                myresult2 = json.loads(myresult2.text)
                # print(myresult2)
                for y in myresult2:
                    dt = str(x['dt']).split('-')
                    day = wDay[int(datetime.date(int(dt[0]), int(dt[1]), int(dt[2])).weekday())]
                    if (x['comment'] != ' '):
                        print(x['comment'])
                        comment = f"💬Комментарий: <b>{x['comment']}</b>"
                    else:
                        comment = ""
                    bot.send_message(y['chat_id'], "🔴ЗАМЕЩЕНИЕ\n"+
                                           f"🗓Дата: <b>{str(datetime.datetime.strptime(x['dt'], '%Y-%m-%d').date().strftime('%d.%m.%Y'))}</b>\n"+
                                            "📌День недели: "+day+"\n"+
                                                                "👉№Урока: "+str(x['lesson'])+"\n"+
                                                                                      "🔬Предмет: "+x['subj']+"\n"+
                                                                                     "👩‍🏫Преподаватель: "+x['fio']+"\n"+
                                                                                                                "👥Класс: "+x['kl_name']+"\n"+
                                     "🏫Кабинет: " + x['cab_name'] + "\n" + comment + "\n\n", parse_mode="HTML")
                requests.get(f"http://{str(HOST)}/api/setsend?token={API}&r_id={str(x['r_id'])}")
                logger.info(f"{str(datetime.datetime.now())} - Информация о замещении в классе {x['kl_name']} у преподавателя {x['fio']} отправлена успешно")
        time.sleep(60)

# Создаём новый поток
th1 = Thread(target=send_repls, args=())
# И запускаем его
th1.start()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📚 Расписание")
    btn2 = types.KeyboardButton("🔔 Оповещания")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=markup)
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} в главном меню")
@bot.message_handler(content_types=['text'])
def getText(message):
    if (message.text == '🔔 Оповещания'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Оповещения'")
        subs = requests.get(f"http://{str(HOST)}/api/getsubs")
        subs = json.loads(subs.text)
        SubThere = False
        btn1 = types.KeyboardButton("")
        btn2 = types.KeyboardButton("НАЗАД")
        text = ""
        for i in subs:
            if (i['chat_id']==message.chat.id):
                SubThere = True
        if (SubThere):
            text = 'Вы можете отписаться от уведомлений'
            btn1 = types.KeyboardButton("Отписаться")
        else:
            text = 'Подписка будет выполнена на уведомления по критерию последней загрузки расписания, если таковая была.'
            btn1 = types.KeyboardButton("Подписаться")
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, text, reply_markup=markup)
    if (message.text == 'Отписаться'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Отписаться'")
        subs = requests.get(f"http://{str(HOST)}/api/subs/unsubscribe?token={API}&chatid={message.chat.id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("📚 Расписание")
        btn2 = types.KeyboardButton("🔔 Оповещания")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Отписка выполнена", reply_markup=markup)
    if (message.text == 'Подписаться'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Подписаться'")
        try:
            typeRasp = configCache.get('typeRasp', str(message.chat.id))
            dataRasp = configCache.get('dataRasp', str(message.chat.id))
            if (typeRasp == 'cab'):
                bot.send_message(message.chat.id, 'Подписка на расписание кабинета невозможна!')
                return

        except Exception as e:
            bot.send_message(message.chat.id,
                     'Подписка невозможна! Проверьте правильность ввода класс, аудитории или преподавателя.')
        subs = ''
        if (typeRasp == 'klass'):
            subs = requests.get(f"http://{str(HOST)}/api/subs/subscribe?token={API}&chatid={message.chat.id}&klass={dataRasp}&teacher=0")
        elif(typeRasp == 'teacher'):
            subs = requests.get(
                f"http://{str(HOST)}/api/subs/subscribe?token={API}&chatid={message.chat.id}&teacher={dataRasp}&klass=0")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("📚 Расписание")
        btn2 = types.KeyboardButton("🔔 Оповещания")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Подписка выполнена", reply_markup=markup)
    if (message.text == '📚 Расписание'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Расписание'")
        # markup = types.ReplyKeyboardMarkupMarkup(row_width=2)
        btn1 = types.KeyboardButton("Сегодня")
        btn2 = types.KeyboardButton("Завтра")
        btn3 = types.KeyboardButton("Неделя")
        btn4 = types.KeyboardButton("Класс")
        btn5 = types.KeyboardButton("Аудитория")
        btn6 = types.KeyboardButton("Преподаватель")
        btn7 = types.KeyboardButton("НАЗАД")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True).row(
            btn1, btn2, btn3
        ).row(btn7, btn4, btn5, btn6)
        bot.send_message(message.chat.id, "Меню расписания", reply_markup=markup)
    if (message.text == 'Класс'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Класс'")
        msg = bot.send_message(message.chat.id, "Введите класс")
        bot.register_next_step_handler(msg, setKlass)
    if (message.text == 'Преподаватель'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Преподаватель'")
        msg = bot.send_message(message.chat.id, "Введите ФИО преподавателя")
        bot.register_next_step_handler(msg, setTeacher)
    if (message.text == 'Аудитория'):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Аудитория'")
        msg = bot.send_message(message.chat.id, "Введите №Кабинета")
        bot.register_next_step_handler(msg, setCab)
    if (message.text == "Сегодня"):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Сегодея'")
        try:
            typeRasp = configCache.get('typeRasp', str(message.chat.id))
            dataRasp = configCache.get('dataRasp', str(message.chat.id))
            getRaspByKlassDay(message, dataRasp, 0, typeRasp)
        except Exception as e:
            bot.send_message(message.chat.id, 'Расписание не найдено! Проверьте правильность ввода класс, аудитории или преподавателя.')
    if (message.text == "Завтра"):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Завтра'")
        try:
            typeRasp = configCache.get('typeRasp', str(message.chat.id))
            dataRasp = configCache.get('dataRasp', str(message.chat.id))
            getRaspByKlassDay(message, dataRasp, 1, typeRasp)
        except Exception as e:
            bot.send_message(message.chat.id, 'Расписание не найдено! Проверьте правильность ввода класс, аудитории или преподавателя.')
    if (message.text == "Неделя"):
        logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл 'Неделя'")
        try:
            typeRasp = configCache.get('typeRasp', str(message.chat.id))
            dataRasp = configCache.get('dataRasp', str(message.chat.id))
            getRaspByKlassWeek(message, dataRasp, typeRasp)
        except Exception as e:
            bot.send_message(message.chat.id, 'Расписание не найдено! Проверьте правильность ввода класс, аудитории или преподавателя.')
    if (message.text == "НАЗАД"):
        start(message)

def setKlass(message):
    kl_id = -1
    for i in klasses:
        if (str.casefold(message.text) == str.casefold(i['kl_name'])):
            kl_id = i['id']
    if (kl_id == -1):
        bot.send_message(message.chat.id, 'Класс не найден!')
        return
    configCache.set('typeRasp', str(message.chat.id), 'klass');
    configCache.set('dataRasp', str(message.chat.id), str(kl_id))
    with open('cache.ini', "w") as config_file:
        configCache.write(config_file)
    bot.send_message(message.chat.id, 'Принято!')
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл класс {message.text}")
def setTeacher(message):
    t_id = -1
    for i in teachers:
        if (str.casefold(message.text) == str.casefold(i['fio'])):
            t_id = i['id']
    if (t_id == -1):
        bot.send_message(message.chat.id, 'Преподаватель не найден!')
        return
    configCache.set('typeRasp', str(message.chat.id), 'teacher');
    configCache.set('dataRasp', str(message.chat.id), str(t_id))
    with open('cache.ini', "w") as config_file:
        configCache.write(config_file)
    bot.send_message(message.chat.id, 'Принято!')
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл преподавателя {message.text}")
def setCab(message):
    c_id = -1
    for i in cabs:
        if (str.casefold(message.text) == str.casefold(i['cab_name'])):
            c_id = i['id']
    if (c_id == -1):
        bot.send_message(message.chat.id, 'Кабинет не найден!')
        return
    configCache.set('typeRasp', str(message.chat.id), 'cab');
    configCache.set('dataRasp', str(message.chat.id), str(c_id))
    with open('cache.ini', "w") as config_file:
        configCache.write(config_file)
    bot.send_message(message.chat.id, 'Принято!')
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} ввёл аудиторию {message.text}")
def setTypeOfRasp(message):
    configCache.set('dataRasp', str(message.chat.id), message.text)
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} выбрал поиск по {message.text}")
def getRaspByKlassDay(message, id, tod, type):
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} вызвал поиск расписания по типу {tod}, {type}, {id}")
    dt = date.today();
    if (tod == 0):
        pass
    else:
        dt = date.today() + timedelta(days=1)
    myresult = requests.get(f"http://{HOST}/api/getraspbyday?token={API}&dt={dt}")
    myresult = json.loads(myresult.text)
    raspList = []
    for y in myresult:
        if (type=='klass'):
            if (str(y['klass']) == str(id)):
                raspList.append(y)
        elif (type=='teacher'):
            if (str(y['teacher']) == str(id)):
                raspList.append(y)
        elif (type=='cab'):
            if (str(y['cab']) == str(id)):
                raspList.append(y)
    text = ""
    if (tod == 0):
        text = "🔴РАСПИСАНИЕ НА СЕГОДНЯ\n\n"
    else:
        text = "🔴РАСПИСАНИЕ НА ЗАВТРА\n\n"
    comment = ""
    dt = ""
    for i in raspList:
        if i['grp'] == 1:
            text += "<u>ГРУППОВОЕ ЗАНЯТИЕ</u>\n"
        if i['grp'] == 2:
            text += "<u>ЗАМЕЩЕНИЕ</u>\n"
            dt = f"🗓Дата: <b>{str(datetime.datetime.strptime(i['dt'], '%Y-%m-%d').date().strftime('%d.%m.%Y'))}</b>\n"
            if (i['comment'] != ' '):
                comment = f"💬Комментарий: <b>{i['comment']}</b>"
            else:
                comment = ""
        text += dt+"👉№Урока: <b>" + str(i['lesson']) + "</b>\n" \
                                                    "🔬Предмет: <b>" + i['subj'] + "</b>\n" \
                                                                                  "👩‍🏫Преподаватель: <b>" + i[
                    'fio'] + "</b>\n" \
                             "👥Класс: <b>" + i['kl_name'] + "</b>\n" \
                                                            "🏫Кабинет: <b>" + i[
                    'cab_name'] + "</b>\n" + comment + "\n\n"
        comment = ""
        dt = ""
    if (text == "🔴РАСПИСАНИЕ НА ЗАВТРА\n\n" or text == "🔴РАСПИСАНИЕ НА СЕГОДНЯ\n\n"):
        text += "🤗 УРА! Выходной!"
    bot.send_message(message.chat.id, text, parse_mode="HTML")
def getRaspByKlassWeek(message, id, type):
    logger.info(f"{str(datetime.datetime.now())} - Пользователь {message.chat.id} вызвал поиск расписания по типу {type}, {id} на неделю")
    myresult = ''
    if (type=='klass'):
        myresult = requests.get(f"http://{str(HOST)}/getrasp?klass={id}&teacher=0&cab=0")
    elif (type=='teacher'):
        myresult = requests.get(f"http://{str(HOST)}/getrasp?klass=0&teacher={id}&cab=0")
    elif (type=='cab'):
        myresult = requests.get(f"http://{str(HOST)}/getrasp?klass=0&teacher=0&cab={id}")
    # print(myresult)
    myresult = json.loads(myresult.text)
    days = [[],[],[],[],[],[],[]]
    for i in myresult:
        if (i['day']=='Понедельник'):
            days[0].append(i)
        if (i['day']=='Вторник'):
            days[1].append(i)
        if (i['day']=='Среда'):
            days[2].append(i)
        if (i['day']=='Четверг'):
            days[3].append(i)
        if (i['day']=='Пятница'):
            days[4].append(i)
        if (i['day']=='Суббота'):
            days[5].append(i)
        if (i['day']=='Воскресенье'):
            days[6].append(i)
    text = "🔴РАСПИСАНИЕ\n\n"
    comment = ""
    dt = ""
    for day in days:
        try:
            text += f"<b><u>=={str.upper(day[0]['day'])}==</u></b>\n\n"
        except Exception as e:
            pass
        for lesson in day:
            if lesson['grp'] == 1:
                text += "<u>ГРУППОВОЕ ЗАНЯТИЕ</u>\n"
            if lesson['grp'] == 2:
                text += "<u>ЗАМЕЩЕНИЕ</u>\n"
                dt = f"🗓Дата: <b>{str(datetime.datetime.strptime(lesson['dt'], '%Y-%m-%d').date().strftime('%d.%m.%Y'))}</b>\n"
                if (lesson['comment'] != ' '):
                    comment = f"💬Комментарий: <b>{lesson['comment']}</b>"
                else:
                    comment = ""
            text += dt+"👉№Урока: <b>" + str(lesson['lesson']) + "</b>\n" \
                                                        "🔬Предмет: <b>" + lesson['subj'] + "</b>\n" \
                                                                                      "👩‍🏫Преподаватель: <b>" + lesson[
                        'fio'] + "</b>\n" \
                                 "👥Класс: <b>" + lesson['kl_name'] + "</b>\n" \
                                                                "🏫Кабинет: <b>" + lesson[
                        'cab_name'] + "</b>\n" + comment + "\n\n"
            comment = ""
            dt = ""
    bot.send_message(message.chat.id, text, parse_mode="HTML")
    # print(days)
def job():
    logger.info(f"{str(datetime.datetime.now())} - Выполнено ежедневное оповещение о расписании на следующий день")
    dt = date.today() + timedelta(days=1)
    subs = requests.get(f"http://{HOST}/api/getsubs");
    subs = json.loads(subs.text)

    for x in subs:
        raspList = []
        myresult = None
        rasp = requests.get(f'http://{HOST}/api/getraspbyday?token={API}&dt={dt}')
        if (rasp.status_code==403):
            return;
        myresult = json.loads(rasp.text)
        delNumb = []
        for i in myresult:
            if (i['grp'] == 2):
                for j in range(len(myresult)):
                    if (i['klass']==myresult[j]['klass'] and i['lesson']==myresult[j]['lesson'] and myresult[j]['grp']!=2):
                        delNumb.append(j)
        for i in delNumb:
            myresult.pop(i)
        for y in myresult:
            # print(y)
            if (x['klass']!=0 and y['klass']==x['klass']):
                raspList.append(y)
            if (x['teacher']!=0 and y['teacher']==x['teacher']):
                raspList.append(y)
        # print(raspList)

        text = "🔴РАСПИСАНИЕ НА ЗАВТРА\n\n"
        comment = ""
        dt = ""
        for i in raspList:
            if i['grp']==1:
                text+= "<u>ГРУППОВОЕ ЗАНЯТИЕ</u>\n"
            if i['grp']==2:
                text+= "<u>ЗАМЕЩЕНИЕ</u>\n"
                dt = f"🗓Дата: <b>{str(datetime.datetime.strptime(i['dt'], '%Y-%m-%d').date().strftime('%d.%m.%Y'))}</b>\n"
                if (i['comment']!= ' '):
                    comment = f"💬Комментарий: <b>{i['comment']}</b>"
                else:
                    comment = ""
            text += dt+"👉№Урока: <b>" + str(i['lesson']) + "</b>\n" \
                                    "🔬Предмет: <b>" +i['subj'] + "</b>\n" \
                                     "👩‍🏫Преподаватель: <b>" + i['fio'] + "</b>\n" \
                                                                    "👥Класс: <b>" + i['kl_name'] + "</b>\n" \
                                                                                         "🏫Кабинет: <b>" + i['cab_name'] + "</b>\n"+comment+"\n\n"
            comment = ""
            dt = ""
        if (text == "🔴РАСПИСАНИЕ НА ЗАВТРА\n\n"):
            text += "🤗 УРА! Выходной!"
        bot.send_message(x['chat_id'], text, parse_mode="HTML")

schedule.every().day.at("21:00").do(job)

def shed():
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute

getActiveKlasses()
getActiveTeachers()
getActiveCabs()
# job()
# Создаём новый поток
th2 = Thread(target=shed, args=())
# И запускаем его
th2.start()
logger.info(f"{str(datetime.datetime.now())} - Бот запущен")

bot.infinity_polling();