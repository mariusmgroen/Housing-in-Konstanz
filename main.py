# coding: utf-8

import pandas as pd
import numpy as np

import os
import requests
import urllib.request
import time
import random
import shutil
import re

from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent = 'PythonProjectUniversityKonstanzmail:marius.groen@uni.kn')



number_of_pages = 25

today = str(time.strftime('%Y%m%d-%H%M'))

dir_path = str('/home/marius/python_project/')
dir_path_data = str('/home/marius/python_project/data')
dir_path_html = str('/home/marius/python_project/data/html')
dir_path_raw = str('/home/marius/python_project/data/raw')
dir_path_clean = str('/home/marius/python_project/data/clean')
dir_path_day = str('/home/marius/python_project/data/html/' + today)

try:
    os.mkdir(dir_path_data)
except FileExistsError:
    print('Directory', '"' + dir_path_data + '"', 'already exists. Continue:')

try:
    os.mkdir(dir_path_html)
except FileExistsError:
    print('Directory', '"' + dir_path_html + '"', 'already exists. Continue:')

try:
    os.mkdir(dir_path_raw)
except FileExistsError:
    print('Directory', '"' + dir_path_raw + '"', 'already exists. Continue:')

try:
    os.mkdir(dir_path_clean)
except FileExistsError:
    print('Directory', '"' + dir_path_clean + '"', 'already exists. Continue:')

try:
    os.mkdir(dir_path_day)
    print('Directory', '"' + dir_path_day + '"', 'created!')
except FileExistsError:
    print('Directory', '"' + dir_path_day + '"', 'already exists.')



list_of_html_sources = []
for i in range(number_of_pages):
    link = 'https://www.wg-gesucht.de/wg-zimmer-in-Konstanz.74.0.1.' + str(i) + '.html'
    print('Requesting:', link)
    list_of_html_sources.append(requests.get(link).text)
    print(' Do not wake Cerberus...!')
    time.sleep(random.randint(10,20))

i = 0
for link in list_of_html_sources:
    webpage = 'webpage' + str(i) + ".html"
    with open(os.path.join(dir_path_day, webpage), 'w') as f:
        f.write(link)
    i = i + 1



def create_dataframe():
    df_columns = ['link',
                  'id',
                  'hhSize',
                  'hhF',
                  'hhM',
                  'size',
                  'price',
                  'price_m2',
                  'location_self',
                  'address',
                  'street',
                  'number',
                  'address_geopy',
                  'location_geopy',
                  'lat',
                  'long',
                  'title',
                  'timestamp',
                  'inactive-stamp',
                  'active',
                  'location'
                 ]
    dataframe = pd.DataFrame(columns = df_columns)
    return(dataframe)


