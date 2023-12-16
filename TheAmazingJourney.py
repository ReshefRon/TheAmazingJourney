##########################
#Import necessary modules#
##########################
import attr as at
import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

########################
##Initially parameters##
########################
idx=1
base_url = 'https://www.transfermarkt.com/hapoel-tel-aviv/bilanz/verein/1017/ajax/yw1/saison_id//land_id//wettbewerb_id//clubs_in_comp_id//heim_gast/gast/day//punkte//group/2/datum_von/-/datum_bis/-/plus/1/page/'
user_agent = {'User-agent': 'Mozilla/5.0'}

######################################################
##Scarpe number of pages in the table for future use##
######################################################

def get_pages_number():
    response = requests.get(base_url, headers=user_agent)
    soup = BeautifulSoup(response.content, "html.parser")
    pager = soup.find('div', {'class':'pager'})
    pages = pager.find_all('a', {'class':'tm-pagination__link'})
    number_of_pages = int(pages[len(pages)-1].get('title')[-2])
    return number_of_pages

##########################
#Define dataframe columns#
##########################

df_struct = pd.DataFrame(columns=['Country', 'Matches', 'Goals Scored', 'Goals Conceded', 'Win Ratio'])


def table_to_df(df):
    # Loop through the pages
    for page_number in range(1, get_pages_number() + 1):
        current_url = f"{base_url}{page_number}"
        response = requests.get(current_url, headers=user_agent)
        soup = BeautifulSoup(response.content, "html.parser")
        mtag = soup.find("div",attrs={"id": "yw1", "class": "grid-view"})
        cnt = 0

        # Iterate through rows and extract data
        for row in mtag.find_all('tr'):
            columns = row.find_all('td')
            country_column = row.find('img', {'class': 'flaggenrahmen'})

            # Check for valid data and filter out 'Israel'
            if country_column and country_column.get('title') != 'Israel':
                data = []

                # Iterate through columns and extract data
                for i, column in enumerate(columns, start=1):
                    text = column.text.strip()

                    if i % 11 == 1:
                        data.append(('Country', text))
                    elif i % 11 == 2:
                        data.append(('Matches', int(text)))
                    elif i % 14 == 6:
                        parts = text.split(':')
                        data.append(('Goals Scored', int(parts[0])))
                        data.append(('Goals Conceded', int(parts[1])))
                    elif i % 14 == 10:
                        data.append(('Win Ratio', float(text.strip('%'))))

                # Append the extracted data as a dictionary to the DataFrame
                new_df = pd.DataFrame([dict(data)], columns=df.columns)
                df = pd.concat([df, new_df], ignore_index=True)
    return df
####################################################################################################3


def create_map(base_df):
    # Load your GeoDataFrame containing country geometries and attributes
    #shape = gpd.read_file('World_Countries.shp')
    shape = gpd.read_file('world-administrative-boundaries.shp')
    world_geo = shape.to_json()
    shape = pd.merge(left=shape,
                     right=base_df,
                     left_on='name',
                     right_on='Country',
                     how='left')




    # Create an interactive map centered on a specific location (e.g., Europe)
    m = folium.Map(location=[50, 10], zoom_start=3, min_zoom=3, max_zoom=5)

    folium.Choropleth(
        geo_data=world_geo,
        data=shape,
        columns=['Country', 'Win Ratio'],
        key_on="feature.properties.name",
        fill_color='Reds',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Win Ratio(%)'
    ).add_to(m)

    shape = shape.dropna()
    # Add markers with tooltips for country names
    for _, row in shape.iterrows():
        country_name = row['Country']
        win_ratio = row['Win Ratio']
        matches = row['Matches']
        scored = row['Goals Scored']
        conceded = row['Goals Conceded']
        centroid = row.geometry.centroid

        custom_marker = folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.Icon(
                icon='futbol',  # Icon name ('cloud' is an example)
                prefix='fa',  # Font Awesome prefix
                color='blue',  # Marker color
                icon_color='white',  # Icon color
                icon_size=(0, 0)  # Icon size (width, height)
            )
        )

        if matches == 1:
            with_s = "match"
        else:
            with_s = "matches"

        popup_message = f"""
                <div style="border: 2px solid #ff5733; padding: 10px; background-color: #fff2e6;text-align:center;">
                    <h3 style="font-family:calibri;font-size: 40px; color: #ff0014;">{country_name}</h3>
                    <p style="font-family:calibri;font-size: 20px; color: #ff0014;">{win_ratio}% in {matches} {with_s}</p>
                    <p style="font-family:calibri;font-size: 15px; color: #ff0014;">Goals(Scored vs. Conceded): {scored}:{conceded}</p>
                </div>
            """

        custom_marker.add_child(folium.Popup(popup_message, max_width=300))
        custom_marker.add_to(m)
    m.save('TheAmazingJourney.html')



def main():
    df = table_to_df(df_struct)
    clean_df = df[df['Country'] != 'Iran']
    create_map(clean_df)








main()





