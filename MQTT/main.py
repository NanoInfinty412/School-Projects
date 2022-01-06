from PIL import Image
from tflite_runtime.interpreter import Interpreter
from urllib import request
import datetime
import io
import csv
import numpy as np
import os
import paho.mqtt.client as mqtt_client
import picamera
import re
import sys
import time

CAMERA_WIDTH = 500
CAMERA_HEIGHT = 500
THRESHOLD = 0.6

MODEL_PATH = os.sep.join([os.getcwd(), "detect.tflite"])
LABELS_PATH = os.sep.join([os.getcwd(), "coco_labels.txt"])
FILE_NAME = os.sep.join([os.getcwd(), "history.csv"])

def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels


def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor


def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  timestamp = str(datetime.datetime.now()).split(".")[0]
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i],
          'timestamp': timestamp,
      }
      results.append(result)
  return results

# on connetc indication of the client
def on_connect(client, userdata, flags, rc):
    if(rc == 0):
        print("Connection success")
    else:
        print("Connection failed")

# function to check if pi is connected to internert
def connected_to_internet(host="http://google.com"):
    try:
        request.urlopen(host)
        return True
    except:
        return False

def write(info):
    with open(FILE_NAME, "a+") as fout:
        write = csv.writer(fout)
        write.writerows(info)

def read():
    data = []
    with open(FILE_NAME, "r") as fout:
        reader = csv.reader(fout)
        for row in reader:
            data.append(row)
    return data

def main():
    
    # set up mqtt publisher role
    publisher = mqtt_client.Client()
    publisher.on_connect = on_connect
        
    # load coco labels
    labels = load_labels(LABELS_PATH)
    
    # load interpreter
    interpreter = Interpreter(MODEL_PATH)
    interpreter.allocate_tensors()
    
    shape_dimensions = interpreter.get_input_details()[0]['shape']
    
    height, width = shape_dimensions[1], shape_dimensions[2]
    
    # keep track if historical data exists
    HISTORICAL_DATA = False
    
    # set up PI camera
    with picamera.PiCamera(
        resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30
    ) as camera:
        camera.rotation = 180
        
        # start camera
        camera.start_preview()
        # store each continous capture in memory for faster computation
        stream = io.BytesIO()
        
        counter = 0
        
        for capture in camera.capture_continuous(stream, format="jpeg", use_video_port=True):
            stream.seek(0)
            image = Image.open(stream).convert("RGB").resize(
                (height, width), Image.ANTIALIAS)
            # call detect objects
            results = detect_objects(interpreter, image, THRESHOLD)
            out = []
            # make sure results are not empty
            if len(results) > 0:
                for result in results:
                    temp = [
                        'timestamp' + ": " + result['timestamp'],
                        'class_id' + ": " + labels[result['class_id']],
                    ]
                    out.append(temp)
                if connected_to_internet():
                    publisher.connect("broker.emqx.io", 1883, 60)
                    if HISTORICAL_DATA:
                        # maintain the time stamp order if historical data exists
                        data = read()
                        for i in out:
                            data.append(i)
                        out = data
                        
                        # clear file contents since everything will be published
                        f = open(FILE_NAME, "w+")
                        f.close()
                    
                    HISTORICAL_DATA = False
                    for i in out:
                        publisher.publish('raspberry/meta', payload=str(i), qos=0, retain=False)
                        print("sent ", i, " to raspberry/temp")
                else:
                    print("Not connected to internet")
                    HISTORICAL_DATA = True
                    write(out)
            out.clear()
            stream.seek(0)
            stream.truncate()
            time.sleep(3)
            counter += 1
            if counter == 20:
                break;
        
    return 0
    
    
if __name__ == "__main__":
    sys.exit(main())
