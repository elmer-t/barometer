from oled import OLED_1inch3
from bmp280 import *
from machine import Pin, I2C

from font_5x5 import Font_5x5
import time
import random
import math

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

font             = Font_5x5()
interrupt_flag   = 0		# Interrupt flag for button press
temp_history     = []       # Temperature history
press_history    = []       # Pressure history
sample_int_secs  = 60       # Sample interval in seconds
temp_calibration = -0.9     # Temperature calibration value
pressure_calibration = 0    # Pressure calibration value

class DisplayModes():
	TEMP_PRESSURE  = 1
	TEMP_GRAPH     = 2
	PRESSURE_GRAPH = 3

HourRanges = [4, 8, 12, 24, 48]

# Set default display settings as startup
display_mode = DisplayModes.TEMP_GRAPH
hour_range = 0 # default to 4h

def splash():
	clear()

	printString(10, 24, "BAROMETER", font, 2, OLED.white)
	printString(12, 40, "→ Made by Birki ←", font, 1, OLED.white)
	OLED.show()

def dummy_data():
	global temp_history, press_history

	print("Filling dummy data...")

	temp_history   = []
	press_history  = []

	# Fill temp_history with random values where the next value is +- 1 from the previous value
	for i in range(48 * 60): # 2880 minutes/measuring points in 48 hours
		if i == 0:
			temp_history.append(15.0)
		else:
			temp_history.append(temp_history[i-1] + random.choice([-1, 1]))

		#temp_history.append(math.sin(i))

	# Fill press_history with random values where the next value is +- 1 from the previous value
	for i in range(48 * 60): # 2880 minutes/measuring points in 48 hours
		if i == 0:
			press_history.append(random.randint(970, 1040))
		else:
			press_history.append(press_history[i-1] + random.choice([-2, 2]))

	# # real-world temperature measurements
	# temp_history = [18.69, 18.68, 18.68, 18.68, 18.69, 18.68, 18.68, 18.71, 18.78, 18.84, 18.92, 19.0, 19.07, 19.14, 19.2, 19.25, 19.31, 19.32, 19.3, 19.36, 19.42, 19.38, 19.36, 19.39, 19.37, 19.36, 19.35, 19.35, 19.34, 19.34, 19.33, 19.32, 19.32, 19.3, 19.29, 19.28, 19.27, 19.26, 19.25, 19.26, 19.25, 19.26, 19.26, 19.26, 19.27, 19.26, 19.25, 19.25, 19.51, 19.5, 19.54, 19.54, 19.76, 19.78, 19.8, 21.22, 20.79, 20.73, 20.73, 20.7, 20.67, 20.63, 20.59, 20.55, 20.49, 20.44, 20.39, 20.34, 20.3, 20.25, 20.22, 20.18, 20.14, 20.1, 20.06, 20.03, 20.0, 19.96, 19.93, 19.9, 19.88, 19.85, 19.83, 19.81, 19.79, 19.77, 19.75, 19.72, 19.7, 19.68, 19.66, 19.63, 19.61, 19.6, 19.58, 19.57, 19.55, 19.53, 19.52, 19.5, 19.49, 19.47, 19.46, 19.45, 19.43, 19.42, 19.41, 19.4, 19.38, 19.37, 19.35, 19.35, 19.34, 19.32, 19.31, 19.3, 19.3, 19.28, 19.27, 19.25, 19.25, 19.24, 19.23, 19.23, 19.22, 19.21, 19.19, 19.19, 19.18, 19.17, 19.17, 19.16, 19.15, 19.15, 19.14, 19.13, 19.13, 19.13, 19.12, 19.11, 19.11, 19.11, 19.1, 19.09, 19.09, 19.08, 19.07, 19.06, 19.06, 19.06, 19.05, 19.04, 19.04, 19.03, 19.03, 19.02, 19.02, 19.02, 19.01, 19.0, 19.0, 18.99, 18.99, 18.98, 18.98, 18.98, 18.97, 18.96, 18.97, 18.96, 18.96, 18.96, 18.94, 18.94, 18.94, 18.94, 18.93, 18.93, 18.93, 18.93, 18.92, 18.92, 18.92, 18.92, 18.91, 18.91, 18.91, 18.92, 18.92, 18.91, 18.91, 18.9, 18.9, 18.9, 18.89, 18.89, 18.89, 18.88, 18.88, 18.88, 18.87, 18.88, 18.88, 18.88, 18.88, 18.88, 18.87, 18.86, 18.86, 18.87, 18.86, 18.86, 18.86, 18.85, 18.85, 18.85, 18.85, 18.85, 18.85, 18.85, 18.85, 18.84, 18.84, 18.84, 18.84, 18.84, 18.84, 18.83, 18.83, 18.83, 18.83, 18.83, 18.82, 18.83, 18.82, 18.82, 18.82, 18.82, 18.82, 18.81, 18.81, 18.81, 18.81]

