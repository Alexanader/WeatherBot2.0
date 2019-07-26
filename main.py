import telebot
import constants
import requests
from flask import Flask, request
import logging
from telebot import util
import os
from threading import Timer
import json 

from datetime import datetime, time 
#-----------------
API_TOKEN = constants.token
appid = constants.appid
units = "metric"
server = Flask(__name__)

bot = telebot.TeleBot(API_TOKEN)
bot.delete_webhook()


# Запись в файл в формате json.

def serialize_json(city_name, file_name, user_id):
  data = deserialize_json(file_name)
  with open(file_name, 'w') as f:
    data[str(user_id)] = city_name
    json.dump(data, f)

# Получение нужной ифнормации из json файла.

def deserialize_json(file_name, user_id=None):
  try:
    with open(file_name, 'r') as f:
      data = json.load(f)
      if not user_id:
        return data
      else:
        return data.get(str(user_id)) or 'Please, use the "city" command first'
  except IOError as e:
    with open(file_name, 'w') as f:
      return {}

def log(message, answer):
    print("\n-----------")
    from datetime import datetime
    print((datetime.now()))
    print(("Message from {0} {1}. (id = {2}) \n text : {3}".format(
                                                message.from_user.first_name,
                                                message.from_user.last_name,
                                                str(message.from_user.id),
                                                message.text)))
    print(answer)


# Обьявление кнопок с пошью комманды start.

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row('/start', '/stop')
    user_markup.row('/forecast')
    user_markup.row('/now')
    bot.send_message(message.from_user.id, """Welcome...\n Type some city to get weather (ex. "London")""",
                    reply_markup=user_markup)


# Скрытие кнопок с помощью комманды stop.

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    hide_markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.from_user.id, '..', reply_markup=hide_markup)
  


# Комманда /forecast выводит прогноз погоды на ближайшее 5 дней, если указать 
# город выведет прогноз указанного города, если не указывать, выведет прогноз 
# вашего города.

@bot.message_handler(commands=['forecast'], 
                     content_types=['text'])
def handle_weather_forecast(message):
    buff = str(message.text)
    if 'forecast' in buff:
        words = buff.split()
        bot.send_message(message.from_user.id, 'Wait a bit...')
        req_city = ' '.join(c for c in words if c != 'city' and c != '/forecast')
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast?",
                            params={'q': req_city, 'units': units,
                                    'APPID': appid})
            data = res.json()
            data['list'][0]['weather'][0]['description']
        except Exception as e:
            bot.send_message(message.from_user.id, "I don't know this city, \
                                                    please type another one or\
                                                     fix existing...")
            req_city = deserialize_json('data.json',message.chat.id)
            res = requests.get("http://api.openweathermap.org/data/2.5/forecast?",
                            params={'q': req_city, 'units': units,
                                    'APPID': appid})
            data = res.json()
            bot.send_message(message.from_user.id, "Here is the weather for \
                                                    the last correct city.")
            print(data)
        finally:
            result = dict()
            print(data)
            for i in range(0,40,8):
                result['description']     = data['list'][i]['weather'][0]['description']
                result['temperature']     = str(data['list'][i]['main']['temp'])+' C'
                result['min temperature'] = str(data['list'][i]['main']['temp_min'])+' C'
                result['max temperature'] = str(data['list'][i]['main']['temp_max'])+' C'
                result['wind']            = str(data['list'][i]['wind']['speed']) + 'm/s'
                result['name']            = data['city']['name']
                result['date']            = str(data['list'][i]['dt_txt'])
                bot.send_message(message.from_user.id,
            """Weather in {0} {1} is 
        {2}
        Temperature: {3}
        Minimal temperature: {4}
        Maximal temperature: {5}
        Wind speed: {6}""".format(result['name'], result['date'],
                                  result['description'], result['temperature'],
                                  result['min temperature'], result['max temperature'],
                                  result['wind']))

                log(message, '')


# Комманда /now выводит прогноз погоды сегодняшнего дня, если указать 
# город выведет прогноз указанного города, если не указывать, выведет прогноз 
# вашего города.

@bot.message_handler(commands=['now'],
                     content_types=['text'])
