# -*- coding: utf-8 -*-
"""Untitled17.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1I4bhfqLsI2I9mnGatQgVoC2BUIHctAYn
"""

api_key = "e776bad00239d4b5e7ae48e89d05c1ff70f60db2606328eba1e21b0a747bbeac"
api_url = "https://api-us.restb.ai/vision/v2/predict"

import time
import requests
import pandas as pd

data = pd.read_csv("/content/photo_links_to_download.csv").dropna()

image_store = []
for link in data['image_link'].drop_duplicates():
  time.sleep(2)

  payload = {
    # Add your client key
    'client_key': api_key,
    'model_id': 're_styles',
    # Add the image URL you want to classify
    'image_url': link
  }

  try:
    response = requests.get(api_url, params=payload)
    json_response = response.json()
    top_pred = json_response['response']['solutions']['re_styles']['top_prediction']
    top_pred['link'] = link
    image_store.append(top_pred)
    print('Success')

  except:
    print(f'Didnt Work on {link}')

final_df = pd.DataFrame(image_store)
final_df.to_csv("house_img_details_restbapi.csv")