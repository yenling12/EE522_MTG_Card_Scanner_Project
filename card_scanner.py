
##########################################
# Import libraries
import RPi.GPIO as GPIO
import time
from picamera2 import Picamera2
import numpy as np
import cv2
import os
import pytesseract
from pytesseract import Output
import requests 
import re # Regular expression
import csv
import subprocess
##########################################
# Initializations
# Set GPIO numbering mode based on GPIO pin
GPIO.setmode(GPIO.BCM)
# Set Motor Pins
fs90r_pin = 13
sg90_pin = 12
# Set pin 13 as an output
GPIO.setup(fs90r_pin,GPIO.OUT)
# Set pin 12 as an output
GPIO.setup(sg90_pin,GPIO.OUT)
# Set up Camera
picam2 = Picamera2()
capture_config = picam2.create_still_configuration(raw={}, display=None) 
picam2.configure(capture_config) 
# Initialize variables for file
##########################################
# Functions
def rotate_fs90r(pin):
    '''
    Sets the FS90R Servo Motor. Range is 
    0 to 360 degrees. Rotates motor CCW for
    1 sec, then rotates CW for 0.5 sec.
    Args: pin
    Returns: none
    '''
    # set pin as PWM. 50 = 50Hz pulse
    motor_fs90r = GPIO.PWM(pin,50)
    # Rotate FS90R Motor
    motor_fs90r.start(0)
    time.sleep(0.5)
    # Rotate motor to push out card
    motor_fs90r.ChangeDutyCycle(7.6)
    time.sleep(1.2)
    # Reverse motor to pull back previous card
    motor_fs90r.ChangeDutyCycle(6.5)
    time.sleep(0.8)
    motor_fs90r.stop()

def setangle_sg90(angle, motor_PWM):
    '''
    Sets the SG90 Servo Motor angle.
    Angle range is 0 to 180 degrees.
    Args: angle, motor_PWM
    Returns: none
    '''
    motor_sg90 = motor_PWM
    duty = angle / 18 + 2.5
    print (f"rotating sg90 motor {angle} degrees..")
    motor_sg90.ChangeDutyCycle(duty)
    time.sleep(0.5)
    motor_sg90.ChangeDutyCycle(0)
    
def rotate_sg90(pin):
    '''
    Rotates the SG90 motor to 0 degrees, then back 
    to 90 degrees (its reset position)
    Args: pin
    Returns: none
    '''
    motor_sg90 = GPIO.PWM(pin,50) # set pin as PWM. 50 = 50Hz pulse
    motor_sg90.start(0)
    setangle_sg90(0, motor_sg90)
    time.sleep(0.7)
    setangle_sg90(90, motor_sg90)
    motor_sg90.stop()
    print ("sg90 Done")

def process_image(img,count):
    '''
    Processes the inputted image for text extraction. 
    Rotates the image, converts the image to grayscale,
    blurs the image, sharpens it, crops the 
    image to isolate the text of interest, then puts a
    mask over the image to accentuate the text.
    Args: img
    Returns: Processed Image
    '''
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Rotate image
    img_rgb = cv2.rotate(img_rgb, cv2.ROTATE_180)

    # Convert image to grayscale
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Blur image. Remove noise using a Gaussian filter 
    img_blur = cv2.GaussianBlur(img_gray, (7, 7), 0) 

    # Sharpen the image
    img_gray = cv2.filter2D(img_blur, -1, kernel) 

    # Crop image to grab Ids
    cropped_image = img_gray[1690:1820, 600:900]

    # Save cropped image
    cv2.imwrite(f'./cropped_image/cropped_img_{count}.jpg', cropped_image) 

    # Change image to black and white
    # Day Time 160-260
    # Night Time 100-200
    lower = 100
    upper = 200
    img_inrange = cv2.inRange(cropped_image, lower, upper)
    neg_img = ~img_inrange

    cv2.imwrite(f'./bw_image/bw_image_{count}.jpg', neg_img) 

    return neg_img

def get_text(img):
    '''
    Extracts any text using pytesseract from 
    the processed image.  
    Args: img
    Returns: Data outputted by pytesseract
    '''
    data = pytesseract.image_to_string(img, lang='eng')
    print(data)
    return data

def process_string(string):
    """
    Replaces all "O" characters with "0" in a string
    regardless of case.
    Args: string
    Returns: The modified string with "O" replaced by "0".
    """
    new_string = re.sub(r"O", "0", string, flags=re.IGNORECASE)

    # Remove any erroneous characters after the first 3 chars
    if len(string) > 3:
        new_string = new_string[:3]
    return new_string

def check_id_valid(string):
    '''
    Checks if all chars in the string ar digits.
    Args: string
    Returns: True if all chars are digits. False otherwise.
    '''
    # Check if chars are digits
    isNum = all(char.isdigit() for char in string)

    if isNum and len(string) == 3:
        return True
    else:
        return False

