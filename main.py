

from oled import OLED_1inch3
from bmp280 import *
from machine import Pin, I2C

from font_5x5 import Font_5x5
import time
import random

DEBUG = False

# Oled display pins (SPI)
DC   =  8
RST  = 12
MOSI = 11
SCK  = 10
CS   =  9

# Initialize the display
OLED = OLED_1inch3(DC, RST, MOSI, SCK, CS)

# BPM280 pins (I2C - temperature and pressure sensor)
SCA  = Pin(0)
SCL  = Pin(1)

# Initialize BMP280
bus = I2C(0, scl=SCL, sda=SCA, freq=400000)
bmp = BMP280(bus)
bmp.use_case(BMP280_CASE_INDOOR) # Note: in WEATHER mode, no more then 1 sample per minute is allowed!

interrupt_flag = 0

class States():
	#TEMP           = 1
	#PRESSURE       = 2
	TEMP_PRESSURE  = 1
	TEMP_GRAPH     = 2
	PRESSURE_GRAPH = 3

# Set default state as startup
state = States.TEMP_PRESSURE

def splash():
	clear()

	font = Font_5x5()
	printString(10, 24, "BAROMETER", font, 2, OLED.white)
	printString(12, 40, "→ Made by Birki ←", font, 1, OLED.white)
	OLED.show()
	
def main():
	
	print("Starting...")

	count = 0
	temp_history  = []
	press_history = []

	if DEBUG:
		# Fill temp_history with random values where the next value is +- 1 from the previous value
		for i in range(128):
			if i == 0:
				temp_history.append(random.randint(15, 25))
			else:
				temp_history.append(temp_history[i-1] + random.choice([-2, 2]))

		# Fill press_history with random values where the next value is +- 1 from the previous value
		for i in range(128):
			if i == 0:
				press_history.append(random.randint(970, 1040))
			else:
				press_history.append(press_history[i-1] + random.choice([-2, 2]))

	while True:

		# Read temperature and pressure using BMP280 sensor
		current_temp = bmp.temperature
		current_press = int(bmp.pressure / 100)

		# Save temperature and pressure to history every 10 minutes
		if count % 60 == 0:
			
			temp_history.append(current_temp)
			if len(temp_history) > 128:
				temp_history.pop(0) # remove first item
			
			press_history.append(current_press)
			if len(press_history) > 128:
				press_history.pop(0) # remove first item

			count = 0

		# if state == States.TEMP:
		# 	showState_TEMP(current_temp)

		# if state == States.PRESSURE:
		# 	showState_PRESSURE(current_press)

		if state == States.TEMP_GRAPH:
			showState_TEMP_GRAPH(temp_history)

		if state == States.PRESSURE_GRAPH:
			showState_PRESSURE_GRAPH(press_history)

		if state == States.TEMP_PRESSURE:
			showState_TEMP_PRESSURE(current_temp, current_press)

		count += 1
		time.sleep(1)

def showState_PRESSURE_GRAPH(press_history):
	clear()
	
	scaler = (max(press_history) - min(press_history)) / 48
	min_press = min(press_history)

	for i in range(len(press_history)):
		# Scale the pressure to values between 8 and 54
		OLED.pixel(i, 55 - int((press_history[i] - min_press) * scaler), OLED.white)

	font = Font_5x5()

	# Header row
	printString(28, 0, "24h Pressure", font, 1, OLED.white)

	# Footer row
	printString(10, 59, "↓{:.0f}  →{:.0f}  ↑{:.0f}".format(min(press_history), press_history[-1], max(press_history)), font, 1, OLED.white)

	# Header/footer lines
	for x in range(128):
		if x % 4 == 0:
			OLED.pixel(x, 7, 1)
			OLED.pixel(x, 56, 1)

	OLED.show()

def showState_TEMP_GRAPH(temp_history):
	clear()

	for i in range(len(temp_history)):
		# Scale the temp to values between 8 and 54
		temp_scaled = (temp_history[i] * 48 / 42) + 8
		OLED.pixel(i, 64 - int(temp_scaled), OLED.white)

	font = Font_5x5()
	# Header row
	printString(19, 0, "24h Temperature", font, 1, OLED.white)
	
	# Footer row
	printString(4, 59, "↓{:.1f}  →{:.1f}  ↑{:.1f}".format(min(temp_history), temp_history[-1], max(temp_history)), font, 1, OLED.white)

	# Header/footer lines
	for x in range(128):
		if x % 4 == 0:
			OLED.pixel(x, 7, 1)
			OLED.pixel(x, 56, 1)

	OLED.show()

def showState_TEMP_PRESSURE(temperature, pressure):
	clear()

	temp = "{:.1f}".format(temperature, 1)
	press = "{:.0f}".format(pressure, 1)
	font = Font_5x5()

	printString(95-((len(temp)+1) * 15), 14, temp, font, 3, OLED.white)
	printString(95, 14, "°C", font, 1, OLED.white)

	printString(95-((len(press)+1) * 15), 34, press, font, 3, OLED.white)
	printString(95, 34, "hPa", font, 1, OLED.white)
	OLED.show()

def showState_PRESSURE(pressure):
	clear()

	press = "{:.0f}".format(pressure, 1)
	font = Font_5x5()

	printString(95-((len(press)+1) * 15), 24, press, font, 3, OLED.white)
	printString(95, 24, "hPa", font, 1, OLED.white)
	OLED.show()

def showState_TEMP(temperature):
	clear()

	temp = "{:.1f}".format(temperature, 1)
	font = Font_5x5()

	printString(95-((len(temp)+1) * 15), 24, temp, font, 3, OLED.white)
	printString(95, 24, "°C", font, 1, OLED.white)
	OLED.show()

# Print a string to the OLED display
# x, y: position on the display
# string: string to print
# font: font to use
# size: size of the characters
# color: color of the characters
def printString(x, y, string, font, size, color):
	for i in range(len(string)):
		printChar(x + i * 6 * size, y, font.characters[string[i]], size, color)


# Print a character to the OLED display
# x, y: position on the display
# char: character to print
# size: size of the character
# color: color of the character
def printChar(x, y, char, size, color):

	for i in range(len(char)): # height
		for j in range(len(char[i])): # width
			if char[i][j] == "1":
				OLED.fill_rect(x + j * size, y + i * size, size, size, color)
			else:
				OLED.fill_rect(x + j * size, y + i * size, size, size, OLED.black)

def keyA_pressed(pin):
	global state

	state += 1
	if state > 3:
		state = 1
	
	saveStateToFlash(state)

def keyB_pressed(pin):
	global state

	state -= 1
	if state <= 0:
		state = 3

	saveStateToFlash(state)

def saveStateToFlash(state):
	pass

def clear():
	OLED.fill(0x0000)

if __name__=='__main__':

	# Initialize keys
	keyA = Pin(15, Pin.IN, Pin.PULL_UP)
	keyB = Pin(17, Pin.IN, Pin.PULL_UP)

	# Create interrupt for keys
	keyA.irq(trigger=Pin.IRQ_FALLING, handler=keyA_pressed)
	keyB.irq(trigger=Pin.IRQ_FALLING, handler=keyB_pressed)
	
	splash()
	time.sleep(2.0)
	
	main()
