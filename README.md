# Lancaster County Home Values
 An analysis of home listings in Lancaster County, PA

## Data Generation

The file `zillowscrape.py` contains code to programmatically scrape listings of for-sale houses in each zip code within Lancaster County. These zip codes were first scraped from https://www.ciclt.net/sn/clt/capitolimpact/gw_ziplist.aspx?FIPS=42071 . Should you want to replicate this project for a different county, change the FIPS code parameter at the end of the link to that of the desired county (`?FIPS=`).   

The code creates a new proxy user agent each pass using a unique hash from the `uuid` library appended to the standard user agent allowed by the site per its `/robots.txt` file. This is done to prevent throttling and eventual blocking from the host server while making programmatic requests. First, links are tested using Zillow's filters for "Newest" and "Cheapest", this appends listings for each zip code, but in a rudimentary fashion. From there, a separate process is defined to extract the listing details for each returned result. The results are then bound into a `pandas` dataframe and exported as `Home_listing_details.csv`.

## Photo Downloads

As part of the above scraping process, the `href` tag of the listing's cover image is extracted as a feature. After mild cleaning using R, these links are downloaded into .png files using `imagedownloader.py`. These are saved for image detection/classification later. 