def parse_data_from_html(html_page, df_alldata):
    with open(html_page, 'r') as f:
        html_data = f.read()
    soup = BeautifulSoup(html_data, 'html.parser')
    wg_container = soup.findAll("div", {"class":["panel panel-default list-details-ad-border offer_list_item",
                                                 "panel panel-default panel-deactivated list-details-ad-border offer_list_item"]})

    for container in wg_container:
        if (container['class'] == ['panel', 'panel-default', 'list-details-ad-border', 'offer_list_item']):
            value_list = []

            # Link
            title_container = container.find('h3', class_ = 'headline headline-list-view noprint truncate_title')
            link = title_container.find('a', class_='detailansicht')['href'].strip()
            link = str("https://www.wg-gesucht.de/" + str(link))
            value_list.append(link)

            # ID
            value_list.append(container['data-id'])

            # Composition
            composition = container.find('span', class_='noprint')['title']
            for number in re.findall('\d+', composition):
                value_list.append(number)

            # Size
            size_price_container = container.find('div', class_ = 'detail-size-price-wrapper')
            size_price_container_clean = size_price_container.find('a', class_='detailansicht').text.strip()
            size_price_split = str.split(str.join(" ", str.split(size_price_container_clean)), sep = '|')
            size = int(str.split(size_price_split[0].strip(), sep = " m")[0])
            value_list.append(int(size))

            # Price
            price = int(str.split(size_price_split[1].strip(), sep = " €")[0].strip())
            value_list.append(price)
            # Price per square meter
            price_per_sqm = float(price/size)
            value_list.append(price_per_sqm)

            # Location and Address
            loc_add_container = container.find('div', class_='list-details-panel-inner')
            loc_add_container_clean = loc_add_container.find('p').text.strip()
            location = str.split(str.split(str.join(" ", str.split(loc_add_container_clean)), sep=", ")[0], "Konstanz")[1].strip()
            value_list.append(location)

            address = str.split(str.split(str.join(" ", str.split(loc_add_container_clean)), sep=",")[1], sep=" Verfügbar")[0].strip()
            if (re.findall(r'\d+', address) == []):
                number = None
                street = address
                if (street == "Hauptstraße") or (street == "Hauptstrasse"):
                    address = str(street + ", Kreuzlingen")
                else:
                    address = str(street + ", Konstanz")
            else:
                number = re.findall(r'\d+\w*', address)[0]
                street = address[:-len(re.findall(r'\d+.*', address)[0])].strip()
                if (street == "Hauptstraße") or (street == "Hauptstrasse"):
                    address = str(street + " " + number + ", Kreuzlingen")
                else:
                    address = str(street + " " + number + ", Konstanz")
            value_list.append(address)
            value_list.append(street)
            value_list.append(number)

            try:
                geodata = geolocator.geocode(address)
                value_list.append(geodata.address)
                try:
                    stadtteilvorlaufig = str.split(str(geodata.address), sep = ",")[-8].strip()
                    value_list.append(stadtteilvorlaufig)
                except:
                    value_list.append(None)
                value_list.append(geodata.latitude)
                value_list.append(geodata.longitude)
            except:
                value_list.append(None)
                value_list.append(None)
                value_list.append(None)
                value_list.append(None)

            # Title
            title_container = container.find('h3', class_ = 'headline headline-list-view noprint truncate_title')
            title = title_container.find('a', class_='detailansicht').text.strip()
            value_list.append(title)

            # Timestamp
            value_list.append(today)

            # Timestamp (inactive)
            value_list.append('')

            # Active
            value_list.append(True)

            # location
            value_list.append('')

            # Turn all infos into a row
            df_alldata.loc[len(df_alldata)] = value_list

        elif (container['class'] == ['panel', 'panel-default', 'panel-deactivated', 'list-details-ad-border', 'offer_list_item']):
            value_list = []

            # Link
            title_container = container.find('h3', class_ = 'headline headline-list-view noprint truncate_title')
            link = title_container.find('a', class_='detailansicht')['href'].strip()
            link = str("https://www.wg-gesucht.de/" + str(link))
            value_list.append(link)

            # ID
            value_list.append(container['data-id'])
            value_list.append(None)
            value_list.append(None)
            value_list.append(None)

            # Size
            size_price_container = container.find('div', class_ = 'detail-size-price-wrapper')
            size_price_container_clean = size_price_container.find('a', class_='detailansicht').text.strip()
            size_price_split = str.split(str.join(" ", str.split(size_price_container_clean)), sep = '|')
            size = int(str.split(size_price_split[0].strip(), sep = " m")[0])
            value_list.append(int(size))

            # Price
            value_list.append(None)
            # Price per square meter
            value_list.append(None)

            # Location and Address
            loc_add_container = container.find('div', class_='list-details-panel-inner')
            loc_add_container_clean = loc_add_container.find('p').text.strip()
            location = str.split(str.split(str.join(" ", str.split(loc_add_container_clean)), sep=", ")[0], "Konstanz")[1].strip()
            value_list.append(location)

            address = str.split(str.split(str.join(" ", str.split(loc_add_container_clean)), sep=",")[1], sep=" Verfügbar")[0].strip()
            if (re.findall(r'\d+', address) == []):
                number = None
                street = address
                if (street == "Hauptstraße"):
                    address = str(street + ", Kreuzlingen")
                else:
                    address = str(street + ", Konstanz")
            else:
                number = re.findall(r'\d+\w*', address)[0]
                street = address[:-len(re.findall(r'\d+.*', address)[0])].strip()
                if (street == "Hauptstraße") or (street == "Hauptstrasse"):
                    address = str(street + " " + number + ", Kreuzlingen")
                else:
                    address = str(street + " " + number + ", Konstanz")

            value_list.append(address)
            value_list.append(street)
            value_list.append(number)
            try:
                geodata = geolocator.geocode(address)
                value_list.append(geodata.address)
                try:
                    stadtteilvorlaufig = str.split(str(geodata.address), sep = ",")[-8].strip()
                    value_list.append(stadtteilvorlaufig)
                except:
                    value_list.append(None)
                value_list.append(geodata.latitude)
                value_list.append(geodata.longitude)
            except:
                value_list.append(None)
                value_list.append(None)
                value_list.append(None)
                value_list.append(None)

            # Title
            title_container = container.find('h3', class_ = 'headline headline-list-view noprint truncate_title')
            title = title_container.find('a', class_='detailansicht').text.strip()
            value_list.append(title)

            # Timestamp
            value_list.append(today)

            # Timestamp (inactive)
            value_list.append('')

            # Active
            value_list.append(False)

            # location
            value_list.append(None)

            # Write Row
            df_alldata.loc[len(df_alldata)] = value_list
    return(df_alldata)



