# simulation-hub-smarthome

Мой вариант решения практического задания на Академию Бэкенда Tinkoff Python 2023

**Creator:** [@begenFys](https://t.me/begenFys)

**Creator's channel:** [@begenFys_life](https://t.me/begenFys_life)

**[Тестовый сервер для отладки](https://github.com/blackav/smart-home-binary)**

## Настройка окружения

1. Установить зависимости из Pipfile(заведомо установить pipenv)
```
pipenv sync
```

2. Запустить виртуальное окружение
```
pipenv shell
```

## Запуск проекта
1. Запустить тестовый сервер
```
./test_server/<server> -s
```

2. Запустить main.py файл, передав **url сервера** и **адрес хаба в hex виде**
```
python main.py <url> <address>
```

## Чем я вообще занимался, пока реализовал этот проект
Буду рассказывать по шагам, что я делал.
### **1. Декодирование пакетов**

- Я разобрался с такой кодировкой как base64, понял как работают байты, научился с ними манипулировать в Python.
- Написал отдельный класс UrlCoder, который включает в себя функции необходимые для декодирования и кодирования.
- Написал алгоритм обработки ответов, о котором рассказывается ниже

### **2. Кодирование пакетов**
- Сделал удобную структуру в UrlCoder разных функций кодирования: payload -> packet -> response. Дальше буду говорить о том, как я обрабатывал запросы, а там будем видно, что в каждом отдельном классе отдельно кодировался такой параметр, как cmd body.
- Реализовал несколько вспомогательных функций, которые приводят "вид, к которому мы привыкли" к виду, необходимого для отправки на сервер.
- Понял зачем можно использовать битовые операции, оказалось очень удобно и быстро

### **3. Отправка запроса**
- Тут не было чего-то прям сверхъестественного, просто снова поработал с requests

### **4. Обработка ответа запроса**
- Прописал полноценный алгоритм, который обрабатывает пакеты в зависимости от их статуса, также формирование новых пакетов

### **5. Реализация классов устройств**
- Понял зачем нужны и научился пользоваться битовыми операторами для обработки маски

## TODO. Очень хочется реализовать полноценно хорошо
1. Разбить всё на файлы(из-за задания не могу так сделать)
2. Подумать как можно избавиться от повторения запросов и объявления
3. Добавить логирование
4. Прописать документацию
