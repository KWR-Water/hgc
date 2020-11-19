"""
Reading data for WB, PRO, 
for kennisimpulse project
to read data from province, water companies, and any other sources
Created on Sun Jul 26 21:55:57 2020

@author: Xin Tian 
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import pickle as pckl
from hgc import ner 
from hgc import io
import tests
# import xlsxwriter

def _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual):
    # generate mapped/unmapped features and units 
    df_feature_map = pd.DataFrame(feature_map.items(), columns=['Original feature', 'New feature'])
    df_feature_map.loc[:, 'Flag'] = 'HGC mapping'
    df_feature_unmap = pd.DataFrame(feature_unmapped, columns=['Original feature'])
    df_feature_unmap.loc[:, 'Flag'] = 'Remaining unmappable items'
    df_feature_manmap = pd.DataFrame(feature_map_manual.items(), columns=['Original feature', 'New feature'])
    if not df_feature_manmap.empty:
        df_feature_manmap.loc[:, 'Flag'] = 'Manually added mapping from unmappable items (repeated entries)'    
    df_feature = pd.concat([df_feature_map, df_feature_unmap, df_feature_manmap])

    df_unit_map = pd.DataFrame(unit_map.items(), columns=['Original unit', 'New unit'])
    df_unit_map.loc[:, 'Flag'] = 'HGC mapping'
    df_unit_unmap = pd.DataFrame(unit_unmapped, columns=['Original unit'])
    if not df_unit_unmap.empty:
        df_unit_unmap.loc[:, 'Flag'] = 'Remaining unmappable items'
    df_unit_manmap = pd.DataFrame(unit_map_manual.items(), columns=['Original unit', 'New unit'])
    if not df_unit_manmap.empty:
        df_unit_manmap.loc[:, 'Flag'] = 'Manually added mapping from unmappable items (repeated entries)'
    df_unit = pd.concat([df_unit_map, df_unit_unmap, df_unit_manmap])

    return df_feature, df_unit

def test_province():
    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    WD = project_folder + r'/provincie_data_long_preprocessed.csv'
    df_temp = pd.read_csv(WD, encoding='ISO-8859-1', header=None)

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 25].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 26].dropna()))
    # add manual mapping
    feature_map_manual = {'pH': 'ph'}
    unit_map_manual = {'oC':'°C'}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

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
            'Monsternummer': 'SampleID', 
        },
        'map_features': {**feature_map, **feature_map_manual},
        'map_units': {**unit_map, **unit_map_manual},
    }
    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    # with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'+r'/provincie_processed.xlsx') as writer:    
    with pd.ExcelWriter(project_folder+r'/province_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


def test_KIWKZUID():
    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    WD = project_folder + r'/Opkomende stoffen KIWK Zuid_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Export KoW 2.0')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Export KoW 2.0',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 24)],
        'slice_data': [slice(1, n_row), slice(1, 24)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter omschrijving':'Feature',
            'Eenheid': 'Unit',
            'Gerapporteerde waarde': 'Value', 
            'Monstername datum': 'Datetime',
            'Analyse': 'SampleID',  # Analyse !?
            'Cas nummer': 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }
    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    # with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'+r'/provincie_processed.xlsx') as writer:    
    with pd.ExcelWriter(project_folder+r'/KIWK_Zuid_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


def test_KIWKVenloschol():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Opkomende stoffen KIWK Venloschol_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Export KoW 2.0')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Export KoW 2.0',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 24)],
        'slice_data': [slice(1, n_row), slice(1, 24)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter omschrijving':'Feature',
            'Eenheid': 'Unit',
            'Gerapporteerde waarde': 'Value', 
            'Monstername datum': 'Datetime',
            'Analyse': 'SampleID', 
            'Cas nummer': 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'\KIWK Venloschol_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')  

        
def test_KIWKRoerdalslenk():
    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    WD = project_folder + r'/Opkomende stoffen KIWK Roerdalslenk_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Export KoW 2.0')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Export KoW 2.0',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 24)],
        'slice_data': [slice(1, n_row), slice(1, 24)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter omschrijving':'Feature',
            'Eenheid': 'Unit',
            'Gerapporteerde waarde': 'Value', 
            'Monstername datum': 'Datetime',
            'Analyse': 'SampleID',  
            'Cas nummer': 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/KIWK Roerdalslenk_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   



def test_KIWKHeelBeegden():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Opkomende stoffen KIWK Heel Beegden_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Export KoW 2.0')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Export KoW 2.0',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 24)],
        'slice_data': [slice(1, n_row), slice(1, 24)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter omschrijving':'Feature',
            'Eenheid': 'Unit',
            'Gerapporteerde waarde': 'Value',
            'Monstername datum': 'Datetime',
            'Analyse': 'SampleID',  
            'Cas nummer': 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/KIWK Heel Beegden_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


 

def test_WBGR():
    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    WD = project_folder + r'/Kennisimpuls kwaliteitsdata_WBGR_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Resultaten')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 11].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Resultaten',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 12)],
        'slice_data': [slice(1, n_row), slice(1, 12)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter':'Feature',
            'Eenheid': 'Unit',
            'Resultaat': 'Value', # Gerapporteerde waarde, right?!
            'Datum': 'Datetime',
            'Beschrijving': 'SampleID',  # Analyse !?
            'CASnr' : 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/WBGR_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


 
def test_WMD():
    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Kennisimpuls kwaliteitsdata_WMD_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Resultaten WMD')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 11].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Resultaten WMD',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 12)],
        'slice_data': [slice(1, n_row), slice(1, 12)],
        'map_header': {
            **io.default_map_header(),
            'Monsterpunt': 'LocationID',
            'Parameter':'Feature',
            'Eenheid': 'Unit',
            'Resultaat': 'Value',
            'Datum': 'Datetime',
            'Beschrijving': 'SampleID',  
            'CASnr' : 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'\WMD_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


        
def test_BOexport_bewerkt():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/BOexport_bewerkt_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='BOexport_bewerkt')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 12].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 26].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'BOexport_bewerkt',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 41)],
        'slice_data': [slice(2, n_row), slice(1, 41)],
        'map_header': {
            **io.default_map_header(),
            'sampling.point': 'LocationID',
            'component':'Feature',
            'eenheid': 'Unit',
            'value.result': 'Value', 
            'sampled.date': 'Datetime',
            'sample.id': 'SampleID', 
            'cas_id' : 'CAS',
            'x_coordinaat' : 'X',
            'y_coordinaat' : 'Y',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'X', 'Y']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/BOexport_bewerkt_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   



       
def test_LIMS_Ruw_2017_2019():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/LIMS_Ruw_2017_2019_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Export Worksheet')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 9].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Export Worksheet',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 10)],
        'slice_data': [slice(1, n_row), slice(1, 10)],
        'map_header': {
            **io.default_map_header(),
            'POINTDESCR': 'LocationID',
            'ANALYTE':'Feature',
            'UNITS': 'Unit',
            'FINAL': 'Value', # Gerapporteerde waarde, right?!
            'SAMPDATE': 'Datetime',
            'TESTNO': 'SampleID',  # Analyse !?
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/LIMS_Ruw_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')        




def test_Oasen():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Data voor KIWK 2009-2019 Oasen_preprocessed.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='data 2009-2019')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 8].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 9].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'data 2009-2019',
        'shape': 'stacked',
        'slice_header': [1, slice(1, 14)],
        'slice_data': [slice(1, n_row), slice(1, 14)],

        'map_header': {
            **io.default_map_header(),
            'Monsterpuntcode': 'LocationID',
            'Omschrijving (Parameter)':'Feature',
            'Eenheid (Parameter)': 'Unit',
            'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
            'Monsternamedatum': 'Datetime',
            'Naam': 'SampleID',  # Analyse !?
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/Oasen_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   



    
def test_VitensMacro():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Vitens_PP_WP_Macro_2009_2020.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Sheet1')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, slice(8, None)].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[2, slice(8, None)].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Sheet1',
        'shape': 'wide',
        'slice_header': [1, slice(1, 8)],
        'slice_feature': [1, slice(8, 25)],
        'slice_unit': [2, slice(8, 25)],
        'slice_data': [slice(3, n_row), slice(1, 25)],

        'map_header': {
            **io.default_map_header(),
            # 'Monsterpuntcode': 'LocationID',
            # 'Omschrijving (Parameter)':'Feature',
            # 'Eenheid (Parameter)': 'Unit',
            # 'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
            'Datum': 'Datetime',
            'Naam': 'SampleID',  # Analyse !?
            'X coördinaat (m+NAP)' : 'X',
            'Y coördinaat (m+NAP)' : 'Y',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'Feature', 'Value', 'Unit', 'X', 'Y']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/VitensMacro_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   




def test_VitensOMIVE():
    project_folder = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'

    # project_folder = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'
    WD = project_folder + r'/Vitens_PP_WP_OMIVE_2009_2020.xlsx'
    df_temp = pd.read_excel(WD, header=None, sheet_name='Sheet1')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, slice(8, n_row)].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[2, slice(8, n_row)].dropna()))

    # add manual mapping
    feature_map_manual = {}
    unit_map_manual = {}

    # generate mapped/unmapped features and units 
    df_feature, df_unit = _generate_feature_unit_map(feature_map, feature_unmapped, feature_map_manual, unit_map, unit_unmapped, unit_map_manual)

    dct2_arguments = {
        'file_path': WD,
        'sheet_name': 'Sheet1',
        'shape': 'wide',
        'slice_header': [1, slice(1, 8)],
        'slice_feature': [1, slice(8, None)],
        'slice_unit': [2, slice(8, None)],
        'slice_data': [slice(3, n_row), slice(1, None)],

        'map_header': {
            **io.default_map_header(),
            # 'Monsterpuntcode': 'LocationID',
            # 'Omschrijving (Parameter)':'Feature',
            # 'Eenheid (Parameter)': 'Unit',
            # 'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
            'Datum': 'Datetime',
            'Naam': 'SampleID',  # Analyse !?
            'X coördinaat (m+NAP)' : 'X',
            'Y coördinaat (m+NAP)' : 'Y',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0]
    df2_select = df2[['Datetime', 'SampleID', 'Feature', 'Value', 'Unit', 'X', 'Y']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    with pd.ExcelWriter(project_folder+r'/VitensOMIVE_processed.xlsx') as writer:              
        df2_select.to_excel(writer, sheet_name='df_processed')
        df_feature.to_excel(writer, sheet_name='feature_map')
        df_unit.to_excel(writer, sheet_name='unit_map')
        df_feature_map.to_excel(writer, sheet_name='feature_reference')
        df_unit_map.to_excel(writer, sheet_name='unit_reference')   


test_province()
test_KIWKZUID()
test_KIWKVenloschol()
test_KIWKRoerdalslenk()
test_KIWKHeelBeegden()   
test_WBGR()
test_WMD()
test_BOexport_bewerkt()
test_LIMS_Ruw_2017_2019()
test_Oasen()
test_VitensMacro()
test_VitensOMIVE()
        