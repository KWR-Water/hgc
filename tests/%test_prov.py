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

#%%
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

def _whether_mapped_hgc(features, units, feature_map, unit_map):
    flag_feature = [('mappable' if feature in feature_map.keys() else 'unmappable') for feature in features]
    flag_unit = [('mappable' if unit in unit_map.keys() else 'unmappable') for unit in units]    
    return flag_feature, flag_unit

# def _export_data():
        # with pd.ExcelWriter(project_folder+r'/province_processed.xlsx') as writer:              
    #     df2_select.to_excel(writer, sheet_name='df_processed')
    #     df_feature.to_excel(writer, sheet_name='feature_map')
    #     df_unit.to_excel(writer, sheet_name='unit_map')
    #     df_feature_map.to_excel(writer, sheet_name='feature_reference')
    #     df_unit_map.to_excel(writer, sheet_name='unit_reference') 
    # pass

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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'Province'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "province.pckl", "wb" ) )


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
            'Analyse': 'SampleID', 
            'Cas nummer': 'CAS',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }
    df2 = io.import_file(**dct2_arguments)[0] 
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WML Zuid'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WML Zuid.pckl", "wb" ))
              

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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WML Venloschol'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WML Venloschol.pckl", "wb" ) )
    
        
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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WML Roerdalslenk'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WML Roerdalslenk.pckl", "wb" ) )



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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WML Heel Beegden'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WML Heel Beegden.pckl", "wb" ) )

 

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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WBGR'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WBGR.pckl", "wb" ) )


 
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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'WMD'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'CAS', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "WMD.pckl", "wb" ) ) 


        
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
            'filter_bovenkant_ref' : 'Z_upper',
            'filter_onderkant_ref' : 'Z_lower',
            'maaiveld_NAP' : 'Ground level',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0] 
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'BrabantWater'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 
                      'CAS', 'X', 'Y', 'Z_upper', 'Z_lower', 'Ground level', 
                      'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "BrabantWater.pckl", "wb" ) )
    
    
  
       
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
            'TESTNO': 'SampleID', 
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }
       
    df2 = io.import_file(**dct2_arguments)[0] 
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'Vitens_Lims'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "Vitens_Lims.pckl", "wb" ) ) 



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
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'Oasen'
    df2_select = df2[['Datetime', 'SampleID', 'LocationID', 'Feature', 'Value', 'Unit', 'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "Oasen.pckl", "wb" ) ) 

    
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
            'Maaiveld hoogte (m+NAP)' : 'Ground level',
            'Bovenkant filter': 'Z_upper',	 
            'Onderkant filter': 'Z_lower',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},

    }

    df2 = io.import_file(**dct2_arguments)[0] 
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'Vitens_Macro'
    df2_select = df2[['Datetime', 'SampleID', 'Feature', 'Value', 'Unit', 
                      'X', 'Y', 'Z_upper', 'Z_lower', 'Ground level', 
                      'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "VitensMacro.pckl", "wb" ) )



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
            'Maaiveld hoogte (m+NAP)' : 'Ground level',
            'Bovenkant filter': 'Z_upper',	 
            'Onderkant filter': 'Z_lower',
        },
        'map_features': {**feature_map},
        'map_units': {**unit_map},
    }

    df2 = io.import_file(**dct2_arguments)[0] 
    flag_feature, flag_unit = _whether_mapped_hgc(df2['Feature_orig'], df2['Unit_orig'], feature_map, unit_map)
    df2.loc[:, 'Flag feature'] = flag_feature
    df2.loc[:, 'Flag unit'] = flag_unit 
    df2.loc[:, 'Source'] = 'Vitens_OMIVE'
    df2_select = df2[['Datetime', 'SampleID', 'Feature', 'Value', 'Unit', 
                      'X', 'Y', 'Z_upper', 'Z_lower', 'Ground level', 
                      'Flag feature', 'Flag unit', 'Source']].reset_index(drop=True)
    df2_hgc = io.stack_to_hgc(df2)
    pckl.dump([df2, df2_select, df2_hgc], open( "VitensOMIVE.pckl", "wb" ) )

# test_province()
# test_KIWKZUID()
# test_KIWKVenloschol()
# test_KIWKRoerdalslenk()
# test_KIWKHeelBeegden()   
# test_WBGR()
# test_WMD()
test_BOexport_bewerkt()
test_LIMS_Ruw_2017_2019()
test_Oasen()
test_VitensMacro()
test_VitensOMIVE()


#%% data with metadata information
[df_pro_full, df_pro, df1_pro_hgc]  = pckl.load(open( "province.pckl", "rb" ))
[df_WML1_full, df_WML1, df_WML1_hgc]  = pckl.load(open( "WML Heel Beegden.pckl", "rb" ))
[df_WML2_full, df_WML2, df_WML2_hgc]  = pckl.load(open( "WML Roerdalslenk.pckl", "rb" ))
[df_WML3_full, df_WML3, df_WML3_hgc]  = pckl.load(open( "WML Venloschol.pckl", "rb" ))
[df_WML4_full, df_WML4, df_WML4_hgc]  = pckl.load(open( "WML Zuid.pckl", "rb" ))
[df_WBGR_full, df_WBGR, df_WBGR_hgc]  = pckl.load(open( "WBGR.pckl", "rb" ))
[df_WMD_full, df_WMD, df_WMD_hgc]  = pckl.load(open( "WMD.pckl", "rb" ))
[df_Oasen_full, df_Oasen, df_Oasen_hgc]  = pckl.load(open( "Oasen.pckl", "rb" ))
[df_LIM_full, df_LIM, df_LIM_hgc]  = pckl.load(open( "Vitens_Lims.pckl", "rb" ))

df_wMD = pd.concat([df_pro, df_WML1, df_WML2, df_WML3, df_WML4,
                    df_WBGR, df_WMD, df_Oasen, df_LIM])
df_wMD.to_csv('Data with metadata.csv', index=False, encoding='utf-32')


#%% data with direct X Y Z
[df_BW_full, df_BW, df_BW_hgc]  = pckl.load(open( "BrabantWater.pckl", "rb" ))
[df_V1_full, df_V1, df_V1_hgc]  = pckl.load(open( "VitensOMIVE.pckl", "rb" ))
[df_V2_full, df_V2, df_V2_hgc]  = pckl.load(open( "VitensMacro.pckl", "rb" ))
df_wXYZ = pd.concat([df_BW, df_V1, df_V2])
df_wXYZ.to_csv('Data with XYZ.csv', index=False, encoding='utf-32')





