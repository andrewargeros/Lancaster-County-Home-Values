# -*- coding: utf-8 -*-
"""CleanZillowScrape.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lcc8NqFtRLBe-jqFCFHWSyrcXtdu8rfc
"""

# !pip install unicodecsv

# Commented out IPython magic to ensure Python compatibility.
from lxml import html
import requests
import unicodecsv as csv
import argparse
import json
import uuid
import pandas as pd
import time
import itertools

def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None


def get_headers():
    # Creating headers.

  useragent = str(uuid.uuid4())

  headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
              'accept-encoding': 'gzip, deflate, sdch, br',
              'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
              'cache-control': 'max-age=0',
              'upgrade-insecure-requests': '1',
              'user-agent': f'Mozilla/5.0 (X11; Linnux x86_64) AppleWebKit/537.36 (KHTML, like) Chrome/74.0.3729.131 Safari/{useragent}'}
  return headers


def create_url(zipcode, filter):
    # Creating Zillow URL based on the filter.

    if filter == "newest":
        url = "https://www.zillow.com/homes/for_sale/{0}/0_singlestory/days_sort".format(zipcode)
    elif filter == "cheapest":
        url = "https://www.zillow.com/homes/for_sale/{0}/0_singlestory/pricea_sort/".format(zipcode)
    else:
        url = "https://www.zillow.com/homes/for_sale/{0}_rb/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy".format(zipcode)
    print(url)
    return url


def save_to_file(response):
    # saving response to `response.html`

    with open("response.html", 'w') as fp:
        fp.write(response.text)


