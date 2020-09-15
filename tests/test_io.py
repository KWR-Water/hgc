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
    # WD = os.path.join(os.path.dirname(os.path.realpath(__file__)))  # set work directory to current module
    WD = Path(tests.__file__).parent
    # @Xin/ MartinK: Test if all HGC features are included in hgc_io.default_features()
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    assert feature_map['Acidity'] == 'ph'
    assert feature_map['Electrical Conductivity'] == 'ec'
    assert unit_map['mS/m'] == 'mS/m'
    assert unit_map['μmol N/l'] == 'μmol/L N'
    # Next version:
    # # Add unit test of the "score" computed by the generate_untity_map function

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
    assert min(df1_hgc.min()) > 0.999
    assert max(df1_hgc.min()) < 1001
    # NOTE: "As" 2nd column not yet correctly read !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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
    assert min(df2_hgc.min()) > 0.999
    assert max(df2_hgc.min()) < 1.001

def test_Gilian_file():
    ''' test an example from Gilian '''
    WD = Path(tests.__file__).parent
    # get feature_map and unit_map for testing
    df_temp = pd.read_excel(WD / 'BO_exmp.xlsx')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(1, None), 6].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(1, None), 8].dropna()))
    dct3_arguments = {
        'file_path': str(WD / 'BO_exmp.xlsx'),
        'sheet_name': 'example',
        'shape': 'stacked',
        'slice_header': [0, slice(0, None)],
        'slice_data': [slice(1, None)],
        'map_header': {
            **hgc.io.default_map_header(),
            'sampled.date': 'Datetime',
            'sample.id': 'SampleID',  
            'eenheid': 'Unit',
            'value.result': 'Value',
            'component': 'Feature'
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df2 = hgc.io.import_file(**dct3_arguments)[0]
    df2_hgc = hgc.io.stack_to_hgc(df2)

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
def test_ner_default_feature_alias_dutch_english():
    ''' check the feature alias '''
    df_check = ner.default_feature_alias_dutch_english()
    df_check.head(15) # check combined dictionaries

def test_default_unit_alias():
    ''' check the unit alias '''
    df_check = ner.default_unit_alias()
    df_check.head(15)

def test_ner_generate_entity_alias():
    ''' check the function used for generating unit/feature'''
    df_check = ner.generate_entity_alias(
        df=ner.entire_unit_alias_table(),
        entity_col='Unit',
        alias_cols=['Unit'])

    df_check = ner.generate_entity_alias(
        df=ner.entire_unit_alias_table(),
        entity_col='Unit',
        alias_cols=['Alias (English)'])
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
    assert feature_map['Acidity'] == 'ph'
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
    df_temp = pd.read_excel(WD / 'testfile1_io.xlsx')
    feature_test = list(df_temp.iloc[2, slice(5, 20, 3)].dropna()) + ['SO3', 'no3', 'random_feature', 'strange_name', '1,2,3-trimethylbenzeen', '1,2,3,4-tetramethylbenzeen']
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=feature_test)
    # feature_test = ['NO3']

    entity_map, entity_unmapped, df_entity_map = ner.generate_entity_map(entity_orig=feature_test,
                        df_entity_alias=ner.default_feature_alias_dutch_english(),
                        entity_col='Feature',
                        string2whitespace=[],
                        string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                                         'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                                         'μ': 'u', 'µ': 'u', '%': 'percentage'},
                        string2remove=ner.strings2remove_from_features(),
                        strings_filtered_gem=ner._strings_filtered(),
                        entity_minscore=ner.default_feature_minscore(),
                        match_method='levenshtein')
    entity_map, entity_unmapped, df_entity_map













# def test_import_file():
#     # define a dictionary that contains information about the input file, which needs modification every time
#     # leave it empty if some keys are unknown in certain fields
#     case = 1

#     # define the following struct 'file_format' to start the program
#     if case == 1:
#         # These are the columns with sample data that the script will use. Other non-feature columns are dropped.
#         MAP_HEADER = {
#             'Sampling Date': 'Date',
#             'Sample Number': 'SampleID',  # the second value already exists as column. so must be removed first
#             'LocationID': 'LocationID',  # column name not adjusted.
#         }

#         # read default mappings for units/features/locations; should be defined by users themselves
#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_features', header=None)
#         mapped_features = dict(zip(x[0], x[1]))

#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_units', header=None)
#         mapped_units = dict(zip(x[0], x[1]))

#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_locations', header=None)
#         mapped_locations = dict(zip(x[0], x[1]))

#         # Example of configuration dictionary for importing Excel with WIDE shape data.
#         # idx = pd.IndexSlice
#         EXAMPLE1_FORMAT = {
#             'file_path': r'.\hgc\constants\default_mapping.xlsx',
#             'sheet_name': 'wide',
#             'shape': 'wide',
#             # 'slice_sample': [idx[9, 2:5], idx[8, 31:32]], # all slice has to be list here
#             # 'slice_feature': [idx[3, 5:31]],
#             # 'slice_unit': [idx[4, 5:31]],
#             # 'slice_data': [idx[10:23, 5:]],
#             'slice_sample': [[9, slice(2, 5)], [8, slice(31, 32)]],
#             'slice_feature': [3, slice(5, 31, None)],
#             'slice_unit': [4, slice(5, 31)],
#             'slice_data': [[slice(10, 23)], [slice(None, None)]],  # only row numbers, columns are ignored
#             # @Martin vd S: slice(5, None, None) can replace 999 thing. pd.IndexSlice returns the same slicing
#             # e.g. pd.IndexSlice[4:, :]
#             # >>>(slice(4, None, None), slice(None, None, None)) 
#             'map_header': MAP_HEADER,
#             'map_features': mapped_features,
#             'map_units': mapped_units,
#             'unit_conversion': UNIT_CONVERSION,
#             'user_defined_feature_units': {  # OPTIONAL INPUT
#                 'DEET': 'mg/L',
#                 'AMPA': 'mg/L',
#                 'Fe': 'μg/L',
#                 'Ca': 'mg/L',
#                 'NH4': 'mg/L',
#                 'NO2': 'mg/L',
#             },
#             'user_defined_format_colums': {  # OPTIONAL INPUT
#                 'Value': 'float64',
#                 'Feature': 'string',
#                 'Unit': 'string',
#                 'Date': 'date',
#                 'LocationID': 'string',
#                 'SampleID': 'float64',
#                 'X': 'float64',
#                 'Y': 'float64',
#             }            
#         }
#         df = import_file(**EXAMPLE1_FORMAT)
#         # export it to an excel spreadsheet
#         df.to_excel('test_example1.xlsx')
    
#     if case == 2:
#         #%% Test example 2: stacked format
#         MAP_HEADER2 = {
#             'SAMPLED_DATE': 'Date',
#             'SAMPLE_ID': 'SampleID',
#             'LOCATION': 'LocationID',
#             'COMPONENT': 'Feature',
#             'UNITS': 'Unit',
#             'REPORT_VALUE': 'Value',
#         }

#         # read default mappings for units/features/locations; should be defined by users themselves
#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_features', header=None)
#         mapped_features = dict(zip(x[0], x[1]))

#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_units', header=None)
#         mapped_units = dict(zip(x[0], x[1]))

#         x = pd.read_excel(r'.\hgc\constants\default_mapping.xlsx', sheet_name='map_locations', header=None)
#         mapped_locations = dict(zip(x[0], x[1]))

#         EXAMPLE2_FORMAT = {
#             'file_path': r'.\hgc\constants\default_mapping.xlsx',
#             'sheet_name': 'stacked',
#             'shape': 'stacked',
#             'slice_sample': [2, slice(2, 13)],
#             # 'slice_feature': [1, slice(12, 999999)], not needed
#             # 'slice_unit': [4, slice(12, 999999)], not needed
#             'slice_data': [[slice(3, 13)], [slice(2, None)]],
#             'map_header': MAP_HEADER2,
#             'map_features': mapped_features,
#             'map_units': mapped_units,
#             'unit_conversion': UNIT_CONVERSION,
#             'user_defined_feature_units': {  # OPTIONAL INPUT
#                 'DEET': 'mg/L',
#                 'AMPA': 'mg/L',
#                 'Fe': 'μg/L',
#                 'Ca': 'mg/L',
#                 'NH4': 'mg/L',
#                 'NO2': 'mg/L',
#             },
#             'user_defined_format_colums': {  # OPTIONAL INPUT
#                 'Value': 'float64',
#                 'Feature': 'string',
#                 'Unit': 'string',
#                 'Date': 'date',
#                 'LocationID': 'string',
#                 'SampleID': 'float64',
#                 'X': 'float64',
#                 'Y': 'float64',
#             }
#         }
#         df = import_file(**EXAMPLE2_FORMAT)
#         # export it to an excel spreadsheet
#         df.to_excel('test_example2.xlsx')
    
#     return df

def test_bas():
    '''test stacked shape'''
    WD = Path(tests.__file__).parent /'example2.xlsx'
    lst_features = list(pd.read_excel(WD, sheet_name='stacked')['Feature'])
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=lst_features)
    lst_units = list(pd.read_excel(WD, sheet_name='stacked')['Unit'])
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=lst_units)
    slice_header = [0, slice(0, 5)]  # row 0
    slice_data = [slice(1, None), slice(0, 5)]
    dct2_arguments = {
        'file_path': str(WD),
        'sheet_name': 'stacked',
        'shape': 'stacked',
        'slice_header': slice_header,
        'slice_data': slice_data,
        'map_header': {
            **hgc.io.default_map_header(), 'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df2 = hgc.io.import_file(**dct2_arguments)[0]
    df2_hgc = hgc.io.stack_to_hgc(df2)




