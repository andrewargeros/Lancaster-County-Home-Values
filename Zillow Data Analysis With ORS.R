# Zillow Scraping Data


# Packages ----------------------------------------------------------------

library(tidyverse)
library(magrittr)
library(glue)
library(openrouteservice)
library(osmdata)
library(ggpointdensity)

# Read Data ---------------------------------------------------------------
details_path = "./Zillow Analysis/Lancaster-County-Home-Values/Data"

ad = read_csv(glue("{details_path}/Lancaster_Listings_Zillow.csv"))
details = read_csv(glue("{details_path}/Home_Listing_details_2020-8-15.csv"))


# Data Wrangling ----------------------------------------------------------

details_cleaned = details %>% 
  janitor::clean_names(case = "snake") %>% # Fix column names
  select(!ends_with("_type")) %>% 
  select(!ends_with("context")) %>% # Type and Context vars are useless
  select(-c(x1, interior_details)) %>%
  mutate(across(everything(), ~ str_replace_all(.x, "^\\{0:", ""))) %>% 
  mutate(across(everything(), ~ str_replace_all(.x, "\\}$", ""))) %>% 
  mutate(across(everything(), ~ str_replace_all(.x, "'", ""))) %>% # Remove Dictionary Stuff from Python
  mutate(across(everything(), ~ str_trim(.x))) %>% # Trim leading/trailing space
  mutate(across(c(number_of_rooms, floor_size_value, hoa), ~ ifelse(.x == "None", NA, .x))) %>% # Changes 'none' to NA
  mutate(across(c(number_of_rooms, floor_size_value, hoa, price_sqft), ~ str_replace_all(.x, ",|\\$|/month", ""))) %>% # remove dollar sign and /month from numeric variables
  transform(geo_latitude = as.numeric(geo_latitude),
            geo_longitude = as.numeric(geo_longitude),
            number_of_rooms = as.numeric(number_of_rooms),
            floor_size_value = as.numeric(floor_size_value),
            address_postal_code = as.integer(address_postal_code),
            year_built = as.integer(year_built),
            price_sqft = as.numeric(price_sqft),
            hoa = as.numeric(hoa)) %>% # Change Variable Types
  mutate(est_price = price_sqft*floor_size_value) %>% 
  mutate(listing_desc = str_remove_all(listing_desc, '"'))

ad_cln = ad %>% 
  mutate(url_ext = str_replace_all(url, "^https://www.zillow.com", "")) %>% 
  left_join(., details_cleaned, by = c("url_ext" = "url"))

ad %>% distinct(url)

details_cleaned %>% 
  select(id_hash, image_link) %>% 
  write_csv("photo_links_to_download.csv") # Download Images from this data frame (see ImageDownload.py)

details_cleaned %>% 
  select(id_hash, listing_desc) %>% 
  write_csv(glue("{details_path}/Home_Listing_Descriptions.csv"))

# Open Route Service  -----------------------------------------------------

# This section of code uses the Openrouteservice API to compute the driving distance of each listing to 
# Lancaster and Philadelphia, PA. Free accounts can be made, and these allow for 2000 requests per day.
# This data frame contains 1194 listings, thus drive times must be computed using distinct values.

api_key = "5b3ce3597851110001cf6248749acdcca12b47c4bcc96d81689a334a"
# ors_api_key("5b3ce3597851110001cf6248749acdcca12b47c4bcc96d81689a334a") # Change API key

test_coords = details_cleaned %>% 
  filter(!is.na(geo_latitude)) %>% 
  top_n(1) %>% 
  select(geo_latitude, geo_longitude) # test coordinates tibble

test_lat = test_coords %>% select(geo_latitude) %>% as.numeric()
test_lng = test_coords %>% select(geo_longitude) %>% as.numeric() # Test coordinates values

lancaster = c(-76.3055, 40.0379)
philadelphia = c(-75.1575, 39.9509) # Centers of Cities 

get_distance_to = function(lat, lon, destination, key) { # Function to return drive time in minutes to specified coordinate pair
  out = tryCatch(
    {
      Sys.sleep(5)
      if(!is.na(lat)&&!is.na(lon)){
      
      coords = list(c(lon, lat), destination)
      
      directions = ors_directions(coords, api_key = key)
      time = directions[["features"]][[1]][["properties"]][["summary"]][["duration"]]
      
      mins = time/60
      return(mins)
      } else {return(NA)}
    },
    error = function(cond){message("Parsing Failed")
                           mins = NA},
    warning = function(cond){message("Warning Recieved")
      if(!is.na(lat)){coords = list(c(lon, lat), destination)
      
      directions = ors_directions(coords)
      time = directions[["features"]][[1]][["properties"]][["summary"]][["duration"]]
      
      mins = time/60
      } else {mins = NA}},
    finally = {print("Success")}
  )
  return(out)
}

get_distance_to(test_lat, test_lng, lancaster)
get_distance_to(NA, test_lng, philadelphia) # Test Functions

lancaster_drives = details_cleaned %>% 
  select(geo_latitude, geo_longitude) %>% 
  distinct() %>% # Add distance to Philadelphia and Lancaster to details cleaned
  mutate(lanc_drive = map2(.x = geo_latitude, .y = geo_longitude, ~ get_distance_to(.x, .y, lancaster)))
beepr::beep()


