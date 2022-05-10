"""
Script to read Excel with info on mapping of units as dataframe and save to pickle.
"""

import os
import pandas as pd
import pickle

from pathlib import Path

# set work directory to current module
PATH = Path(__file__).parent
os.chdir(PATH)

FILE_PATH_READ = PATH / 'unit_map 20210317.xlsx'
FILE_PATH_EXPORT = PATH / 'unit_map.pkl'

# read excel
df = pd.read_excel(FILE_PATH_READ, encoding='ISO-8859-1')
for col in list(set(df.columns) - set(['Unit'])):
    df[col] = df[col].str.split('|')  # split cell to list using "|" as a seperator
    df[col] = df[col].str.strip()

# export as pkl
pickle.dump(df, open(FILE_PATH_EXPORT, "wb"))
