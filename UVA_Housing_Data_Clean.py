import pandas as pd

## average price calculator 
def calculate_average_price(amounts):
    if not isinstance(amounts,list) or len(amounts)==0:
        return None
    numbers=[int(amount.replace(',',''))for amount in amounts]
    return sum(numbers)/len(numbers) ##returns average price.

data=pd.read_csv("UVA_housing_detailed.csv")

## Removes 'bad' data scraped 
data_clean= data.dropna(subset=['beds','baths','price'], how='all')
data_clean=data_clean[~((data_clean['beds']=='')& (data_clean['baths']=='')&(data_clean['price']==''))]

## Removes exact duplicates
data_clean=data_clean.drop_duplicates()

## Normalize distance
data_clean['distance']=data_clean['distance'].str.replace(' miles to UVa','').str.replace(' mile to UVa', '').str.replace('+','').astype(float)
## Normalize bed number
data_clean['beds']=data_clean['beds'].str.replace(' Bedroom','').str.replace(' Bedrooms','')
data_clean['beds']=data_clean['beds'].str.extract(r'(\d+)').astype(float)
##Normalize bath number
data_clean['baths']=data_clean['baths'].str.replace(' Bathroom','').str.replace(' Bathrooms','')
data_clean['baths']=data_clean['baths'].str.extract(r'([\d.]+)').astype(float)
## Moves lease terms found in price over to lease_terms
lease=data_clean['price'].str.extract(r'(\d+\s+Month\s+Lease)',expand=False)
data_clean['lease_terms']=data_clean['lease_terms'].fillna('')
data_clean.loc[data_clean['lease_terms']=='','lease_terms']=lease
##Per Bedroom pricing should to its own feature column
data_clean['per bedroom pricing']=data_clean['price'].str.contains('/ Bedroom', na=False).astype(int)

## extract dollar ammounts
data_clean['call for rent']=data_clean['price'].str.contains('Call for Rent',na=False).astype(int)
data_clean['price_amounts']=data_clean['price'].str.findall(r'\$([\d,]+)')
data_clean['price_avg']=data_clean['price_amounts'].apply(calculate_average_price)
data_clean=data_clean.drop(columns=['price_amounts'])

## Amenity filtering/normalization
amenity_columns={
    'dishwasher':'Dishwasher','washer/dryer in unit':'Washer/Dryer in Unit','has balcony':'Balcony|Patio|Porch or Deck', ##Similar enough to group them as individual amenity.
    'gym':'Fitness Room','internet':'High-Speed Internet','pool':'Pool','near bus stop':'Near Bus Stop','furnished':'Furnished','parking':'Parking|Garage',
    'laundry available':'Laundry Room in Community|Laundry Acesss','pet friendly':'Pet|Dog|Cat', 'individual lease':'Individual Leases','disability access':'Disability Accessibility'}

for col_name, pattern in amenity_columns.items():
    data_clean[col_name]=data_clean['amenities'].str.contains(pattern, case=False,na=False).astype(int)
    


data_clean.to_csv("UVA_housing_clean.csv", index=False)