##########################
#Import necessary modules#
##########################

import pandas as pd
import geopandas as gpd
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
        mtag = soup.find("div", attrs={"id": "yw1", "class": "grid-view"})
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



def main():
    df = table_to_df(df_struct)
    df.reset_index()
    print(df)






main()






