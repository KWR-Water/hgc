# -*- coding: utf-8 -*-
"""
Reading data for WB, PRO, 
for kennisimpulse project
Created on Sun Jul 26 21:55:57 2020

@author: Xin Tian 
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import pickle as pckl
import hgc
import os
from hgc import ner 
from hgc import io
import tests
# import xlsxwriter

def test_province():
    # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
    WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/provincie_data_long_preprocessed.csv'
    df_temp = pd.read_csv(WD, encoding='ISO-8859-1', header=None)

    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 25].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 26].dropna()))
    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'stacked',
        'shape': 'stacked',
        'slice_header': [1, slice(1, None)],
        'slice_data': [slice(1, n_row), slice(1, None)],
        'map_header': {
            **io.default_map_header(),
            'MeetpuntId': 'LocationID',
            'parameter':'Feature',
            'eenheid': 'Unit',
            'waarde': 'Value',
            'Opgegeven bemonstering datum': 'Datetime',
            'Monsternummer': 'SampleID',  # "SampleID" already exists as header, but contains wrong date. Use "Sample number" as "SampleID"
            # 'SampleID': None  # otherwise exists twice in output file
        },
        'map_features': {**feature_map,'pH(1)':'pH'},
        'map_units': {**unit_map, 'oC':'°C'},
    }
    df2 = io.import_file(**dct2_arguments)[0]
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/provincie.xlsx') as writer:  
        df2.to_excel(writer, sheet_name='df_prov')
        df2_hgc.to_excel(writer, sheet_name='hgc_prov')

    # import xlsxwriter
