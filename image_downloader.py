import requests
import pandas as pd

df = pd.read_csv("C:/RScripts/Zillow Analysis/photo_links_to_download.csv")


for i in range(0, len(df)):
    name = df['id_hash'][i]
    filename = f'C:/RScripts/Zillow Analysis/Images/{name}.png'

    link = df['image_link'][i]

    try:
        r = requests.get(link)

        file = open(filename, "wb")
        file.write(r.content)
        file.close()
        print('Success')

    except:
        print(f'Didnt work on {name}')