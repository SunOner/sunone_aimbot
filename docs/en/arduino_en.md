1. Purchase an `Arduino Leonardo R3 ATMEGA32U4` and an `ARDUINO USB HOST SHIELD`.
2. Install the Arduino IDE on your computer.
3. Download [this archive](https://disk.yandex.ru/d/aZIvJX_YM6FkBw).
4. Extract the archive to a location on your computer, such as the desktop.
5. Open Arduino IDE and navigate to the `arduino/load_first/1Arduino.ino` file.
6. In the `1Arduino.ino` tab, remove all the existing code and replace it with the code from the `arduino/new.ino` file.
7. Connect the `ARDUINO USB HOST SHIELD` to the `Arduino Leonardo` and then connect it to your PC using the `ARDUINO` cable.
8. In the Arduino IDE, select the COM port for your device and upload the script to your Arduino (click the right arrow button).
9. Restart the Arduino IDE.
10. In the IDE, go to the `Sketch` menu, select `Include Library > Add .ZIP Library...` and navigate to the `arduino/USB_Host_Shield_2.0-master.zip` file. Click `Yes` when prompted about replacing files.
11. Upload the script to your Arduino (click the right arrow button).
12. Everything should now be set up. Try enabling the `mouse_shoot_by_arduino` and `mouse_auto_shoot` options in the `config.ini`.