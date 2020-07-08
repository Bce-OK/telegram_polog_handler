# Polog - ультимативный логгер для баз данных

Используйте преимущества базы данных для логгирования в ваших проектах! Легко ищите нужные вам логи, составляйте статистику и управляйте ими при помощи SQL.

Данный пакет максимально упростит миграцию ваших логов в базу данных. Вот список некоторых преимуществ логгера Polog:

- Автоматическое логгирование. Просто повесьте декоратор на вашу функцию или класс, и каждый их вызов будет автоматически логгироваться в базу данных (или не каждый - это легко настроить)!
- Высокая производительность. Непосредственно сама запись в базу делается из отдельных потоков и не блокирует основной поток исполнения вашей программы.
- Поддержка асинхронных функций. Декораторы для автоматического логгирования работают как на синхронных, так и на асинхронных функциях.
- Самый простой синтаксис. Сделать логгирование еще проще уже вряд ли возможно. Вы можете залоггировать целый класс всего одной строчкой кода. Имена функций короткие, насколько это позволяет здравый смысл.
- Удобное профилирование. В базу автоматически записывается время работы ваших функций. Так вы можете накопить статистику производительности вашего кода и легко ее анализировать.

## Быстрый старт

Просто импортируйте декоратор @flog() и примените его к вашей функции. Никаких настроек, ничего лишнего - все уже работает.

```
from polog.flog import flog


@flog()
def sum(a, b):
  return a + b

print(sum(2, 2))
```

На этом примере при первом вызове вашей функции sum в папке с вашим проектом будет автоматически создан файл с базой данных sqlite, в которой появится соответствующая запись. В данном случае сохранится информация о том, какая функция была вызвана, из какого она модуля, с какими аргументами, сколько времени заняла ее работа и какой результат она вернула.

```
from polog.flog import flog


@flog()
def division(a, b):
  return a / b

print(division(2, 0))
```

Произошла ошибка, мы делим число на 0. Что на этот раз записано в базу? Очевидно, что результат работы функции в базу записан не будет, т.к. она не успела ничего вернуть. Зато там появилась подробная информация об ошибке: название вызванного исключения, текст его сообщения, и главное, трейсбек. Кроме того, появится отметка о неуспешности выполненной операции - ко всем автоматическим логам такие метки проставляются автоматически, чтобы вы могли легко выбирать из базы данных только успешные или только неуспешные операции и как-то анализировать результат.

```
from polog.flog import flog


@flog()
def division(a, b):
  return a / b

@flog()
def operation(a, b):
  return division(a, b)

print(operation(2, 0))
```

Чего примечательного в этом примере кода? В данном случае ошибка происходит в функции division(), а затем, поднимаясь по стеку вызовов, она проходит через функцию operation(). Однако логгер записал в базу данных сообщение об ошибке только один раз! Встретив исключение в первый раз, он пишет его в базу и подменяет другим, специальным, которое игнорирует в дальнейшем. В результате ваша база данных не засоряется бесконечным дублированием информации об ошибках.

На случай, если ваш код специфически реагирует на конкретные типы исключений и вы не хотите, чтобы логгер исключал дублирование логов таким образом, его поведение можно изменить, об этом вы можете прочитать в более подробной части документации ниже.

```
from polog.clog import clog


@clog()
class OneOperation(object):
  def division(self, a, b):
    return a / b

  def operation(self, a, b):
    return self.division(a, b)

print(OneOperation().operation(2, 0))
```

Что, если мы хотим залоггировать целый класс? Обязательно ли проходиться по всем его методам и на каждый вешать декоратор @flog()? Нет! Для классов существует декоратор @clog(). Что он делает? Он за вас проходится по методам класса и вешает на каждый из них декоратор @flog(). Если вы не хотите логгировать ВСЕ методы класса, передайте в @clog() имена методов, которые вам нужно залоггировать, например: @clog('division').

