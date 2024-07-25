##  Yolov8 aimbot Инструкция по ручной установке
1. **(ДОПОЛНИТЕЛЬНО ДЛЯ ЧИСТОЙ УСТАНОВКИ)** Удалите все установленные версии Python и Cuda, затем перезагрузите компьютер.
<br></br>
2. Обновите драйвер графики Nvidia. Cudnn должна установиться автоматически после обновления драйвера.
<br></br>
3. Загрузите и установите [Python]((https://www.python.org/downloads/)) версии 3.11.6. На начальном экране установщика активируйте опцию "Add Python 3.11.6 to PATH"!
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/python.png)
<br></br>
4. Загрузите и распакуйте файлы [aimbot Yolov8](https://github.com/SunOner/sunone_aimbot)
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/aimbot.png)
<br></br>
5. Загрузите и установите Cuda версии 12.4, затем перезагрузите компьютер [скачать](https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_551.61_windows.exe)
![](https://github.com/SunOner/sunone_aimbot/blob/main/media/cuda.png)
<br></br>
6. Откройте командную строку и введите `python -m pip install --upgrade pip`, затем `pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu124`
<br></br>
7. Далее в командной строке введите `cd C:/путь_где_вы_распаковали/sunone_aimbot-main/`, затем `pip install -r requirements.txt`
<br></br>
8. Попробуйте запустить aimbot. Введите `python run.py`. Если aimbot работает, экспортируйте модель .pt в .engine.
<br></br>
9. Введите `yolo export model="models/sunxds_0.4.1.pt" format=engine device=0 imgsz=480 half=True`. Экспорт может составить более 10 минут (в зависимости от комплектующих ПК). После экспорта не забудьте изменить модель в `config.ini` на `sunxds_0.4.1.engine`.