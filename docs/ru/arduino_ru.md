1. Купите `Arduino Leonardo R3 ATMEGA32U4`, а так-же `ARDUINO USB HOST SHIELD`.
2. Установите Arduino ide.
3. Скачайте [этот архив](https://disk.yandex.ru/d/aZIvJX_YM6FkBw).
4. Распакуйте архив к примеру на рабочий стол.
5. Зайдите в Arduino ide и откройте файл arduino/load_first/1Arduino.ino
6. Во вкладке 1Arduino.ino удалите весь код и вставьте код из файла arduino/new.ino
7. Подключите плату `ARDUINO USB HOST SHIELD` к `Arduino Leonardo` и подключите через к ПК через `ARDUINO`.
8. В Arduino ide выберите COM порт устройства и загрузите скрипт на ардуино. (кнопка стрелочка в право).
9. Перезагрузите Arduino ide.
10. Во вкладке sketch выберите include library-Add .ZIP Library... и откройте файл arduino/USB_Host_Shield_2.0-master.zip. Пойвится окно с саменой файлов, нажмите Yes.
11. Загрузите скрипт на ардуино. (кнопка стрелочка в право).
12. Всё должно быть готово. Попробуйте активировать опцию `mouse_shoot_by_arduino` и `mouse_auto_shoot` в `config.ini`.