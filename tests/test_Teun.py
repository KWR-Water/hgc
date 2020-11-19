# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 11:39:40 2020

@author: tianxi
"""

import pandas as pd
import hgc
from hgc import ner
from hgc import io
from hgc import constants
from pathlib import Path
import os 

datadir          = r'\\nwg\dfs\projectdata\P402722_003\Grondwaterkwaliteit\WPFP'                   
datafile         = 'Overzicht_resultaten_peilbuizen-WPFP.xlsx'                   

file_path        = os.path.join(datadir,datafile)                                 
TOT              = pd.read_excel(io=file_path,sheet_name='Totaal',     skiprows=0,index_col='Name')          
lst_features = list(TOT)

feature_map, feature_unmapped, TOT_feature_map = hgc.ner.generate_feature_map(entity_orig=lst_features)


