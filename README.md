# Polog - универсальный логгер для баз данных

Используйте преимущества базы данных для логгирования в ваших проектах! Легко ищите нужные вам логи, составляйте статистику и управляйте ими при помощи стандартного языка SQL.

Данный пакет максимально упростит миграцию ваших логов в базу данных. Вот список некоторых преимуществ логгера Polog:

&gt; Автоматическое логгирование. Просто повесьте декоратор на вашу функцию или класс, и каждый их вызов будет автоматически логгироваться в базу данных!
&gt;
&gt; Высокая производительность. Непосредственно сама запись в базу делается из отдельных потоков и не блокирует основной поток исполнения вашей программы.
&gt;
&gt; Поддержка асинхронных функций. Декораторы для автоматического логгирования работают как на синхронных, так и на асинхронных функциях.
&gt;
&gt; Самый простой синтаксис. Сделать логгирование еще проще уже вряд ли возможно. Вы можете залоггировать целый класс всего одной строчкой кода.