def main():
	global temp_history, press_history

	print("Starting...")
	count = 0

	# On first start, fill the history with the current temperature and pressure
	temp_history  = [bmp.temperature + temp_calibration] * 48 * 60
	press_history = [int((bmp.pressure + pressure_calibration) / 100)] * 48 * 60
	
	if DEBUG:
		dummy_data()

	while True:

		# Read temperature and pressure using BMP280 sensor
		current_temp = bmp.temperature + temp_calibration
		current_press = int((bmp.pressure + pressure_calibration) / 100)

		# Save the temperature and pressure to the history every 60 seconds
		if DEBUG == False and count % sample_int_secs == 0:

			temp_history.append(current_temp)
			if len(temp_history) > 48 * 60:
				temp_history.pop(0) # remove first item
			
			press_history.append(current_press)
			if len(press_history) > 48 * 60:
				press_history.pop(0) # remove first item

			count = 0

		if display_mode == DisplayModes.TEMP_GRAPH:
			showState_GRAPH(temp_history, "Temperature", True)

		if display_mode == DisplayModes.PRESSURE_GRAPH:
			showState_GRAPH(press_history, "Pressure")

		if display_mode == DisplayModes.TEMP_PRESSURE:
			showState_TEMP_PRESSURE(current_temp, current_press)

		count += 1
		time.sleep(1) # must be 1 or less for button interrupts to work

def showState_GRAPH(history, title, show_decimals = False):
	clear()

	min_y = 8
	max_y = 55
	y_range = max_y - min_y
	
	# sample_size is the number of measuring point we want to display on the screen
	sample_size = HourRanges[hour_range] * 60 #sample_interval_seconds

	# When calculating the average, we want to group the measuring points into chunks
	# and calculate the average of each chunk. The chunk size is calculated so that
	# the number of chunks is equal to the width of the display (128 pixels)
	chunk_size = sample_size // 120 # 128 is the available width of the display
	if chunk_size == 0:
		chunk_size = 1

	# Calculate the average of the last sample_size measuring points
	averaged_temp_history = []
	for i in range(len(history)-chunk_size, len(history)-chunk_size - sample_size, -chunk_size):
		averaged_temp_history.append(
			sum(history[i:i + chunk_size]) / chunk_size
		)
	# Reverse the list so that the oldest values are first
	averaged_temp_history.reverse()

	min_temp = min(averaged_temp_history)
	max_temp = max(averaged_temp_history)
	temp_range = max_temp - min_temp
	if temp_range == 0:
		temp_range = 1

	for i in range(len(averaged_temp_history)):
		temp_scaled = (averaged_temp_history[i] - min_temp) * y_range / temp_range + min_y
		OLED.line(i+4, max_y, i+4, 64 - int(temp_scaled), OLED.white)

	# Header row
	printString(19, 0, str(HourRanges[hour_range]) + "h " + title, font, 1, OLED.white)
	hor_dotted_line(6)
	
	# Footer row
	if show_decimals:
		printString(4, 59, "↓{:.1f}  →{:.1f}  ↑{:.1f}".format(min_temp, history[-1], max_temp), font, 1, OLED.white)
	else:
		printString(4, 59, "↓{:.0f}  →{:.0f}  ↑{:.0f}".format(int(min_temp), history[-1], int(max_temp)), font, 1, OLED.white)
	hor_dotted_line(56)

	# Vertical dotted lines
	vert_dotted_line(0)
	vert_dotted_line(1)
	vert_dotted_line(2)

	vert_dotted_line(32)
	vert_dotted_line(64)
	vert_dotted_line(96)

	vert_dotted_line(125)
	vert_dotted_line(126)
	vert_dotted_line(127)

	OLED.show()

def showState_TEMP_PRESSURE(temperature, pressure):
	clear()

	temp = "{:.1f}".format(temperature, 1)
	press = "{:.0f}".format(pressure, 1)

	printString(95-((len(temp)+1) * 15), 14, temp, font, 3, OLED.white)
	printString(95, 14, "°C", font, 1, OLED.white)

	printString(95-((len(press)+1) * 15), 34, press, font, 3, OLED.white)
	printString(95, 34, "hPa", font, 1, OLED.white)
	OLED.show()

# Print a horizontal dotted line
def hor_dotted_line(y = 0):
	for x in range(127):
		if x % 4 == 0:
			OLED.pixel(x, y, 1)
			OLED.pixel(x, y, 1)

# Print a vertical dotted line
def vert_dotted_line(x = 0):
	for y in range(51):
		if y % 10 == 0:
			OLED.pixel(x, y+6, 1)
			OLED.pixel(x, y+6, 1)

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

def key_0_pressed(pin):
	global display_mode

	display_mode += 1
	if display_mode > 3:
		display_mode = 1

def key_1_pressed(pin):
	global hour_range

	hour_range += 1
	if hour_range > 4:
		hour_range = 0

def clear():
	OLED.fill(0x0000)

if __name__=='__main__':

	# Initialize keys
	key_0 = Pin(15, Pin.IN, Pin.PULL_UP)
	key_1 = Pin(17, Pin.IN, Pin.PULL_UP)

	# Create interrupt for keys
	key_0.irq(trigger=Pin.IRQ_FALLING, handler=key_0_pressed)
	key_1.irq(trigger=Pin.IRQ_FALLING, handler=key_1_pressed)
	
	splash()
	time.sleep(2.0)
	
	main()
