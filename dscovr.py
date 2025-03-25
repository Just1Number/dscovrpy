#!/usr/bin/python3
import argparse
import json
from datetime import datetime, UTC
from datetime import timedelta
from os import rename, remove, getcwd, path, name
from glob import glob
from shutil import copyfile
from urllib.request import urlopen, urlretrieve
from PIL import Image
import cv2 as cv
import numpy as np

# Constants
API_URL_BASE = "https://epic.gsfc.nasa.gov/api/natural/date/"
IMAGE_SOURCE = "https://epic.gsfc.nasa.gov/archive/natural/"

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-o", dest = "output_dir", help = "set output directory", default = getcwd()) # location of the script: default = path.dirname(path.realpath(__file__))
  parser.add_argument("-n", dest = "pics_per_day", type = int, help = "use a day with at least PICS_PER_DAY pictures", default = 1)
  parser.add_argument("-b", dest = "background", help = "circle crop image onto background", default = "")
  parser.add_argument("-c", dest = "clean_output", help = "wether or not to clean the output dir", action = 'store_true')
  args = parser.parse_args()

  if args.pics_per_day > 24:
    print("There are no days with this many pictures. Setting n to 24")
    args.pics_per_day = 24

  if not path.isdir(args.output_dir):
    print("Output directory '" + args.output_dir + "' invalid. Check if it exists")
    exit(1)

  if args.clean_output:
    epic_clean(args.output_dir)

  image_name, image_url = epic_find(args.pics_per_day)

  epic_download(args.output_dir, image_name, image_url)

  # crop image
  if args.background != "":
    epic_crop(args.output_dir, image_name, args.background)
  
  epic_finalize(args.output_dir, image_name)

  print(image_name + " downloaded")

def epic_find(pics_per_day):
  # EPIC is out of order, so old images from 2018 are used
  dtnow = datetime.now(UTC)#.replace(year=2018)
  api_url = API_URL_BASE + dtnow.strftime("%Y-%m-%d")
  # https://epic.gsfc.nasa.gov/api/natural/date/2018-06-30

  # Parsing api 
  contents = bytes(0)
  try:
    contents = urlopen(api_url).read()
  except Exception as e:
    print("Cannot connect to API at " + api_url)
    print("Check your internet connection")
    print(e)
    exit(1)
  data = json.loads(contents.decode('utf-8'))

  # If there are to few images per day use a previous day, that has more
  # Cancel search after 10 days
  d = dtnow.date()
  i = 0
  while len(data) < pics_per_day:
    if i == 10:
      if pics_per_day == 1:
        print("The last 10 days don't contain any pictures. Check " + API_URL_BASE)
        exit(1)
      print("None of the last 10 days had at least " + str(pics_per_day) + " pictures. Trying again with " + str(pics_per_day - 1))
      d = dtnow.date()
      pics_per_day -= 1
      i = 0
      continue
    i += 1
    # go back one day
    d -= timedelta(1)
    api_url = API_URL_BASE + d.strftime("%Y-%m-%d")
    try:
      contents = urlopen(api_url).read()
    except Exception as e:
      print("Cannot connect to API at " + api_url)
      print(e)
      exit(1)
    data = json.loads(contents.decode('utf-8'))

  image_times = []
  # Fill image_times with all timestamps of the chosen day
  for meta in data:
    # convert json date into python time object, ignoring the date
    t = datetime.strptime(meta['date'], "%Y-%m-%d %H:%M:%S").time()
    # set date to today
    dt = datetime.combine(dtnow.date(), t)
    # return to timestamp
    ts = dt.timestamp()
    image_times.append(ts)

  tsnow = dtnow.timestamp()
  additional_data = []
  early = False
  late = False
  # handle the special case of tsnow being in between the last and the first image of the day
  if tsnow < min(image_times):
    # if tsnow is before the first timestamp:
    # load last image of previous day, if possible
    d -= timedelta(1)
    early = True

  elif tsnow > max(image_times):
    # if tsnow is after the last timestamp:
    # load first image of next day, if possible
    d += timedelta(1)
    late = True

  if early or late:
    api_url = API_URL_BASE + d.strftime("%Y-%m-%d")
    try:
      contents = urlopen(api_url).read()
      additional_data = json.loads(contents.decode('utf-8'))
    except Exception as e:
      print("Cannot connect to API at " + api_url)
      print(e)

    if len(additional_data) > 0:
      # add one image to data
      if early:
        data.append(additional_data[len(additional_data) - 1])
      elif late:
        data.append(additional_data[0])
      # append additional image's timestamp to image_times
      # convert json date into python time object, ignoring the date
      t = datetime.strptime(data[len(data) - 1]['date'], "%Y-%m-%d %H:%M:%S").time()
      # set date to today
      dt = datetime.combine(dtnow.date(), t)
      # return to timestamp
      if early:
        ts = dt.timestamp() - (24 * 3600)
      elif late:
        ts = dt.timestamp() + (24 * 3600)
      image_times.append(ts)

  diffs = []
  for ts in image_times:
    diff = abs( tsnow - ts )
    diffs.append(diff)

  # choosing image by index. picking a picture taken close to the current daytime
  index = diffs.index(min(diffs))
  image_name = data[index]['image'] + '.png' # epic_1b_20180630224431.png
  image_id = data[index]['identifier'] # 20180630224431
  image_url = IMAGE_SOURCE + image_id[:4] + "/" + image_id[4:6] + "/" + image_id[6:8] + "/png/" + image_name
  # https://epic.gsfc.nasa.gov/archive/natural/2018/06/30/png/epic_1b_20180630224431.png

  return image_name, image_url