details_cleaned %>% 
  inner_join(., lancaster_drives) %>% 
  write_csv("details_cleaned_with_ors.csv") # Write to CSV as ORS only works on this machine

geo_data = details_cleaned %>% 
  select(id_hash, geo_latitude, geo_longitude) %>% 
  filter(!is.na(geo_latitude))

lanc_drive_times = list()
for(i in 1:nrow(geo_data)){ # other way to do this if tidyverse syntax fails
  hash = geo_data[i,"id_hash"]
  print(hash)
  
  lat = geo_data %>% 
    filter(id_hash == hash) %>% 
    select(geo_latitude) %>% 
    as.numeric()
  lon = geo_data %>% 
    filter(id_hash == hash) %>% 
    select(geo_longitude) %>% 
    as.numeric()
  
  drive_time = get_distance_to(lat, lon, lancaster)
  
  temp_tbl = tribble(~hash, ~time,
                     hash, drive_time)
  
  lanc_drive_times[[hash]] = temp_tbl
}

# Open Route Service Isochrones -------------------------------------------

isochrome_test = ors_isochrones(lancaster, range = 1200, api_key = api_key, output = "sf")
isochrome_30 = ors_isochrones(lancaster, range = 1800, api_key = api_key, output = "sf")
isochrome_test_gj = ors_isochrones(lancaster, range = 1800, api_key = api_key)

# Open Street Maps Visualizations -----------------------------------------

# httr::set_config(httr::config(ssl_verifypeer = 0L, ssl_verifyhost = 0L))

lancaster_co = getbb("Lancaster County, Pennsylvania")

streets = lancaster_co %>%
  opq() %>%
  add_osm_feature(key = "highway", 
                  value = c("motorway", "primary", "secondary", "tertiary")) %>%
  osmdata_sf()

small_streets = lancaster_co %>% 
  opq() %>% 
  add_osm_feature(key = "highway",
                  value = c("residential", "living_street", "unclassified", "service", "footway")) %>% 
  osmdata_sf()

water = lancaster_co %>% 
  opq() %>% 
  add_osm_feature(key = "waterway",
                  value = "river") %>% 
  osmdata_sf()

gg1 = details_cleaned %>% 
  ggplot() +
  geom_sf(data = small_streets$osm_lines, col = 'grey40', size = .1) +
  geom_sf(data = streets$osm_lines, col = 'grey40', size = .4) +
  geom_sf(data = small_streets$osm_lines, col = alpha('grey40', .2), size = .1) +
  geom_sf(data = streets$osm_lines, col = alpha('grey40', .2), size = .4) +
  geom_sf(data = isochrome_test$geometry, color = "#6a8bad", fill = NA, size = 2) +
  geom_sf(data = isochrome_30$geometry, color = "#3e5871", fill = NA, size = 2) +
  geom_pointdensity(aes(geo_longitude, geo_latitude), size = 2, alpha = .8) +
  scale_color_viridis_c(option = 'inferno') +
  coord_sf(xlim = lancaster_co[1,], ylim = lancaster_co[2,], expand = TRUE) + 
  geom_blank() +
  theme_void() +
  theme(legend.position = "none",
        plot.background = element_rect(fill = "#282828"))

gg2 = details_cleaned %>% 
  ggplot() +
  geom_sf(data = small_streets$osm_lines, col = 'grey40', size = .1) +
  geom_sf(data = streets$osm_lines, col = 'grey40', size = .4) +
  geom_sf(data = small_streets$osm_lines, col = alpha('grey40', .2), size = .1) +
  geom_sf(data = streets$osm_lines, col = alpha('grey40', .2), size = .4) +
  geom_pointdensity(aes(geo_longitude, geo_latitude, color = log(price_sqft)), size = 2, alpha = .8) +
  scale_color_viridis_c(option = 'inferno') +
  coord_sf(xlim = lancaster_co[1,], ylim = lancaster_co[2,], expand = TRUE) + 
  geom_blank() +
  theme_void() +
  theme(legend.position = "none",
        plot.background = element_rect(fill = "#282828"))


# Adding House Type from RestB --------------------------------------------

house_types = read_csv(glue('{details_path}/house_img_details_restbapi.csv')) %>% select(-X1)

house_types %>% 
  group_by(label) %>% 
  summarise(n = n(),
            avg_cl = mean(confidence)) %>% 
  arrange(desc(n))

details_cleaned %>% 
  inner_join(., house_types, by = c('image_link' = 'link')) %>% 
  group_by(label) %>% 
  summarise(mean_pr_sqft = mean(est_price, na.rm = T),
            homes = n())

gg2 = details_cleaned %>% 
  ggplot() +
  geom_sf(data = small_streets$osm_lines, col = 'grey40', size = .1) +
  geom_sf(data = streets$osm_lines, col = 'grey40', size = .4) +
  geom_sf(data = small_streets$osm_lines, col = alpha('grey40', .2), size = .1) +
  geom_sf(data = streets$osm_lines, col = alpha('grey40', .2), size = .4) +
  geom_pointdensity(aes(geo_longitude, geo_latitude, color = log(price_sqft)), size = 2, alpha = .8) +
  scale_color_viridis_c(option = 'inferno') +
  coord_sf(xlim = lancaster_co[1,], ylim = lancaster_co[2,], expand = TRUE) + 
  geom_blank() +
  theme_void() +
  theme(legend.position = "none",
        plot.background = element_rect(fill = "#282828"))




























