def cleaning(df):
    legit = ["Allensbach",
             "Allmannsdorf",
             "Altstadt",
             "Dettingen",
             "Dingelsdorf",
             "Egg",
             "Fürstenberg",
             "Industriegebiet",
             "Kreuzlingen",
             "Königsbau",
             "Litzelstetten",
             "Paradies",
             "Petershausen-Ost",
             "Petershausen-West",
             "Reichenau",
             "Staad",
             "Wallhausen",
             "Wollmatingen"
            ]

    df['location'] = df['location_geopy']
    df.loc[(df['location_geopy'] == "Konstanz-Industriegebiet"), 'location'] = "Industriegebiet"
    df.loc[(df['location_geopy'] == "Dettingen-Wallhausen"), 'location'] = "Dettingen"
    df.loc[(df['location_geopy'] == "Reichenau-Waldsiedlung"), 'location'] = "Reichenau"
    df.loc[(df['location_geopy'] == "Lindenbühl"), 'location'] = "Reichenau"
    df.loc[(df['location_self'] == "Kreuzlingen"), 'location'] = "Kreuzlingen"
    df.loc[(df['address'].str.contains("Kreuzlingen")), 'location'] = "Kreuzlingen"

    df.loc[~df['location'].isin(legit), 'location'] = ''

    df.drop('location_geopy', axis = 1, inplace = True)
    df.drop('location_self', axis = 1, inplace = True)

    df['location'].replace('', np.nan, inplace = True)
    df.dropna(subset = ['location'], inplace = True)

    df['size'] = df['size'].astype(int)
    df['price'] = df['price'].astype(float)
    df['price_m2'] = df['price_m2'].astype(float)
    df['lat'] = df['lat'].astype(float)
    df['long'] = df['long'].astype(float)
    df['hhSize'] = df['hhSize'].astype(float)
    df['hhF'] = df['hhF'].astype(float)
    df['hhM'] = df['hhM'].astype(float)

    df = df[['id',
             'size',
             'price',
             'price_m2',
             'location',
             'address',
             'street',
             'number',
             'address_geopy',
             'lat',
             'long',
             'hhSize',
             'hhF',
             'hhM',
             'title',
             'link',
             'timestamp',
             'inactive-stamp',
             'active'
            ]
           ]
    return(df)



df_raw_data = create_dataframe()

list_of_df = []
for i in range(number_of_pages):
    webpage = dir_path_day + '/webpage' + str(i) + '.html'
    print('Parsing', webpage + '...')
    list_of_df.append(parse_data_from_html(webpage, df_raw_data))
print("\n All pages parsed.")

df_raw_data.to_csv(str(dir_path_raw + '/parsed_' + today + '.csv'),
                   sep = ';',
                   encoding = 'utf-8',
                   index = False
                  )


df_raw_data = pd.read_csv(str(dir_path_raw + '/parsed_' + today + '.csv'), sep=';')
df = cleaning(df_raw_data)

df.to_csv(str(dir_path_clean + '/parsed_' + today + '_cleaned.csv'),
          sep = ';',
          encoding = 'utf-8',
          index = False
         )


with open(str(dir_path + '/dataframes.txt'), 'a') as f:
    f.write(str(dir_path_clean + '/parsed_' + today + '_cleaned.csv' + '\n'))



# Define: Combining dataframes
def combine(total, new):
    new_total = total.append(new, ignore_index=True)
    new_total = new_total.drop(new_total[new_total.duplicated(subset = ['id', 'active'])].index)

    # Condition 1: if was active and should be inactive
    con1 = ((new_total.duplicated(subset = ['id'], keep='last')) & (new_total['active'][new_total.duplicated(subset = ['id'], keep = 'last')] == True))
    # Condition 2: if was inactive and should be active
    con2 = ((new_total.duplicated(subset = ['id'], keep='last')) & (new_total['active'][new_total.duplicated(subset = ['id'], keep = 'last')] == False))

    new_total['inactive-stamp'] = np.select([con1, con2], [today, None], default=new_total['inactive-stamp'])
    new_total['active'] = np.select([con1, con2], [False, True], default=new_total['active'])

    new_total = new_total.drop(new_total[new_total.duplicated(subset = ['id'], keep='first')].index)

    return(new_total)



with open(str(dir_path + '/dataframes.txt'), 'r') as f:
    file = f.read().splitlines()
dir_path_newest = file[-1]

exists = os.path.exists(str(dir_path_data + '/0_total.csv'))
if exists:
    df_total = pd.read_csv(str(dir_path_data + '/0_total.csv'), sep = ';')
    df_new = pd.read_csv(dir_path_newest, sep = ';')
    df_total_new = combine(df_total, df_new)
    df_total_new.to_csv(str(dir_path_data + '/0_total.csv'), sep = ';',
                        encoding = 'utf-8',
                        index = False
                       )
else:
    create = shutil.copy(dir_path_newest,
                         str(dir_path_data + '/0_total.csv'))