def handle_weather_now(message):
    buff = message.text
    if 'now' in buff:
        words = buff.split()
        bot.send_message(message.from_user.id, 'Wait a bit...')
        req_city = ' '.join(c for c in words if c != 'city' and c!= '/now')
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                            params={'q': req_city, 'units': units,
                                    'APPID': appid})
            data = res.json()
            data['weather'][0]['description']
        except Exception as e:
            req_city = deserialize_json('data.json',message.chat.id)
            print(req_city)
            res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                            params={'q': req_city, 'units': units,
                                    'APPID': appid})
            data = res.json()
            bot.send_message(message.from_user.id, "Here is the weather for the last correct city.")
        
        finally:
            result = dict()
            print(data)
            result['description']     = data['weather'][0]['description']
            result['temperature']     = str(data['main']['temp'])+' C'
            result['min temperature'] = str(data['main']['temp_min'])+' C'
            result['max temperature'] = str(data['main']['temp_max'])+' C'
            result['wind']            = str(data['wind']['speed']) + 'm/s'
            result['name']            = data['name']

            bot.send_message(message.from_user.id,
"""Weather in {0} today : {1}
Temperature: {2}
Minimal temperature: {3}
Maximal temperature: {4}
Wind speed: {5}""".format(result['name'], result['description'],
                          result['temperature'], result['min temperature'],
                          result['max temperature'], result['wind']))

            log(message, '')


# Функция hander_weather запоминает введеный вами город в файл data.json для 
# для использование его в дальнейшем, так же выводит погоду в городе на данный
# момент.

@bot.message_handler(content_types=['text'])
def handle_weather(message):
    buff = message.text
    #if 'city' in buff:
    words = buff.split()
    bot.send_message(message.from_user.id, 'Wait a bit...')
    req_city = ' '.join(c for c in words if c != 'city')
    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                        params={'q': req_city, 'units': units, 'APPID': appid})
        data = res.json()
        data['weather'][0]['description']
    except Exception as e:
        bot.send_message(message.from_user.id, "I don't know this city, \
                                                please type another one or\
                                                fix existing...")
        req_city = deserialize_json('data.json',message.chat.id)
        print(req_city)
        res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                        params={'q': req_city, 'units': units, 'APPID': appid})
        data = res.json()
        bot.send_message(message.from_user.id, "Here is the weather for \
                                                the last correct city.")
    else:
        city = req_city
        serialize_json(city, 'data.json',message.chat.id)
        result = dict()
        print(data)
        result['description']     = data['weather'][0]['description']
        result['temperature']     = str(data['main']['temp'])+' C'
        result['min temperature'] = str(data['main']['temp_min'])+' C'
        result['max temperature'] = str(data['main']['temp_max'])+' C'
        result['wind']            = str(data['wind']['speed']) + 'm/s'
        result['name']            = data['name']

        bot.send_message(message.from_user.id,
"""Weather in {0} today : {1}
Temperature: {2}
Minimal temperature: {3}
Maximal temperature: {4}
Wind speed: {5}""".format(result['name'], result['description'],
                          result['temperature'], result['min temperature'],
                          result['max temperature'], result['wind']))

        log(message, '')


# Функция send_weather используетсья для вывода прогноза погоды вашего города 
# с помощью chat_id и city которые находяться в data.json.

def send_weather():
    data = deserialize_json('data.json')
    for chat_id, city in data.items():
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                    params={'q': city, 'units': units, 'APPID': appid})
            data = res.json()
            data['weather'][0]['description']
        except Exception as e:
            req_city = deserialize_json('data.json',message.chat.id)
            print(req_city)
            res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                            params={'q': req_city, 'units': units, 'APPID': appid})
            data = res.json()
            bot.send_message(message.from_user.id, 'sorry incorrect name')
        finally:    
            result = dict()
            print(data)
            result['description']     = data['weather'][0]['description']
            result['temperature']     = str(data['main']['temp'])+' C'
            result['min temperature'] = str(data['main']['temp_min'])+' C'
            result['max temperature'] = str(data['main']['temp_max'])+' C'
            result['wind']            = str(data['wind']['speed']) + 'm/s'
            result['name']            = data['name']

            bot.send_message(int(chat_id),
"""Weather in {0} today : {1}
Temperature: {2}
Minimal temperature: {3}
Maximal temperature: {4}
Wind speed: {5}""".format(result['name'], result['description'],
                          result['temperature'], result['min temperature'],
                          result['max temperature'], result['wind']))


x    = time(15, 00, 00, 00000)
y    = time(15, 24, 00, 00000)
secs = 30


# Функция every_day служит определителем времени, для отправки прогноза погоды 
# ежендневно.

def every_day():
    if x < datetime.now().time() < y:
        print(datetime.now().time())
        data = deserialize_json('data.json')
        send_weather()


t = Timer(secs, every_day)
t.start()

@server.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url= 'https://ancient-wave-55409.herokuapp.com/' + API_TOKEN)
    return "!", 200



            
if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    # bot.polling(none_stop=True, )


