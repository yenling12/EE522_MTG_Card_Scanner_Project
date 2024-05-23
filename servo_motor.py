# Import libraries
import RPi.GPIO as GPIO
import time
##########################################
# Initializations
# Set GPIO numbering mode based on GPIO pin
GPIO.setmode(GPIO.BCM)

sg90_pin = 12
fs90r_pin = 13
# Set pin 12 as an output
GPIO.setup(sg90_pin,GPIO.OUT)
# Set pin 13 as an output
GPIO.setup(fs90r_pin,GPIO.OUT)

motor_sg90 = GPIO.PWM(sg90_pin,50) # set pin as PWM. 50 = 50Hz pulse
motor_fs90r = GPIO.PWM(fs90r_pin,50)  # set pin as PWM. 50 = 50Hz pulse
##########################################
# Functions
def SetAngle_sg90(angle):
	'''
	Function for setting the SG90 Servo Motor angle.
    Angle range is 0 to 180 degrees.
	'''
	duty = angle / 18 + 2.5
	#GPIO.output(sg90_pin, True)
	print (f"rotating sg90 motor {angle} degrees..")
	motor_sg90.ChangeDutyCycle(duty)
	time.sleep(1)
	motor_sg90.ChangeDutyCycle(0)
	#GPIO.output(sg90_pin, False)
	print ("Done")

def Rotate_fs90r(angle, direction):
	'''
	Function for setting the FS90R Servo Motor angle.
    Angle range is 0 to 360 degrees. 
	Specify direction as 'CW' or 'CCW'.
	'''


##########################################
# Rotate FS90R Motor
motor_fs90r.start(0)
#SetAngle_fs90r(180, 'CW')
time.sleep(1)
motor_fs90r.ChangeDutyCycle(7.6)
time.sleep(1)
#SetAngle_fs90r(180, 'CW')
motor_fs90r.stop()

# Rotate SG90 Motor
motor_sg90.start(0)
SetAngle_sg90(0)
time.sleep(1)
SetAngle_sg90(90)
motor_sg90.stop()

# #Clean things up at the end
GPIO.cleanup()