def write_data_to_csv(data):
    # saving scraped data to csv.

    with open("properties-%s.csv" % (zipcode), 'wb') as csvfile:
        fieldnames = ['title', 'address', 'city', 'state', 'postal_code', 'price', 'facts and features', 'real estate provider', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_response(url):
    # Getting response from zillow.com.

    for i in range(5):
        response = requests.get(url, headers=get_headers())
        print("status code received:", response.status_code)
        if response.status_code != 200:
            # saving response to file for debugging purpose.
            save_to_file(response)
            continue
        else:
            save_to_file(response)
            return response
    return None

def get_data_from_json(raw_json_data):
    # getting data from json (type 2 of their A/B testing page)

    cleaned_data = clean(raw_json_data).replace('<!--', "").replace("-->", "")
    properties_list = []

    try:
        json_data = json.loads(cleaned_data)
        search_results = json_data.get('searchResults').get('listResults', [])

        for properties in search_results:
            address = properties.get('addressWithZip')
            property_info = properties.get('hdpData', {}).get('homeInfo')
            city = property_info.get('city')
            state = property_info.get('state')
            postal_code = property_info.get('zipcode')
            price = properties.get('price')
            bedrooms = properties.get('beds')
            bathrooms = properties.get('baths')
            area = properties.get('area')
            info = f'{bedrooms} bds, {bathrooms} ba ,{area} sqft'
            broker = properties.get('brokerName')
            property_url = properties.get('detailUrl')
            title = properties.get('statusText')

            data = {'address': address,
                    'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'price': price,
                    'facts and features': info,
                    'real estate provider': broker,
                    'url': property_url,
                    'title': title}
            properties_list.append(data)

        return properties_list

    except ValueError:
        print("Invalid json")
        return None


def parse(zipcode, filter=None):
    url = create_url(zipcode, filter)
    response = get_response(url)

    if not response:
        print("Failed to fetch the page, please check `response.html` to see the response received from zillow.com.")
        return None

    parser = html.fromstring(response.text)
    search_results = parser.xpath("//div[@id='search-results']//article")

    if not search_results:
        print("parsing from json data")
        # identified as type 2 page
        raw_json_data = parser.xpath('//script[@data-zrr-shared-data-key="mobileSearchPageStore"]//text()')
        return get_data_from_json(raw_json_data)

    print("parsing from html page")
    properties_list = []
    for properties in search_results:
        raw_address = properties.xpath(".//span[@itemprop='address']//span[@itemprop='streetAddress']//text()")
        raw_city = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressLocality']//text()")
        raw_state = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressRegion']//text()")
        raw_postal_code = properties.xpath(".//span[@itemprop='address']//span[@itemprop='postalCode']//text()")
        raw_price = properties.xpath(".//span[@class='zsg-photo-card-price']//text()")
        raw_info = properties.xpath(".//span[@class='zsg-photo-card-info']//text()")
        raw_broker_name = properties.xpath(".//span[@class='zsg-photo-card-broker-name']//text()")
        url = properties.xpath(".//a[contains(@class,'overlay-link')]/@href")
        raw_title = properties.xpath(".//h4//text()")

        address = clean(raw_address)
        city = clean(raw_city)
        state = clean(raw_state)
        postal_code = clean(raw_postal_code)
        price = clean(raw_price)
        info = clean(raw_info).replace(u"\xb7", ',')
        broker = clean(raw_broker_name)
        title = clean(raw_title)
        property_url = "https://www.zillow.com" + url[0] if url else None
        is_forsale = properties.xpath('.//span[@class="zsg-icon-for-sale"]')

        properties = {'address': address,
                      'city': city,
                      'state': state,
                      'postal_code': postal_code,
                      'price': price,
                      'facts and features': info,
                      'real estate provider': broker,
                      'url': property_url,
                      'title': title}
        if is_forsale:
            properties_list.append(properties)
    return properties_list

zips1 = pd.read_html("https://www.ciclt.net/sn/clt/capitolimpact/gw_ziplist.aspx?FIPS=42071")[2]
zips2 = pd.read_html("https://www.ciclt.net/sn/clt/capitolimpact/gw_ziplist.aspx?FIPS=42071")[3]
zips = pd.concat([zips1, zips2])

def api_call(code, zip_holder):
  time.sleep(2)
  try:
    bt = parse(code, filter=None)
    zip_holder.append(bt)
    print(f'                                Worked on {code} with filter None')
  except: 
    try:
      time.sleep(2)
      bt = parse(code, filter="newest")
      zip_holder.append(bt)
      print(f'                                Worked on {code} with filter Newest')
    except:
      bt = parse(code, filter="cheapest")
      zip_holder.append(bt)
      print(f'                                Worked on {code} with filter Cheapest')

zip_holder = []
bad_zips = []

for code in zips['Zip Code']:
  try:
    api_call(code, zip_holder)
  except:
    try:
      time.sleep(5)
      api_call(code, zip_holder)
    except:
      print(f"                                                                                     Didnt work on {code}")

listings_list =  list(itertools.chain(*zip_holder))
listings = pd.DataFrame(listings_list)

def community_scrape(url):
  response = get_response(url)
  parser = html.fromstring(response.text)

  p = parser.xpath('//*[@id="ds-container"]/div[4]//text()')[0]
  listing_details = pd.json_normalize(json.loads(p))

  fcts = parser.xpath('//*[@id="ds-data-view"]/ul/li[3]/div//text()')[1:]

  fact_names = [i for i in fcts if fcts.index(i)%2 == 0]
  fact_values = [i for i in fcts if fcts.index(i)%2 == 1]

  z = dict(zip(fact_names, fact_values))

  facts_all_df = pd.DataFrame(z, index=[0])
  facts_df = facts_all_df[facts_all_df.columns[0:13]]

  page_df = pd.concat([listing_details, facts_df], axis=1)
  page_df["listing_desc"] = parser.xpath('//*[@id="ds-data-view"]/ul/li[2]/div/div[4]//text()')[0]
  
  try:
    j = parser.xpath("/html/body/div[1]/div[6]/div[1]/div[1]/div/div/div[3]/div/div/div/div[2]/div[4]//text()")[1]
    image_link = json.loads(j)["image"]
    page_df['image_link'] = image_link
  except:
    page_df['image_link'] = 'NA'
    print("Couldn't Retrieve Image Link: Inserting NA")

  page_dict = page_df.to_dict()

  return page_dict

  print("Success")


def homedetail_scrape(url):
  response = get_response(url)
  parser = html.fromstring(response.text)

  fullpage = parser.xpath("/html/body/div[1]/div[6]/div[1]/div[1]/div/div/div[3]/div/div/div/div[2]/div[4]//text()")

  page = fullpage[0]

  page_norm = pd.json_normalize(json.loads(page))
  # page2_norm = pd.json_normalize(json.loads(page2))

  fcts = parser.xpath('//*[@id="ds-data-view"]/ul/li[4]/div/div/div[1]/ul//text()')

  fact_names = [i for i in fcts if fcts.index(i)%2 == 0]
  fact_values = [i for i in fcts if fcts.index(i)%2 == 1]

  z = dict(zip(fact_names, fact_values))

  facts_df = pd.DataFrame(z, index=[0])

  page_df = pd.concat([page_norm, facts_df], axis=1)
  page_df["listing_desc"] = parser.xpath('//*[@id="ds-data-view"]/ul/li[2]/div/div/div[1]/div[4]//text()')[0]
  
  try:
    j = fullpage[1]
    page_df['image_link'] = json.loads(j)["image"]
  except:
    page_df['image_link'] = 'NA'
    print("Couldn't Retrieve Image Link: Inserting NA")
  
  page_dict = page_df.to_dict()
  
  return page_dict

  print("Success")

dict_list = []

for url in listings['url']:
  
  print(url)
  time.sleep(5)
    
  try:
    dd = community_scrape(url)
    dict_list.append(dd)
  
  except:
    try:
      dd = homedetail_scrape(url)
      dict_list.append(dd)

    except:
      print(f"                                                   Didn't Work on {url}")

add_details = pd.DataFrame(dict_list)

hash_list = []
for i in range(len(add_details)):
  hash_list.append(str(uuid.uuid4()))

add_details["id_hash"] = hash_list

add_details.to_csv("Home_Listing_details.csv")
listings.to_csv("Lancaster_co_listings.csv", index=False)

print("Finally Done Running")