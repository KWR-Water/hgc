# -*- coding: utf-8 -*-
"""
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
# from googletrans import Translator


def test_ner():
    ''' to test whether the function ner can generate correctly mapped features and units '''
    WD = Path(tests.__file__).parent
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx', sheet_name='wide')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    assert feature_map['Acidity'] == 'Acidity'
    assert feature_map['Electrical Conductivity'] == 'ec'
    assert unit_map['mS/m'] == 'mS/m'
    assert unit_map['μmol N/l'] == 'μmol/L N'

def test_io_wide():
    '''test wide-shaped file'''
    WD = Path(tests.__file__).parent
    # get feature_map and unit_map for testing
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx', sheet_name='wide')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    # define input dictionary
    dct1_arguments = {
        'file_path': str(WD / 'testfile1_io.xlsx'),
        'sheet_name': 'wide',
        'shape': 'wide',
        'slice_header': [[9, slice(2, 5)], [8, slice(32, 33)]],
        'slice_feature': [3, slice(5, 32)],
        'slice_unit': [4, slice(5, 32)],
        'slice_data': [[slice(10, 22)], [slice(24, 25), slice(None, None)]],
        'map_header': {
            **hgc.io.default_map_header(),
            'Sampling Date': 'Datetime',
            'Sample Number': 'SampleID',  # "SampleID" already exists as header, but contains wrong date. Use "Sample number" as "SampleID"
            'SampleID': None  # otherwise exists twice in output file
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df1, df1_dropna, df1_dropduplicates = hgc.io.import_file(**dct1_arguments)
    df1_hgc = hgc.io.stack_to_hgc(df1)
    assert df1_hgc.iloc[0]['PO4'] == '<1.0'
    assert df1_hgc.iloc[0]['As'] == 1000

def test_io_stacked():
    '''test stacked shape'''
    WD = Path(tests.__file__).parent
    # get feature_map and unit_map for testing
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx', sheet_name='stacked')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(3, None), 6].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(3, None), 7].dropna()))
    dct2_arguments = {
        'file_path': str(WD / 'testfile1_io.xlsx'),
        'sheet_name': 'stacked',
        'shape': 'stacked',
        'slice_header': [2, slice(2, None)],
        'slice_data': [slice(3, None)],
        'map_header': {
            **hgc.io.default_map_header(),
            'Sampling Date': 'Datetime',
            'Sample Number': 'SampleID',  # "SampleID" already exists as header, but contains wrong date. Use "Sample number" as "SampleID"
            'SampleID': None  # otherwise exists twice in output file
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df2 = hgc.io.import_file(**dct2_arguments)[0]
    df2_hgc = hgc.io.stack_to_hgc(df2)

    assert df2_hgc.iloc[0]['PO4'] == '<1.0'
    # assert min(df2_hgc.min()) > 0.999
    # assert max(df2_hgc.min()) < 1.001

# def test_Gilian_file():
#     ''' test an example from Gilian '''
#     WD = Path(tests.__file__).parent
#     # get feature_map and unit_map for testing
#     df_temp = pd.read_excel(WD / 'BO_exmp.xlsx')
#     feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(1, None), 6].dropna()))
#     unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(1, None), 8].dropna()))
#     dct3_arguments = {
#         'file_path': str(WD / 'BO_exmp.xlsx'),
#         'sheet_name': 'example',
#         'shape': 'stacked',
#         'slice_header': [0, slice(0, None)],
#         'slice_data': [slice(1, None)],
#         'map_header': {
#             **hgc.io.default_map_header(),
#             'sampled.date': 'Datetime',
#             'sample.id': 'SampleID',  
#             'eenheid': 'Unit',
#             'value.result': 'Value',
#             'component': 'Feature'
#         },
#         'map_features': feature_map,
#         'map_units': unit_map,
#     }
#     df2 = hgc.io.import_file(**dct3_arguments)[0]
#     df2_hgc = hgc.io.stack_to_hgc(df2)

def test_io_default_features():
    ''' testing whether features have right units '''
    dct_feature = io.default_feature_units()
    assert dct_feature['Cl'] == 'mg/L'   
    assert dct_feature['Fe'] == 'mg/L'      
    assert dct_feature['Ca'] == 'mg/L'      
    assert dct_feature['Na'] == 'mg/L'      
    assert dct_feature['Mn'] == 'mg/L'      
    assert dct_feature['NH4'] == 'mg/L'      
    assert dct_feature['NO2'] == 'mg/L'      
    assert dct_feature['NO3'] == 'mg/L'      
    assert dct_feature['Al'] == 'μg/L'       
    assert dct_feature['As'] == 'μg/L'      
    assert dct_feature['ec'] == 'μS/cm'      
    assert dct_feature['ec_field'] == 'μS/cm'         
    assert dct_feature['ph'] == '1'    

def test_ner_units():
    ''' testing whether ner returns right units and features '''
    print(hgc.ner.generate_unit_map(entity_orig=['mg/l NH4'])[0])
    print(hgc.ner.generate_unit_map(entity_orig=['    mg/l NH4', 'mg/L NO3   '])[0]) # remove whitespace before unit

def test_ner_entire_feature_alias_table():
    ''' check the loadings from "default_features_alias.csv" '''
    df_check = ner.entire_feature_alias_table()
    df_check.head(4)
    #   Feature        CAS REMARK  ... SIKB_Omschrijving SIKB_CASnummer     SIKB_Group
    # 0     CH4    74-82-8    NaN  ...           methaan       '74-82-8  ChemischeStof
    # 1     H2S   6/4/7783    NaN  ...  waterstofsulfide     '7783-06-4  ChemischeStof
    # 2     CO2   124-38-9    NaN  ...       kooldioxide      '124-38-9  ChemischeStof
    # 3     CO3  3812-32-6    NaN  ...         carbonaat     '3812-32-6  ChemischeStof
    # df_check.columns
    # Index(['Feature', 'CAS', 'REMARK', 'DefaultUnits', 'HGC', 'Category',
    #     'IUPAC (Dutch)', 'IUPAC (English)', 'IUPAC (CAS)',
    #     'User defined (Dutch)', 'User defined (English)',
    #     'User defined Category', 'SIKB_Code', 'SIKB_Omschrijving',
    #     'SIKB_CASnummer', 'SIKB_Group'],
    #     dtype='object')
    pass

def test_ner_entire_unit_alias_table():
    ''' check the loadings from "entire_unit_alias_table.csv" '''
    df_check = ner.entire_unit_alias_table()
    df_check.head(10)
    #     Unit Alias (English) Alias (Dutch) Unnamed: 3
    # 0    1             NaN           NaN        NaN
    # 1    1              na           nvt        NaN
    # 2    %      percentage           NaN        NaN
    # 3  min          Minute        minuut        NaN
    # 4    h            hour           uur        NaN
    pass

#%% individual tests for ner
def test_ner_generate_feature_alias():
    ''' check the feature alias '''
    df_check = ner.generate_feature_alias()
    df_check.head(15) # check combined dictionaries

def test_default_unit_alias():
    ''' check the unit alias '''
    df_check = ner.generate_unit_alias()
    df_check.head(15)

def test_ner_generate_entity_alias():
    ''' check the function used for generating unit/feature'''
    df_check = ner.generate_entity_alias(
        df=ner.entire_feature_alias_table(),
        entity_col='Feature',
        alias_cols=['Feature', 'IUPAC',
                    'UserDefined_Dutch', 'UserDefined_English',
                    'SIKBcode', 'SIKBomschrijving'])
    df_check.head(15)

    df_check = ner.generate_entity_alias(
        df=ner.entire_unit_alias_table(),
        entity_col='Unit',
        alias_cols=['Alias (English)'])
    df_check.head(15)
    pass

def test_generate_feature2remove():
    lst_check = ner.generate_feature2remove()
    print(lst_check[:10]) # find atoms, ions, and others


def test_strings2remove_from_units():
    lst_check = ner.strings2remove_from_units()
    print(lst_check[:10]) # given feature names ['N', 'P', 'S', 'Si'] removed.

def test_strings_filtered():
    lst_check = ner._strings_filtered()
    print(lst_check[:10])

def test_interp1d_fill_value():
    dct = {
        1: 100, # exactly matching
        3: 100, # exactly matching
        4: 75, # at most one mismatching
        5: 80, # at most one mismatching
        6: 66, # at most two mismatching
        8: 75  # at most two mismatching
    }
    df_test = pd.DataFrame({'x': list(dct.keys()), 'y': list(dct.values())})
    func = ner._interp1d_fill_value(df_test.x, df_test.y)
    assert func(1) == 100.
    assert func(2) == 100.
    assert func(5) == 80
    assert func(7) == np.mean([66, 75])
    assert func(100) == 75.

def test_cleanup_alias():
    df = pd.DataFrame({'feature':['SO4', 'SO4', '\t'], 'Unit':['Mg/L', 'mg/L', '\n']})
    df_check = ner._cleanup_alias(df, col='feature')
    pass

def test_generate_feature_map():
    WD = Path(tests.__file__).parent
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    assert feature_map['Acidity'] == 'Acidity'
    assert feature_map['Electrical Conductivity'] == 'ec'

def test_generate_unit_map():
    WD = Path(tests.__file__).parent
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx')
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    assert unit_map['mS/m'] == 'mS/m'
    assert unit_map['μmol N/l'] == 'μmol/L N'
    assert unit_map['mg-N/l'] == 'mg/L N'

def test_entity_map():
    WD = Path(tests.__file__).parent
    # df_temp = pd.read_excel(WD / 'testfile1_io.xlsx')
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx', sheet_name='wide')
    feature_test = list(df_temp.iloc[2, slice(5, 20, 3)].dropna()) + ['SO3', '124TClBen', 'Flumethasonacetaat', 'strange_name']
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=feature_test)
    # feature_test = ['NO3']
    print(feature_map['Flumethasonacetaat'])

def test__translate_matching():
    df_entity_orig4_f=pd.DataFrame()
    df_entity_orig4_f.loc[0, 'Feature_orig'] = '1,2,3-trimethylbenzeen'
    df_entity_orig4_f.loc[1, 'Feature_orig'] = '1,2,3,4-tetramethylbenzeen'
    ner._translate_matching(df_entity_orig4_f, match_method = 'levenshtein', entity_col = 'feature', trans_from = 'nl', trans_to = 'en')


