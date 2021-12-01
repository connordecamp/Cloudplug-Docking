# Cloudplug-Docking

## Disclaimer
This is part of a senior project from UT Dallas Electrical and Computer Engineering (ECE) program. Use at your own risk!

This is intended for use with the "CloudPlug-Control" repository for the network code to work properly (or somewhat properly, it's a bit of a mess :D).
This code allows control of a "Docking Station", which is a microcontroller paired with any board that exposes the I2C interface of SFP/SFP+ transceivers. You can use the board from here: https://osmocom.org/projects/misc-hardware/wiki/Sfp-breakout. 

You can run this on a Raspberry Pi 4B and connect its I2C pins (pin #3 (SDA) and pin #5 (SCL)) and GND to the SFP breakout board mentioned above.

TODO-
  Screenshots

# Dependencies
- Python 3.8.10
- mysql-connector-python 
