1. Все команды выполняются из командной строки, когда вы находитесь в директории программы.
   - После запуска командной строки выполните команду `cd where_you_unpacked_the_bot`, например, 'cd C:\Users\amongus\downloads\yolov8_aimbot'
2. Как запустить программу?
   - `python run.py` или `py run.py`
3. Как изменить настройки?
   - Откройте файл config.ini с помощью блокнота или другого текстового редактора, после изменения опций сохраните файл.
4. Как уменьшить избыточное дрожание прицела?
   - Увеличьте значение `mouse_break_force`
5. Я хочу, чтобы движение мыши было еще более плавным.
   - Увеличьте значение `mouse_smoothing` на 2, 4, 8, 16 и т.д., также увеличьте значение fps.
6. The model does not export, and the line appears TensorRT: export failure ❌ 0.5s: Could not find: cublas64_12.dll. Is it on your PATH?
   - Скачайте [cudnn64_8.zip](https://disk.yandex.ru/d/cm1Wi7OdkLtcLQ) и распакуйте его в C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/(версия cuda)/bin
7. Как установить новую модель, которую я скачал с boosty?
   - Разместите ее в папке `models/`, перейдите в config.ini и измените AI_model_path = sunxds_0.3.4.pt или AI_model_path = sunxds_0.3.4.engine, если вы экспортировали модель в .engine.
8. Как экспортировать модель?
   - Перейдите в раздел [export](https://github.com/SunOner/yolov8_aimbot?tab=readme-ov-file#export-pt-model-to-engine) на странице github.
9. Как запустить его, если игра находится в полноэкранном режиме?
   - Сверните игру, запустите бота, а затем разверните игру (это ошибка dxcam).
10. Прицел стреляет над головой, как настроить?
    - Измените параметр `body_y_offset`. Чем ниже значение, тем ниже будет целиваться.
11. Авто-выстрел не работает в некоторых играх.
    - Некоторые игры имеют защиту от программных кликов мыши.
12. Ошибки сообщаются и исправляются [здесь](https://github.com/SunOner/yolov8_aimbot/issues?q=is%3Aissue)
13. У меня есть предложение по улучшению!
    - [Создайте тему здесь](https://github.com/SunOner/yolov8_aimbot/discussions)