```
from polog.log import log


log(message="All right!")
log(message="It's bad.", success=False, exception=ValueError("Example of an exception."))
```

Если вам все же не хватило автоматического логгирования, вы можете писать логи вручную, вызывая функцию log() из своего кода.

На этом введение закончено. Если вам интересны тонкости настройки логгера и его более мощные функции, можете почитать более подробную документацию.

## Подробности

Начнем с общей информации о логгере. Запись в базу данных происходит из отдельных потоков. Ваша программа "выплевывает" логи в очередь, откуда их считывают воркеры в отдельных потоках. Непосредственно запись в БД происходит в момент, когда ваша программа уже продолжает делать что-то другое. Количество потоков, которые пишут в БД, можно настроить, по умолчанию оно равно 2-м.

Таблица, в которую происходит запись, выглядит так:

| id | function | module | message | exception_type | exception | traceback | input_variables | result | success | time | time_of_work | service | auto | level |
| -- | -------- | ------ | ------- | -------------- | --------- | --------- | --------------- | ------ | ------- | ---- | ------------ | ------- | ---- | ----- |
| int | str | str | str | str | str | str | str | str | bool | datetime | float | str | bool | int |

Рассмотрим предназначение столбцов в таблице подробнее:

- id. Главное, что вы должны знать про столбец id - порядок их распределения не обязан совпадать с реальным порядком следования операций. Запись в базу данных производится из нескольких потоков, асинхронно. Чтобы получить операции в порядке их реального следования, сортируйте таблицу по полю **time**.
- function: название функции, действие в которой мы логгируем. При автоматическом логгировании (которое происходит через декораторы), название функции берется извлекается из атрибута \_\_name\_\_ объекта функции. При ручном логгировании вы можете передать в логгер как сам объект функции, чтобы из нее автоматически извлекся атрибут \_\_name\_\_, так и строку с названием функции. Рекомендуется предпочесть первый вариант, т.к. это снижает вероятность опечаток.
- module: название модуля, в котором произошло событие. Автоматически извлекается из атрибута \_\_module\_\_ объекта функции.
- message: произвольный текст, который вы можете приписать к каждому логу.
- exception_type: тип исключения. Автоматические логи заполняют эту колонку самостоятельно, вручную - вам нужно передать в логгер объект исключения.
- exception: сообщение, с которым вызывается исключение.
- traceback: json со списком строк трейсбека. При ручном логгировании данное поле недоступно.
- input_variables: входные аргументы логгируемой функции. Автоматически логгируются в формате json. Стандартные для json типы данных указываются напрямую, остальные преобразуются в строку. Чтобы вы могли отличить преобразованный в строку объект от собственно строки, к каждой переменной указывается ее оригинальный тип данных из кода python. Для генерации подобных json'ов при ручном логгировании рекомендуется использовать функцию polog.utils.json_vars(), куда можно передавать любый аргументы (позиционные и именные) и получать в результате стандартно оформленный json.
- result: то, что вернула задекорированная логгером функция. Вы не можете заполнить это поле при ручном логгировании.
- success: метка успешного завершения операции. При автоматическом логгировании проставляется в значение True, если в задекорированной функции не произошло исключений. При ручном логгировании вы можете проставить метку самостоятельно, либо она заполнится автоматически, если передадите в функцию log объект исключения (False).
- time: объект datetime, соответствующий дате и времени начала операции. Заполняется всегда автоматически, в том числе при ручном логгировании.
- time_of_work: время работы задекорированной логгером функции, в секундах. Проставляется автоматически. При ручном логгировании вы не можете указать этот параметр.
- service: название или идентификатор сервиса, из которого пишутся логи. Идея в том, что в одну базу и в одну таблицу у вас могут писать несколько разных сервисов, а вы можете легко отфильтровывать только те из них, которые вас интересуют в момент чтения логов. Имя сервиса по умолчанию - 'base'. 
- auto:
- level:


### Уровни логгирования

Каждая запись в базе данных сопровождается це
