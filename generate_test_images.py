import os
import shutil
import re

# Housing Data set at https://github.com/emanhamed/Houses-dataset

source = "C:/RScripts/Zillow Analysis/Houses-dataset/Houses Dataset"
destination = "C:/RScripts/Zillow Analysis/Lancaster-County-Home-Values/Training Images"

files = os.listdir(source)

for file in files:
    if re.findall(r"frontal", str(file)):
        shutil.move(f"{source}/{file}", destination)

training_imgs = os.listdir(destination)
print(f"Finished on {len(training_imgs)} images")