def extract_card_id_set(text):
    '''
    Extracts the card id and card set from
    the tesseract results.
    E.g. 134/281
         DMU -EN
    card_id=134, card_set=DMU
    Args: text
    Returns: status, card_id, card_set, isFoil
    '''
    status = "N/A"
    isFoil = False
    # Extract MTG Card ID on the first line
    card_id = text.split("\n")[0].strip()
    # Check to see if there is a '/'. Foil cards do not have a '/'
    if re.search('/', card_id):
        card_id = card_id.split('/')[0]
    else:
        isFoil = True

    # Replace "O" and "o" with "0"
    card_id = process_string(card_id)
    # Check if all chars in card_id are digits
    id_valid = check_id_valid(card_id)
    #print('id_is_digits: ', id_is_digits)

    # Extract the MTG card set
    card_set = text.split("\n")[1].split(" ")[0]
    # If card_set length is greater than 3, extract first 3 characters
    if len(card_set) > 3:
        card_set = card_set[:3]

    if id_valid and len(card_set) == 3:
        # Convert ID to int type to remove any leading zeros
        card_id = int(card_id)
        print('card_id:', card_id)
        print('card_set:', card_set)
        status = 'success'
    elif not id_valid and len(card_set) == 3:
        status = 'Issue with Card ID'
    elif id_valid and len(car_set) != 3:
        # Convert ID to int type to remove any leading zeros
        card_id = int(card_id)
        status = 'Issue with Card Set'
    return status, card_id, card_set, isFoil

def get_card_data(id, set):
    # Create API info to search on 
    info = {
    "identifiers": [
        {
        "set": set,
        "collector_number": str(id)
        }
    ]
    }

    # POST API URL
    url = "https://api.scryfall.com/cards/collection"

    # Send Request
    response = requests.post(url, json=info)

    # Handle response
    if response.status_code == 200:
        print("Request successful!")
        data = response.json()
        if not data["data"]:
            return 0
        else:
            return data["data"]
    else:
        print(f"Error: {response.status_code}")
        print(response)
        return 0

def empty_folder(folder_path):
    '''
    Clears out image folders.
    Args: folder_path
    Returns: none
    '''
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)
    print(f"{folder_path} emptied successfully!")

def get_cpu_temp():
  """Gets the CPU temperature of the Raspberry Pi using vcgencmd."""
  output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
  temp = float(output.split("=")[1].split("'")[0])
  return temp
##########################################
# Create new card.csv file with headers
with open('card.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Text_Extract_Status','Card_ID','Card_Set','Card_Data','Card_Name','Card_Price_USD','Card_Price_Foil_USD','is_Foil'])
    print('card.csv created')

# Empty folders
bw_image_path = './bw_image'
cropped_image_path = './cropped_image'
empty_folder(bw_image_path)
empty_folder(cropped_image_path)

# Intialize count for scan cycle
count = 20
cpu_temp = get_cpu_temp()
print(f"CPU temperature at start: {cpu_temp:.1f}°C")
start_time = time.time()  # Capture start time
while count > 0:
    # re-Intialize variables
    data = ''
    card_name = ''
    usd_price = ''
    usd_foil_price = ''
    # Rotate fs90r motor to push out card
    rotate_fs90r(fs90r_pin)

    # # Capture card image
    picam2.start(show_preview=False)
    time.sleep(1)
    picam2.capture_file("test.jpg")
    picam2.stop_()

    # Read and process image
    image = cv2.imread("test.jpg")
    img_processed = process_image(image,count)

    # Extract text from image
    text = get_text(img_processed)
    print('text: ', text)

    # Get ID and Set from extracted text
    status, id, set, isFoil = extract_card_id_set(text)

    # Drop card in preparation for next card
    rotate_sg90(sg90_pin)

    if status == 'success':
        # Get card data
        data = get_card_data(id, set)

        # If card data is found, get Card Name and Price
        if data != 0:
            card_name = data[0]["name"]
            usd_price = data[0]["prices"]["usd"]
            usd_foil_price = data[0]["prices"]["usd_foil"]
            print(f'card title: {card_name}; price is {usd_price} usd, {usd_foil_price} usd_foil')
        else:
            status = 'no data found'

    # Write card information to card.csv
    with open('card.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([status, id, set, data, card_name, usd_price, usd_foil_price, isFoil])
    
    count -= 1

end_time = time.time()  # Capture end time
elapsed_time = end_time - start_time
print("Elapsed time:", elapsed_time, "seconds")

cpu_temp = get_cpu_temp()
print(f"CPU temperature at end: {cpu_temp:.1f}°C")

# #Clean things up at the end
GPIO.cleanup()



