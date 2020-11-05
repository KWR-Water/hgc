# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 14:29:55 2020

@author: schanma
"""



from pathlib import Path
from hgc import constants
import pandas as pd
import pubchempy as pcp

# WD = os.path.join(os.path.dirname(os.path.realpath(__file__)))  # set work directory to current module
# os.chdir(WD)

# %%
# Put hyphen before CAS number before reading it in Excel 
# (to prevent conversion of CAS to date format).

# df = pd.read_csv(WD + r'\SIKB_2020_02_06 original.csv', engine='python', sep=";", encoding='utf-8')
# df['CASnummer2'] = "'" + df['CASnummer']
# df.loc[df['Omschrijving']=='neon']

# df.to_csv('sikb_2020_02_06 with extra column.csv', encoding='utf-8')


# %%
# # Convert Excel with Feature and Alias to CSV.
# # If Excel is saved directly from CSV, then some symbols (e.g. latin symbols) are
# # saved incorretly as "?"

file_path = r'D:\DBOX\Dropbox\008KWR\0081Projects\HGC\Git\hgc-2\hgc\constants'

df = pd.read_excel(file_path + r'/default_features_alias.xlsx', 'HGCinput', skiprows=4)
                #    encoding='ISO-8859-1')
df.to_csv(file_path + r'/default_features_alias.csv', encoding='utf-8', index=False)

df = pd.read_excel(file_path + r'/default_units_alias.xlsx') #, encoding='ISO-8859-1')
df.to_csv(file_path + r'/default_units_alias.csv', encoding='utf-8', index=False)
