# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
import sqlite3

import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None

def get_data(vehicle_url, city_code_url):
    # Load vehicle registration data
    print('Getting vehicle data..')
    data = pd.read_csv(vehicle_url, sep=';', encoding='latin-1', low_memory=False)
    df = data[data.sahkohybridi == True]  # hybrids only
    df.drop('sahkohybridi', axis=1, inplace=True)
    
    # City codes
    print('Getting city codes..')
    result = requests.get(city_code_url)
    soup = bs(result.content, 'lxml')
    rows = soup.find('table').find('tbody').find_all('tr')
    city_codes = {int(row.find_all('td')[0].text): row.find_all('td')[1].text
                  for row in rows}
    
    print('Processing..')
    def assign_city(x, city_codes):
        try:
            res = city_codes[int(x)]
        except:
            res = 'unknown'
        return(res.strip().lower())
    
    df['kuntanimi'] = df.kunta.apply(assign_city, args=(city_codes,))
    
    #df.info()
    #df.describe()
    #for col in df.columns: print(df[col].head(10))
    #for col in df.columns: print(col, len(df[col].unique()))
        
    # Drop mostly null and redundant/useless columns
    cols_to_drop = ['ajoneuvoryhma',
                    'ohjaamotyyppi',
                    'tieliikSuurSallKokmassa',
                    'vaihteidenLkm',
                    'ensirekisterointipvm', # kayttoonottopvm
                    'tyyppihyvaksyntanro',
                    'valmistenumero2',
                    'jarnro',
                    'variantti',
                    'versio',
                    'alue', # kunta
                    ]
    df.drop(cols_to_drop, axis=1, inplace=True)
    
    # Consolidate manufacturers
    def cons_manuf(x):
        x = ''.join(x.strip().split()).lower()
        if 'vw' in x:
            return('volkswagen')
        elif 'bmw' in x:
            return('bmw')
        elif 'ford' in x:
            return('ford')
        elif 'tesla' in x:
            return('tesla')
        else:
            return(x)
    df['merkki'] = df.merkkiSelvakielinen.apply(cons_manuf)
    
    ## Fill meter reading by registration year mean
    #df.kayttoonottopvm = pd.to_datetime(
    #        df.kayttoonottopvm, format='%Y%m%d', errors='coerce')
    #df = df[df.kayttoonottopvm.notnull()] # few invalid dates
    #df['ko_vuosi'] = df.kayttoonottopvm.apply(lambda x: x.year)
    #df['matkamittarilukema'] = df.groupby('ko_vuosi').transform(
    #        lambda x: x.fillna(x.mean()))['matkamittarilukema']
    #df = df[df.matkamittarilukema < 500000]
    
    try:
        from fancyimpute import MICE
        # Fill numeric cols by MICE
        df_numeric = df.select_dtypes(include=[np.float])
        float_cols = df_numeric.as_matrix()
        df_filled = pd.DataFrame(MICE().complete(float_cols))
        df_filled.columns = df_numeric.columns
        df_filled.index = df_numeric.index
        df[df_numeric.columns] = df_filled
        df.reset_index(drop=True, inplace=True)
        # Fill the rest by most common (few missing values)
        df = df.apply(lambda x: x.fillna(x.value_counts().index[0]))
    except ImportError:
        print('No imputation')
        
    # Result to db
    db_file = 'trafi.db'
    con = sqlite3.connect(db_file)
    df.to_sql('hybrids', con, if_exists='replace', index=False)
    con.close()
    print('Results saved')


if __name__ == '__main__':
    cars = r'http://trafiopendata.97.fi/opendata/180117_tieliikenne_5_1.zip'
    city_codes = r'https://www.tilastokeskus.fi/meta/luokitukset/kunta/001-2018/index.html'
    get_data(cars, city_codes)
    