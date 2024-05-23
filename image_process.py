# Image process
##########################################
# Import libraries
import numpy as np
import cv2
import os
from PIL import Image
import pytesseract
from pytesseract import Output
import requests 
import re # regular expression operations
##########################################
# Initialization
#pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) 
##########################################
# Functions
def get_text(img):
    '''This will extract any text using pytesseract from 
       the processed image.    
    '''
    # cv2.imwrite('neg_img_rgb_inrange.png', neg_rgb_image)
    data = pytesseract.image_to_string(img, lang='eng')
    print(data)
    return data

def replace_o_with_zero(string):
  """Replaces all "O" characters with "0" in a string.

  Args:
    string: The input string.

  Returns:
    The modified string with "O" replaced by "0".
  """
  new_string = re.sub(r"O", "0", string, flags=re.IGNORECASE)
  return re.sub(r"O", "0", string)

def extract_card_id_set(text):
    '''This will extract the card id and 
       card set from the tesseract results.
       E.g. 134/281
            DMU -EN
        card_id=134, card_set=DMU
    '''
    # Extract MTG Card ID before the first "/"
    card_id = text.split("/")[0].strip()
    card_id = replace_o_with_zero(card_id)
    card_id = int(card_id)

    # Extract the card set
    card_set = text.split("\n")[1].split(" ")[0]
    print('card_set:', card_set)
    return card_id, card_set

def get_card_title_price(id, set):
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

##########################################
# Using cv2.imread() method
img = cv2.imread("test2.jpg")
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
cropped_image = img_gray[1600:1800, 600:900]

# Save cropped image
cv2.imwrite('croppedimg.jpg', cropped_image) 

# Change image to black and white
lower = 150
upper = 230
img_rgb_inrange = cv2.inRange(cropped_image, lower, upper)
neg_rgb_image = ~img_rgb_inrange

cv2.imwrite('bw_image.jpg', neg_rgb_image) 
# Grab text data
text = get_text(neg_rgb_image)

# From text, grab ID and Card Set
card_id, card_set = extract_card_id_set(text)

# Call Scryfall API to determine title and prices
data = get_card_title_price(card_id, card_set)

# card_name = data["data"][0]["name"]
# usd_price = data["data"][0]["prices"]["usd"]
# usd_foil_price = data["data"][0]["prices"]["usd_foil"]

# print(f'card title: {card_name}; price is {usd_price} usd and {usd_foil_price} foil usd')