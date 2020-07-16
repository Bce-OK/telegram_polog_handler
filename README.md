# Polog - ультимативный логгер, пишущий в базу данных

Используйте преимущества базы данных для логирования в ваших проектах! Легко ищите нужные вам логи, составляйте статистику и управляйте записями при помощи SQL.

Данный пакет максимально упростит миграцию ваших логов в базу данных. Вот список некоторых преимуществ логгера Polog:

- **Автоматическое логирование**. Просто повесьте декоратор на вашу функцию или класс, и каждый вызов будет автоматически логироваться в базу данных (или только ошибки - это легко настроить)!
- **Высокая производительность**. Непосредственно сама запись в базу делается из отдельных потоков и не блокирует основной поток исполнения вашей программы.
- **Поддержка асинхронных функций**. Декораторы для автоматического логирования работают как на синхронных, так и на асинхронных функциях.
- **Самый простой синтаксис**. Сделать логирование еще проще уже вряд ли возможно. Вы можете залогировать целый класс всего одной строчкой кода. Имена функций короткие, насколько это позволяет здравый смысл.
- **Удобное профилирование**. В базу автоматически записывается время работы ваших функций. Так вы можете накопить статистику производительности вашего кода и легко ее анализировать.
- Поддержка **SQLite**, **PostgreSQL**, **MySQL**, **Oracle** и **CockroachDB** за счет использования "под капотом" [Pony ORM](https://ponyorm.org/).
- Удобная работа с **несколькими сервисами**, которые пишут в одну базу.

## Быстрый старт

Установите Polog через pip:

```
pip install polog
```

Теперь просто импортируйте декоратор ```@flog()``` и примените его к вашей функции. Никаких настроек, ничего лишнего - все уже работает:

```python
from polog.flog import flog


@flog()
def sum(a, b):
  return a + b

print(sum(2, 2))
```

На этом примере при первом вызове функции sum() в папке с вашим проектом будет автоматически появится файл с базой данных SQLite, в которой будет соответствующая запись. В данном случае сохранится информация о том, какая функция была вызвана, из какого она модуля, с какими аргументами, сколько времени заняла ее работа и какой результат она вернула.

Теперь попробуем залогировать ошибку:

```python
from polog.flog import flog


@flog()
def division(a, b):
  return a / b

print(division(2, 0))
```

Делим число на 0. Что на этот раз записано в базу? Очевидно, что результат работы функции записан не будет, т.к. она не успела ничего вернуть. Зато там появилась подробная информация об ошибке: название вызванного исключения, текст его сообщения, трейсбек и даже локальные переменные. Кроме того, появится отметка о неуспешности выполненной операции - они проставляются ко всем автоматическим логам, чтобы вы могли легко выбирать из базы данных только успешные или только неуспешные операции и как-то анализировать результат.

Еще небольшой пример кода:

```python
from polog.flog import flog


@flog()
def division(a, b):
  return a / b

@flog()
def operation(a, b):
  return division(a, b)

print(operation(2, 0))
```

Чего в нем примечательного? В данном случае ошибка происходит в функции division(), а затем, поднимаясь по стеку вызовов, она проходит через функцию operation(). Однако логгер записал в базу данных сообщение об ошибке только один раз! Встретив исключение в первый раз, он пишет его в базу и подменяет другим, специальным, которое игнорирует в дальнейшем. В результате ваша база данных не засоряется бесконечным дублированием информации об ошибках.

На случай, если ваш код специфически реагирует на конкретные типы исключений и вы не хотите, чтобы логгер исключал дублирование логов таким образом, его поведение можно изменить, об этом вы можете прочитать в более подробной части документации ниже. Однако имейте ввиду, что, возможно, существуют лучшие способы писать код, чем прокидывать исключения через много уровней стека вызовов функций, после чего ловить их там, ожидая конкретный тип.

Что, если мы хотим залогировать целый класс? Обязательно ли проходиться по всем его методам и на каждый вешать декоратор ```@flog()```? Нет! Для классов существует декоратор ```@clog()```:

```python
from polog.clog import clog


@clog()
class OneOperation(object):
  def division(self, a, b):
    return a / b

  def operation(self, a, b):
    return self.division(a, b)

print(OneOperation().operation(2, 0))
```

Что он делает? Он за вас проходится по методам класса и вешает на каждый из них декоратор ```@flog()```. Если вы не хотите логировать ВСЕ методы класса, передайте в ```@clog()``` имена методов, которые вам нужно залогировать, например: ```@clog('division')```.

Если вам все же не хватило автоматического логирования, вы можете писать логи вручную, вызывая функцию ```log()``` из своего кода:

```python
from polog.log import log


log(message="All right!")
log(message="It's bad.", exception=ValueError("Example of an exception."))
```

На этом введение закончено. Если вам интересны тонкости настройки логгера и его более мощные функции, можете почитать более подробную документацию.

## Подробности

Начнем с общей информации о логгере. Ваша программа "выплевывает" логи в очередь, откуда их считывают воркеры в отдельных потоках. Непосредственно запись в БД происходит в момент, когда ваша программа уже продолжает делать что-то другое. Количество потоков, которые пишут в БД, можно настроить (подробнее об этом ниже), по умолчанию оно равно 2-м.

Таблица, в которую происходит запись, выглядит так:

| id  | level | function | module | message | exception_type | exception_message | traceback | input_variables | local_variables | result | success | time     | time_of_work | service | auto |
| --- | ----- | -------- | ------ | ------- | -------------- | ----------------- | --------- | --------------- | --------------- | ------ | ------- | --------- | ------------ | ------- | ---- |
| int | int   | str      | str    | str     | str            | str               | str       | str             | str             | str    | bool    | datetime | float        | str     | bool |


Рассмотрим предназначение столбцов в таблице подробнее:

- **id**. Главное, что вы должны знать про столбец **id** - порядок распределения в нем значений не обязан совпадать с реальным порядком следования операций. Запись в базу данных производится из нескольких потоков, асинхронно. Чтобы получить операции в порядке их реального следования, сортируйте таблицу по полю **time**.
- **level**: уровень важности лога. Подробнее об уровнях в следующем разделе. На данном этапе вам только нужно знать, что по умолчанию при автоматическом логировании уровень обычного события - 1, а уровень исключения - 2. Поэтому вам достаточно установить общий уровень логирования, равный 2-м, чтобы в базу не попадало ничего, кроме ошибок.
- **function**: название функции, действие в которой мы логируем. При автоматическом логировании (которое происходит через декораторы), название функции извлекается из атрибута \_\_name\_\_ объекта функции. При ручном логировании вы можете передать в логгер как сам объект функции, чтобы из нее автоматически извлекся атрибут \_\_name\_\_, так и строку с названием функции. Рекомендуется предпочесть первый вариант, т.к. это снижает вероятность опечаток.
- **module**: название модуля, в котором произошло событие. Автоматически извлекается из атрибута \_\_module\_\_ объекта функции.
- **message**: произвольный текст, который вы можете приписать к каждому логу.
- **exception_type**: тип исключения. Автоматические логи заполняют эту колонку самостоятельно, вручную - вам нужно передать в логгер объект исключения.
- **exception_message**: сообщение, с которым вызывается исключение.
- **traceback**: json со списком строк трейсбека. При ручном логировании данное поле недоступно.
- **input_variables**: входные аргументы логируемой функции. Автоматически логируются в формате json. Стандартные для json типы данных указываются напрямую, остальные преобразуются в строку. Чтобы вы могли отличить преобразованный в строку объект от собственно строки, к каждой переменной указывается ее оригинальный тип данных из кода python. Для генерации подобных json'ов при ручном логировании рекомендуется использовать функцию ```json_vars()```, куда можно передавать любый аргументы (позиционные и именные) и получать в результате стандартно оформленный json.
- **local_variables**: локальные переменные функции. Извлекаются автоматически при автоматическом логировании исключений. Также представлены в виде json с указанием типов данных.
- **result**: то, что вернула задекорированная логгером функция. Вы не можете заполнить это поле при ручном логировании.
- **success**: метка успешного завершения операции. При автоматическом логировании проставляется в значение True, если в задекорированной функции не произошло исключений. При ручном логировании вы можете проставить метку самостоятельно, либо она заполнится автоматически, если передадите в функцию log объект исключения (False).
- **time**: объект datetime, соответствующий дате и времени начала операции. Заполняется всегда автоматически, в том числе при ручном логировании.
- **time_of_work**: время работы задекорированной логгером функции, в секундах. Проставляется автоматически. При ручном логировании вы не можете указать этот параметр.
- **service**: название или идентификатор сервиса, из которого пишутся логи. Идея в том, что в одну базу и в одну таблицу у вас могут писать несколько разных сервисов, а вы можете легко отфильтровывать только те из них, которые вас интересуют в момент чтения логов. Имя сервиса по умолчанию - 'base'. Изменить его вы можете через ```Config.settings(service_name='<YOUR SERVICE NAME>')```, об этом подробнее будет ниже.
- **auto**: метка, автоматический лог или ручной. Проставляется автоматически, вы не можете этим управлять.

### Уровни логирования

Как было сказано выше, по умолчанию автоматические логи имеют 2 уровня: 1 и 2. 1 - это рядовое событие, 2 - исключение. Однако это легко поменять.

В декораторах вы можете указать желаемый уровень логирования:

```python
from polog.flog import flog


@flog(level=5)
def sum(a, b):
  return a + b

print(sum(2, 2))
# В базу упадет лог с меткой 5 уровня.
```

Это доступно как для ```@flog()```, так и для ```@clog()```, работает одинаково.

Также вы можете присвоить уровням логирования имена и в дальнейшем использовать их вместо чисел:

```python
from polog.config import Config
from polog.flog import flog


# Присваиваем уровню 5 имя 'ERROR', а уровню 1 - 'ALL'.
Config.levels(ERROR=5, ALL=1)

# Используем присвоенное имя вместо номера уровня.
@flog(level='ERROR')
def sum(a, b):
  return a + b

print(sum(2, 2))
# В базу упадет лог с меткой 5 уровня.
```

При этом указание уровней числами вам по-прежнему доступно, имена и числа взаимозаменяемы.

Если вы привыкли пользоваться стандартным модулем [logging](https://docs.python.org/3.8/library/logging.html), вы можете присвоить уровням логирования [стандартные имена](https://docs.python.org/3.8/library/logging.html#logging-levels) оттуда:

```python
from polog.config import Config
from polog.flog import flog


# Имена уровням логирования проставляются автоматически, в соответствии со стандартной схемой.
Config.standart_levels()

@flog(level='ERROR')
def sum(a, b):
  return a + b

print(sum(2, 2))
# В базу упадет лог с меткой 40 уровня.
```

Также вы можете установить текущий уровень логирования:

```python
from polog.config import Config
from polog.flog import flog


# Имена уровням логирования проставляются автоматически, в соответствии со стандартной схемой.
Config.standart_levels()

# Устанавливаем текущий уровень логирования - 'CRITICAL'.
Config.settings(level='CRITICAL')

@flog(level='ERROR')
def sum(a, b):
  return a + b

print(sum(2, 2))
# Запись в базу произведена не будет, т. к. уровень сообщения 'ERROR' ниже текущего уровня логирования 'CRITICAL'.
```

Все события уровнем ниже в базу не пишутся. По умолчанию уровень равен 1.

Используя декораторы, для ошибок вы можете установить отдельный уровень логирования:

```python
# Работает одинаково в декораторе функций и декораторе классов.
@flog(level='DEBUG', error_level='ERROR')
@clog(level='DEBUG', error_level='ERROR')
```

Также вы можете установить уровень логирования для ошибок глобально через настройки:

```python
from polog.config import Config


Config.settings(error_level='CRITICAL')
```

Сделав это 1 раз, вы можете больше не указывать уровень логирования локально в каждом декораторе. Но иногда вам это может быть полезным. Уровень, указанный в декораторе, обладает более высоким приоритетом, чем глобальный. Поэтому вы можете, к примеру, для какого-то особо важного класса указать более высокий уроень логирования. Или наоборот, понизить его, если не хотите в данный момент записывать логи из конкретной функции или класса.

### Общие настройки

Выше уже упоминалось, что общие настройки логирования можно делать через класс ```Config```. Давайте вспомним, откуда его нужно импортировать:

```python
from polog.config import Config
```

Класс ```Config``` предоставляет несколько методов. Все они работают непосредственно от класса, без вызова \_\_init\_\_, например вот так:

```python
Config.settings(pool_size=5)
```

- **```settings()```**: общие настройки логирования.

Принимает следующие именованные параметры:

**pool_size** (int) - количество потоков-воркеров, которые пишут в базу данных. По умолчанию оно равно 2-м. Вы можете увеличить это число, если ваша программа пишет в базу достаточно интенсивно.

**service_name** (str) - имя сервиса. Указывается в каждой записи в базу. По умолчанию 'base'.

**level** (int) - общий уровень логирования. Подробнее в разделе "**Уровни логирования**" (выше).

**errors_level** (int) - уровень логирования для ошибок. Также см. в "**Уровни логирования**".

**original_exceptions** (bool) - режим оригинальных исключений. По умолчанию False. True означает, что все исключения остаются как были и никак не видоизменяются логгером. Это может приводить к дублированию информации об одной ошибке в базе данных, т. к. исключение, поднимаясь по стеку вызовов функций, может пройти через несколько задекорированных логгером функций. В режиме False все исключения логируются 1 раз, после чего оригинальное исключение подменяется на ```polog.errors.LoggedError```, которое не логируется никогда.

- **```levels()```**: присвоение имен уровням логирования, см. подробнее в разделе "**Уровни логирования**".

- **```standart_levels()```**: присвоение стандартных имен уровням логирования, см. подробнее в разделе "**Уровни логирования**".

- **```db()```**: указание базы данных, куда будут писаться логи.

Для управления базой данных Polog использует [Pony ORM](https://ponyorm.org/) - самую быструю и удобную ORM из доступных на python. В метод ```db()``` вы можете передать данные для подключения к базе данных в том же формате, в каком это делается в методе ```bind()``` [самой ORM](https://docs.ponyorm.org/database.html).

Pony поддерживает: **SQLite**, **PostgreSQL**, **MySQL**, **Oracle**, **CockroachDB**.

Если вы не укажете никакую базу данных, по умолчанию логи будут писаться в базу SQLite, которая будет автоматически создана в папке с проектом в файле с названием ```logs.db```.

### Декоратор @flog()

Декоратор ```@flog()``` используется для автоматического логирования вызовов функций. Поддерживает как обычные функции, так и [корутины](https://docs.python.org/3/library/asyncio-task.html).

Напомним, он импортируется так:

```python
from polog.flog import flog
```

Используйте параметр ```message``` для добавления произвольного текста к каждому логу.

```python
@flog(message='This function is very important!!!')
def very_important_function():
  ...
```

Про управление уровнями логирования через аргументы к данному декоратору читайте в разделе "**Уровни логирования**" (выше).

### @clog() - декоратор класса

По традиции, вспомним, откуда он импортируется:

```python
from polog.clog import clog
```

Принимает все те же аргументы, что и ```@flog()```. Автоматически навешивает декоратор ```@flog()``` на все методы задекорированного класса.

Игнорирует дандер-методы (методы, чьи названия начинаются с "\_\_").

Если не хотите логировать все методы класса, можете перечислить нужные в качестве неименованных аргументов:

```python
@сlog('important_method', message='This class is also very important!!!')
class VeryImportantClass():
  def important_method(self):
    ...
  def not_important_method(self):
    ...
  ...
```

### Перекрестное использование ```@сlog()``` и ```@flog()```

При наложении на одну функцию нескольких декораторов логирования, срабатывает из них по итогу только один. Это достигается за счет наличия внутреннего реестра задекорированных функций. При каждом новом декорировании декорируется оригинальная функция, а не ее уже ранее задекорированная версия.

Пример:

```python
@flog(level=6) # Сработает только этот декоратор.
@flog(level=5) #\
@flog(level=4) # |
@flog(level=3) #  > А эти нет. Они знают, что их несколько на одной функции и уступают место последнему.
@flog(level=2) # |
@flog(level=1) #/
def some_function(): # При каждом вызове этой функции лог будет записан только 1 раз.
  ...
```

Мы наложили на одну функцию 6 декораторов ```@flog()```, однако реально сработает из них только тот, который выше всех. Это удобно в ситуациях, когда вам нужно временно изменить уровень логирования для какой-то функции. Не редактируйте старый декоратор, просто навесьте новый поверх него, и уберите, когда он перестанет быть нужен.

Также вы можете совместно использовать декораторы ```@сlog()``` и ```@flog()```:

```python
@сlog(level=3)
class SomeClass():
  @flog(level=10)
  def some_method(self):
    ...

  def also_some_method(self):
    ...
  ...
```

У ```@flog()``` приоритет всегда выше, чем у ```@сlog()```, поэтому в примере some_method() окажется задекорирован только через ```@flog()```, а остальные методы - через ```@сlog()```. Используйте это, когда вам нужно залогировать отдельные методы в классе как-то по-особенному.

### Запрет логирования через декоратор ```@logging_is_forbidden```

На любую функцию или метод вы можете навесить декоратор ```@logging_is_forbidden```, чтобы быть уверенными, что тут не будут срабатывать декораторы ```@сlog()``` и ```@flog()```. Это удобно, когда вы хотите, к примеру, временно приостановить логирование какой-то функции, не снимая логирующего декоратора.

Импортируется ```@logging_is_forbidden``` так:

```python
from polog.forbid import logging_is_forbidden
```

```@logging_is_forbidden``` сработает при любом расположении среди декораторов логирования:

```python
@flog(level=5) # Этот декоратор не сработает.
@flog(level=4) # И этот.
@flog(level=3) # И этот.
@logging_is_forbidden
@flog(level=2) # И вот этот.
@flog(level=1) # И даже этот.
def some_function():
  ...
```

Также ```@logging_is_forbidden``` удобно использовать совместно с ```@сlog()``` для отдельных методов класса.

```python
@сlog()
class VeryImportantClass():
  def important_method(self):
    ...

  @logging_is_forbidden
  def not_important_method(self):
    ...
  ...
```

Иногда это может быть удобнее, чем прописывать "разрешенные" методы в самом ```@сlog()```. Например, когда в вашем классе много методов и строка с их перечислением получилась бы слишком огромной.

### "Ручное" логирование через ```log()```

Отдельные важные события в вашем коде вы можете регистрировать вручную.

Импортируйте функцию ```log()```:

```python
from polog.log import log
```

И используйте ее в вашем коде:

```python
log(message='Very important message!!!')
```

Уровень логирования вы можете передать первым неименованным аргументом:

```python
# Когда псевдонимы для уровней логирования прописаны по стандартной схеме.
log('ERROR', message='Very important message!!!')
# Ну или просто в виде числа.
log(40, message='Very important message!!!')
```

Вы можете передать в ```log()``` функцию, в которой исполняется код:

```python
def foo():
  log(function=foo)
```

Колонки **function** и **module** в этом случае заполнятся автоматически.

Также вы можете передать в ```log()``` экземпляр исключения:

```python
try:
  var = 1 / 0
except ZeroDivisionError as e:
  log(exception=e)
```

Колонки **exception_message** и **exception_type** тогда тоже заполнятся автоматически. Флаг ```success``` будет установлен в значение False. Трейсбек автоматически не заполняется и задать его вручную невозможно.

При желании, в качестве аргументов ```function``` и ```exception``` можно использовать и обычные строки, но тогда дополнительные поля не заполнятся сами как надо.

Также вы можете передавать в ```log()``` произвольные переменные, которые считаете нужным залогировать. Для этого нужно использовать функцию ```json_vars()```, которая принимает любые аргументы и переводит их в стандартный json-формат:

```python
from polog.utils.json_vars import json_vars
from polog.log import log


def bar(a, b, c, other=None):
  ...
  log(function=bar, vars=json_vars(a, b, c, other=other))
  ...
```

Также вы можете автоматически получить все переменные в функции при помощи [```locals()```](https://docs.python.org/3/library/functions.html#locals):

```python
def bar(a, b, c, other=None):
  ...
  log(function=bar, vars=json_vars(**locals()))
  ...
```

### Общие советы про логирование

Чтобы получить наибольшую пользу от ведения логов, следуйте нескольким небольшим правилам для организации вашего проекта.

- Заведите для логов отдельную базу данных. Она может быть одна для нескольких разных проектов или сервисов, однако желательно отделить ее от той базы, с которой работает ваше приложение. Логирование иногда может быть достаточно интенсивным, и так вы защитите функциональность вашего приложения от этой нагрузки.
- Держите каждый класс в отдельном файле. Не держите "отдельно стоящих" функций в одном файле с классом. Помимо очевидного, что это делает вашу работу с проектом удобнее, это также устраняет возможность конфликта имен. Polog записывает название функции и модуля. Но если в модуле присутствуют 2 функции с одинаковыми названиями (например, в составе разных классов), вы не сможете их отличить, когда будете читать логи, и можете принять за одну функцию, которая почему-то ведет себя по-разному.
- Следите за конфиденциальностью данных, которые вы логируете. Скажем, если функция принимает в качестве аргумента пароль пользователя, ее не стоит логировать. Polog предоставляет удобные возможности для экранирования функций от логирования, например декоратор ```@logging_is_forbidden```.
- Избегайте логирования функций, которые вызываются слишком часто. Обычно это функции с низким уровнем абстракции, лежащие в основе вашего проекта. Выберите уровень абстракции, на котором количество логов становится достаточно комфортным. Помните, что, поскольку запись логов в базу делается в отдельном потоке, то, что вы не чувствуете тормозов от записи логов, не означает, что логирование не ведется слишком интенсивно. Вы можете не заметить, если Polog пишет по несколько гигабайт логов в минуту.
