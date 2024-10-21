#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEAM NAME: CGENWAY
TEAM MEMBER: TIFFANY GAN(tgan), YUMENG SHA(yumengsh), CHOLE HUANG(yihanhua), OUYU HAN(ouyuh)
"""
#%%
print('USER INSTRUCTIONS:')
print('Our current version supports region searches for North Oakland, Shadyside, and Squirrel Hill.')
print('For the best experience, please ensure the region name is entered correctly.')
print('You can simply copy and paste the region names: North Oakland, Shadyside, or Squirrel Hill.')
print('-'*80)
import pandas as pd
import json
import requests, bs4
import csv
import sys
zipcode_region=pd.read_csv('Pittsburgh Region Zip Code.csv')
zipcode_region.fillna(method='ffill',inplace=True)

# Legal regions for inputting
allowed_regions = ['North Oakland', 'Shadyside', 'Squirrel Hill' ]

# Input for region selection
region = input('Enter the interested region: ')
# Check if the entered region is valid
if region not in allowed_regions:
    print(f"Error: '{region}' is not a valid region. Please enter one of the following: {', '.join(allowed_regions)}.")
    sys.exit()
interested_region_zipcode = zipcode_region.loc[zipcode_region['Region Name']==region,'Zip Code']

#%%
#as the interested region has several corresponding zipcodes, loop over the zipcodes to get the information
for a in interested_region_zipcode:
    print(a,'region:')
    url = 'https://api.rentcast.io/v1/markets?zipCode='+str(a)+'&dataType=Rental&historyRange=6'
    # Set up headers for the API request
    headers = {
         "accept": "application/json",
         "X-Api-Key": "c2c1356a13b24ec5ae2d48df74500081"}
    response=requests.get(url, headers=headers)

    if response.status_code==200:
         data = json.loads(response.content.decode('utf-8'))
    #extract the needed statistics through indexing the dict
    try: 
         average_rent=data['rentalData']['averageRent']
         print(f"The average rent is: {average_rent}")
    except KeyError:
         print('Currently the statistics is unavaliable')
    try:
        median_rent=data['rentalData']['medianRent']
        print(f"The median rent is: {median_rent}")
    except KeyError:
         print('Currently the statistics is unavaliable')
    try:
        minimum_rent=data['rentalData']['minRent']
        print(f"The minimum rent is: {minimum_rent}")
    except KeyError:
         print('Currently the statistics is unavaliable')
    try:
        maximum_rent=data['rentalData']['maxRent']
        print(f"The maximum rent is: {maximum_rent}")
    except KeyError:
         print('Currently the statistics is unavaliable')

#%%
#read crime data csv
raw_data = pd.read_csv('crime data.csv')
address = raw_data['INCIDENTLOCATION'].tolist()

#append a row indicating the zipcode
zipcode_list = []
for item in address:
    address_split = item.split(" ")
    zipcode = address_split[-1]
    zipcode_list.append(zipcode)  # Append to the list

raw_data['zipcode'] = zipcode_list

#keep the rows that have the right format of zipcode
data_cleaned = raw_data[raw_data['zipcode'].apply(lambda x: len(str(x)) == 5)]

#extract year from the ARRESTTIME column
import time

for item in data_cleaned:
    data_cleaned['ARRESTTIME'] = pd.to_datetime(data_cleaned['ARRESTTIME'])
    data_cleaned['Year'] = data_cleaned['ARRESTTIME'].dt.year

#filter data
data_cleaned = data_cleaned[(data_cleaned['Year'] >= 2016) & (data_cleaned['Year'] <= 2023)]

# Ensure Zip Code is the same type in both DataFrames (convert to string if necessary)
zipcode_region['Zip Code'] = zipcode_region['Zip Code'].astype(str)
data_cleaned['zipcode'] = data_cleaned['zipcode'].astype(str)

# Merge data_cleaned with zipcode_region on 'Zip Code'
data_cleaned_with_region = pd.merge(data_cleaned, zipcode_region[['Zip Code', 'Region Name']], 
                                    left_on='zipcode', right_on='Zip Code', 
                                    how='inner')

# Rename 'Region Name' column to 'region' in the merged DataFrame
data_cleaned_with_region.rename(columns={'Region Name': 'Region'}, inplace=True)


# Group by 'region' and 'Year'
grouped = data_cleaned_with_region.groupby(['Region', 'Year'])

# Iterate through each group and assign them to a dictionary
grouped_dataframes = {name: group for name, group in grouped}

#create a dataframe indicating Region, Year and cases of crimes
results = []
for name, group in grouped_dataframes.items():
    region1, year1 = name  # Unpack the name tuple into region and year
    count = len(group)   # Count the number of records in the group
    results.append({'Region': region1, 'Year': year1, 'Count': count})  

# Create a new DataFrame from the results
region_year = pd.DataFrame(results)

#create a new column indicating the increase in crimes over year
region_year['Increase Rate(%)'] = region_year.groupby('Region')['Count'].pct_change() * 100



import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick

def plot():
    # Get unique region names from zipcode_region
    unique_regions = zipcode_region['Region Name'].unique()

    # Prompt user for a region
    #region_input = input("Please enter a region: ")

    # Check if the entered region is valid
    if region in unique_regions:
        # Filter the region_year DataFrame for the valid region
        df = region_year[region_year['Region'] == region]

        # Extract 'Count', 'Increase Rate(%)', and 'Year' from the DataFrame
        count = df['Count'].tolist()  # 'Count' column as a list
        increase_rate = df['Increase Rate(%)'].tolist()  # 'Increase Rate(%)', handling NaN values
        year = df['Year'].tolist()  # 'Year' column as a list

        # Format y-axis with percentage for Increase Rate
        fmt = '%.2f%%'
        yticks = mtick.FormatStrFormatter(fmt)  # Set percentage format

        # Create figure and axes
        fig = plt.figure(figsize=(10, 6))  # Adjust the size of the figure
        ax1 = fig.add_subplot(111)  

        # Plot Increase Rate on the primary y-axis
        ax1.plot(year, increase_rate, 'or-', label='Increase Rate(%)')  
        ax1.yaxis.set_major_formatter(yticks)  # Format y-axis for percentage

        # Annotate data points on the Increase Rate line
        for i, (_x, _y) in enumerate(zip(year, increase_rate)):  
            plt.text(_x, _y, f'{increase_rate[i]:.2f}%', color='black', fontsize=10)  # Show values on the plot

        # Set legend and labels for Increase Rate
        ax1.legend(loc=1)
        ax1.set_ylim([-30, 250])  # Adjust based on your data range
        ax1.set_ylabel('Increase Rate (%)')

        # Secondary y-axis for 'Count'
        ax2 = ax1.twinx()  
        ax2.bar(year, count, alpha=0.3, color='blue', label='Count')  
        ax2.set_ylim([0, 2500])  # Adjust this based on your data range
        ax2.set_ylabel('Count')

        # Set legend and labels for 'Count'
        ax2.legend(loc=2)

        #Set x-axis labels for years
        plt.xticks(year, [str(y) for y in year])
        plt.title(f'crimes in {region}')

        # Show the plot
        plt.show()

    else:
        print(f"Region '{region}' not found. Please enter a valid region.")

# Call the function to plot
plot()

    #%%
zipcodes = zipcode_region.loc[zipcode_region['Region Name'] == region, 'Zip Code']

# Initialize a list to store results
all_comparables = []

for zipcode in zipcodes:
     # Start with the base URL
     url = f"https://api.rentcast.io/v1/avm/rent/long-term?address={zipcode}"

     # Set up headers for the API request
     headers = {
         "accept": "application/json",
         "X-Api-Key": "c2c1356a13b24ec5ae2d48df74500081"
     }

     # Make the API request
     response = requests.get(url, headers=headers)

     # Check if the request was successful
     if response.status_code != 200:
         print(f"Failed to fetch data for Zip Code {zipcode}. Please check the inputs and try again.")
         continue

     # Parse the response data
     data = json.loads(response.content.decode('utf-8'))

     # Check if the 'comparables' field is present and not empty
     if 'comparables' not in data or not data['comparables']:
         print(f"No results found for Zip Code {zipcode}.")
     else:
         print(f"Results for Zip Code {zipcode}:")
         comparables = data['comparables']
         all_comparables.extend(comparables)  # Collect all comparables for later filtering

         # Display the results for the current zip code
         for property in comparables:
             if 'price' in property:
                 print('Price:', property['price'])
             if 'formattedAddress' in property:
                 print('Address:', property['formattedAddress'])
             if 'propertyType' in property:
                 print('Property Type:', property['propertyType'])
             if 'bedrooms' in property:
                 property['bedrooms'] = str(property['bedrooms'])
                 print('Bedrooms:', property['bedrooms'])
             if 'bathrooms' in property:
                 property['bathrooms'] = str(property['bathrooms'])
                 print('Bathrooms:', property['bathrooms'])
             print("-" * 40)
      
# Load the data from Zillow (using web scraping method)
Zillow_listings = pd.read_csv('listing-cleaned.csv', dtype={'bedrooms': str, 'bathrooms': str, 'Zip Code': str})

# Print Zillow listings
print("Zillow Listings:")
for index, row in Zillow_listings.iterrows():
    print('Price:', row.get('price', 'N/A'))
    print('Address:', row.get('formattedAddress', 'N/A'))
    print('Property Type:', row.get('propertyType', 'N/A'))
    print('Bedrooms:', row.get('bedrooms', 'N/A'))
    print('Bathrooms:', row.get('bathrooms', 'N/A'))
    print('Zillow Link:', row.get('Zillow Link', 'N/A'))
    print("-" * 40)

                 
#%%   
# Filter Zillow data based on zip codes
filtered_zillow_data = Zillow_listings[Zillow_listings['Zip Code'].isin(zipcodes)]

# Merge and display both API and web scraping results

combined_listings = pd.concat([pd.DataFrame(all_comparables), filtered_zillow_data], ignore_index=True)



# Get optional user inputs for property type, number of bedrooms, and bathrooms
property_type = input("Enter the property type (e.g., House, Apartment) or press Enter to skip: ").strip()
bedrooms = input("Enter the number of bedrooms or press Enter to skip: ").strip()
bathrooms = input("Enter the number of bathrooms or press Enter to skip: ").strip()


# Default property type handling

if property_type.lower() == 'house':
    property_type = 'Single Family'  # Default to 'Single Family' if user inputs 'house'
    

# Filter results based on additional user inputs
filtered_results = combined_listings

if property_type:
    filtered_results = filtered_results[filtered_results['propertyType'].str.lower() == property_type.lower()]

if bedrooms:
    filtered_results = filtered_results[filtered_results['bedrooms'].astype(str) == bedrooms]

if bathrooms:
    filtered_results = filtered_results[filtered_results['bathrooms'].astype(str) == bathrooms]

# Display filtered results
if filtered_results.empty:
    print("No results found matching the specified criteria.")
else:
    print("Filtered results based on your criteria:")
    for index, property in filtered_results.iterrows():
        price = property.get('price', 'N/A')
        print('Price:', price)

        address = property.get('formattedAddress', 'N/A')
        print('Address:', address)

        property_type_value = property.get('propertyType', 'N/A')
        print('Property Type:', property_type_value)

        bedrooms_value = property.get('bedrooms', 'N/A')
        print('Bedrooms:', bedrooms_value)

        bathrooms_value = property.get('bathrooms', 'N/A')
        print('Bathrooms:', bathrooms_value)

        # Add Zillow Link (if exists)
        zillow_link = property.get('Zillow Link', 'N/A')
        if zillow_link != 'N/A':
            print('Zillow Link:', zillow_link)

        print("-" * 40)
        

#%%
import folium
import pandas as pd

#user input
year_input = input("Please enter a year: ")

# Convert the year_input to an integer if necessary
try:
    year_input = int(year_input)
except ValueError:
    print("Invalid year input. Please enter a valid year between 2016 and 2020.")
    raise

# Filter data based on region and year
data_filtered = data_cleaned_with_region[
    (data_cleaned_with_region['Region'] == region) &
    (data_cleaned_with_region['Year'] == year_input)
]

# clean data
data_cleaned_with_region_cleaned = data_filtered.dropna(subset=['Y', 'X'])

# Initialize the map for Pittsburgh
pittsburgh_location = [40.4406, -79.9959]  # Latitude and Longitude of Pittsburgh
pittsburgh_map = folium.Map(location=pittsburgh_location, zoom_start=12)

# Add markers based on the latitude and longitude
for i in range(len(data_cleaned_with_region_cleaned)):
    # Extract the latitude and longitude from the respective columns
    try:
        latitude = data_cleaned_with_region_cleaned['Y'].iloc[i]
        longitude = data_cleaned_with_region_cleaned['X'].iloc[i]

        # Check if latitude and longitude are valid
        if pd.notna(latitude) and pd.notna(longitude):
            # Add a marker to the map at the latitude and longitude
            folium.Marker([latitude, longitude]).add_to(pittsburgh_map)
    except IndexError:
        print(f"IndexError: Failed at row {i} - skipping this row.")

# Save the map to an HTML file
pittsburgh_map.save("pittsburgh_map.html")
print('Now, pittsburgh_map.html is in your working directory :)')
   
    
  

 



            
            
            
            
            
            
            
            
            
            
            
            
            
    