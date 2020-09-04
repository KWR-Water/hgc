# -*- coding: utf-8 -*-
"""
Created on Sun Jul 26 21:55:57 2020

@author: schanma
"""
import pytest
import pandas as pd
from pathlib import Path
import pickle as pckl
import hgc
import os
from hgc import ner 
from hgc import io
import tests

def test_ner():
    ''' to test whether the function ner can generate correctly mapped features and units '''
    # WD = os.path.join(os.path.dirname(os.path.realpath(__file__)))  # set work directory to current module
    WD = WD = Path(tests.__file__).parent
    # os.chdir(WD) @ Martin K: why do we have to change dir here?
    # @Xin/ MartinK: Test if all HGC features are included in hgc_io.default_features()
    df_temp = pd.read_excel(WD / 'tests/testfile1_io.xlsx')
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
    WD = Path(__file__).cwd()
    # get feature_map and unit_map for testing
    df_temp = pd.read_excel(WD / 'tests/testfile1_io.xlsx')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    # define input dictionary
    dct1_arguments = {
        'file_path': str(WD / 'tests/testfile1_io.xlsx'),
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
    assert max(df1_hgc.min()) < 1.001
    # NOTE: "As" 2nd column not yet correctly read !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def test_default_feature_units():
    io.default_feature_units()

def test_io_stacked():
    '''test stacked shape'''
    WD = Path(__file__).cwd()
    # get feature_map and unit_map for testing
    df_temp = pd.read_excel(WD / 'tests/testfile1_io.xlsx')
    feature_map, feature_unmapped, df_feature_map = hgc.ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, slice(5, 999)].dropna()))
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, slice(5, 999)].dropna()))
    dct2_arguments = {
        'file_path': str(WD / 'tests/testfile1_io.xlsx'),
        'sheet_name': 'stacked',
        'shape': 'stacked',
        'slice_header': [2, slice(2, 9)],
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