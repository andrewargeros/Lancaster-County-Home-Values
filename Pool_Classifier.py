# This Script is used to classify homes with listing descriptions that refer to a pool into having either private or Community amenities
# Uses Zero-Shot Classification from HuggingFace Transformers

from transformers import pipeline
from tqdm import tqdm
import pandas as pd
import re 

classifier = pipeline("zero-shot-classification")

pool_options = ['Private Pool', 'Community Pool', 'Pool Table', 'Whirlpool'] # Using Regex Finds matches for things that shouldn't count

result_list = []
for listing in tqdm(df['listing_desc'].unique()): # Runs on Unique Values of Listing Description to save time/memory
  if len(re.findall(r'pool|Pool|POOL', listing)) > 0:

    result = classifier(listing, pool_options, multi_class=True)
    result_label = result['labels'][0] # Takes best Prediction and Score
    result_score = result['scores'][0]

    result_dict = {'input': listing,
                   'output': result_label,
                   'score': result_score}
    result_list.append(result_dict)
    print(f'Pool Found with Class {result_label}. Appending to List. List now contains {len(result_list)} elements')

  else:
    print('String Did Not Contain References to Pool')

pools = pd.DataFrame(result_list)

pool_join = pd.merge(pools, df, left_on='input', right_on='listing_desc').drop('listing_desc', axis = 1)
pool_join.to_csv("Pool_Listings_Processed.csv", index=False)