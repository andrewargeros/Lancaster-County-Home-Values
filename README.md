# Lancaster County Home Values
 An analysis of home listings in Lancaster County, PA

## Data Generation

The file `zillowscrape.py` contains code to programmatically scrape listings of for-sale houses in each zip code within Lancaster County. These zip codes were first scraped from https://www.ciclt.net/sn/clt/capitolimpact/gw_ziplist.aspx?FIPS=42071 . Should you want to replicate this project for a different county, change the FIPS code parameter at the end of the link to that of the desired county (`?FIPS=`).   

The code creates a new proxy user agent each pass using a unique hash from the `uuid` library appended to the standard user agent allowed by the site per its `/robots.txt` file. This is done to prevent throttling and eventual blocking from the host server while making programmatic requests. First, links are tested using Zillow's filters for "Newest" and "Cheapest", this appends listings for each zip code, but in a rudimentary fashion. From there, a separate process is defined to extract the listing details for each returned result. The results are then bound into a `pandas` dataframe and exported as `Home_listing_details.csv`.

## Photo Downloads

As part of the above scraping process, the `href` tag of the listing's cover image is extracted as a feature. After mild cleaning using R, these links are downloaded into .png files using `imagedownloader.py`. These are saved for image detection/classification later.

## OpenRouteService

In R, the OpenRouteService API is used to calculate the driving time and distance from each listing to both Lancaster and Philadelphia, PA. API tokens can be requested at https://openrouteservice.org/ . Note, with a free account, only 2000 directions requests can be made perday, thus it currently takes two attemps to run the code to generate these listings.

Isochrones, representing driving times to the center of the county are also added to some of the maps so as to show the distance relative to a resident's commute into the city.

## RestB API

Using a trial of the RestB API, a neural-based API for real estate listings. By passing the listing cover images to the api, a classification of, first whether the image is of a house, and in what style of architecture is the house built.

## Zero Shot Natural Language Processing

Using the listing descriptions from the houses collected, a zero-shot machine learning classifier is used to classify listings that mention "pool" into "Community Pool", "Private Pool", or "Not a Pool" classes. This allows us to create accurate descriptions of the amenities offered in the descriptions. This approach is similar in nature to methods like GPT-3 in that there is not an iterative training procedure to create the model. 