def epic_download(download_directory, image_name, image_url):
  # check if metadata file exists
  metadata = path.join(download_directory, "image_info.epic")
  if path.exists(metadata):
    # read filename of last image 
    # and skip download if it is the same as the current one
    rf = open(metadata, "r")
    old_image = rf.read()
    rf.close()
    if old_image == image_name:
      print(image_name + " is already on local machine. Skipping download.")
      exit()

  image_path = path.join(download_directory, image_name)
  # Download image
  try:
    urlretrieve(image_url, image_path)
  except Exception as e:
    print("Download failed")
    print(image_url + image_name)
    print(e)
    exit(1)

  # write current image_name to the metadata file
  wf = open(metadata, "w")
  wf.write(image_name)
  wf.close()

def epic_crop(download_directory, image_name, background):

  image_path = path.join(download_directory, image_name)

  # Open image with openCV
  img = cv.imread(image_path)

  # Get mask of everything which is not black
  lower = np.array([0,0,1]) # almost black
  upper = np.array([255,255,255]) # white
  shapeMask = cv.inRange(img, lower, upper)
  alpha_np = shapeMask.copy()

  # Open image with PIL
  img = Image.open(image_path)

  img_np = np.array(img)
  img_np = np.dstack((img_np,alpha_np))
  img = Image.fromarray(img_np)

  try:
    img_bg = Image.open(background)
  except Exception as e:
    print("Adding background failed")
    print(e)
    return

  # Get size of epic image
  w, h = img.size #2048x2048
  # Resize background to to height of epic image
  w_bg, h_bg = img_bg.size
  if (h_bg != h):
    # calculate new width so height can be 2048 (epic image height)
    w_bg = int(w_bg * (h/h_bg))
    img_bg = img_bg.resize((w_bg,h))

  # Paste epic on background
  pos_x = (w_bg - w) / 2
  img_bg.paste(img, (int(pos_x),0), mask=img)
  img_bg.save(image_path)

def epic_finalize(download_directory, image_name):
  # move downloaded image to final path
  image_path = path.join(download_directory, image_name)
  final_path = path.join(download_directory, 'epic.png')
  if path.exists(final_path):
    remove(final_path) # needed for windows only
  rename(image_path, final_path)

  # Create a copy of the image for a diashow under windows
  if name == "nt":
    final_path_copy = path.join(download_directory, 'epic_copy.png')
    if path.exists(final_path_copy):
      remove(final_path_copy) # Windows only
    copyfile(final_path, final_path_copy)

def epic_clean(download_directory):
  file_pattern = path.join(download_directory, 'epic_1b_*.png')
  file_list = glob(file_pattern)
  for file_path in file_list:
    try:
      remove(file_path)
    except:
      print('Could not delete ', file_path)

if __name__ == "__main__":
  main()
