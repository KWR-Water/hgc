# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 13:59:40 2020

@author: beta6
"""
#pip install -U git+https://github.com/KWR-Water/hgc.git@HGC.io

import pytest
import pandas as pd
# import os
from pathlib import Path
from hgc import constants
from hgc import convertFeatureNames as cf
import tests
def test_feature_map():
    # file_path = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\HGC\Git\hgc-2\hgc\constants\default_features_alias.xlsx'
    file_path = Path(constants.__file__).parent / 'default_features_alias.xlsx'
    df = pd.read_excel(file_path, sheet_name='HGC_input_conv')
    df_pubchem = cf.convert_feature_to_standard_pubchem(df.iloc[400:410,:5])
    # export it to an excel spreadsheet
    file_path = Path(constants.__file__).parent / 'default_features_alias99.xlsx'
    df_pubchem.to_excel(file_path) # cannot call xlsxwrite for some unknown reasons
