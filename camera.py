# camera.py
################################################
# Import Libraries
import time
from picamera2 import Picamera2, Preview
###############################################
picam2 = Picamera2() 

# Configure camera for preview mode
preview_config = picam2.create_preview_configuration() 
# Configure camera for still capture
capture_config = picam2.create_still_configuration(raw={}, display=None) 
picam2.align_configuration(preview_config)
picam2.configure(preview_config) 

#Start preview for X forwarding
picam2.align_configuration(capture_config)
picam2.start_preview(Preview.QT) 
picam2.start() 
time.sleep(8)   #8 seconds
#picam2.stop_()

# Reconfigure camera for still capture

#picam2.configure(camera_config) 
#picam2.switch_mode_and_capture_file(capture_config, "test1.jpg")
r = picam2.switch_mode_capture_request_and_stop(capture_config)
# Capture photo and save it
#picam2.start() 
#time.sleep(2) 
#picam2.capture_file("test1.jpg")
r.save("main", "test2.jpg")
#r.save_dng("test1.dng")
picam2.stop_()