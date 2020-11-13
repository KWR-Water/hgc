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

def test_province():
    # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
    # WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'+'/provincie_data_long_preprocessed.csv'
    WD = r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'+'/provincie_data_long_preprocessed.csv'
    df_temp = pd.read_csv(WD, header=None, encoding='ISO-8859-1')

    # define the nrow here 
    n_row = None    
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 25].dropna()))
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 26].dropna()))
    
    feature_map_manual = {}
    unit_map_manual = {'oC':'°C'}

    # create a df to record what has been mapped and what has not
    df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
    if not not feature_unmapped:
        df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
    if not not unit_unmapped:
        df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))
    if not not feature_map_manual:
        df_map = df_map.join(pd.DataFrame(feature_map_manual.keys(), columns=['Manually added feature mapping_from']))
        df_map = df_map.join(pd.DataFrame(feature_map_manual.values(), columns=['Manually added feature mapping_to']))
    if not not unit_map_manual:
        df_map = df_map.join(pd.DataFrame(unit_map_manual.keys(), columns=['Manually added unit mapping_from']))
        df_map = df_map.join(pd.DataFrame(unit_map_manual.values(), columns=['Manually added unit mapping_to']))


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
    df2_hgc = io.stack_to_hgc(df2)
    # with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse'+r'/provincie_processed.xlsx') as writer:    
    with pd.ExcelWriter(r'D:\DBOX\Dropbox\008KWR\0081Projects\kennisimpulse'+r'/provincie_processed2.xlsx') as writer:              
        df2.to_excel(writer, sheet_name='df_prov')
        df_map.to_excel(writer, sheet_name='mapAndUnmap')
        df_feature_map.to_excel(writer, sheet_name='feature_map')
        df2_hgc.to_excel(writer, sheet_name='hgc_prov')


# def test_KIWKZUID():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     df_temp = pd.read_csv(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Export KoW 2.0',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 24)],
#         'slice_data': [slice(1, n_row), slice(1, 24)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter omschrijving':'Feature',
#             'Eenheid': 'Unit',
#             'Gerapporteerde waarde': 'Value', # Gerapporteerde waarde, right?!
#             'Monstername datum': 'Datetime',
#             'Analyse': 'SampleID',  # Analyse !?
#             # 'SampleID': None  # otherwise exists twice in output file
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'oC':'°C'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#         df2.to_excel(writer, sheet_name='KIWK_Zuid')
#         df2_hgc.to_excel(writer, sheet_name='hgc_KIWK_Zuid')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')

# def test_KIWKVenloschol():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Venloschol_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Export KoW 2.0',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 24)],
#         'slice_data': [slice(1, n_row), slice(1, 24)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter omschrijving':'Feature',
#             'Eenheid': 'Unit',
#             'Gerapporteerde waarde': 'Value', # Gerapporteerde waarde, right?!
#             'Monstername datum': 'Datetime',
#             'Analyse': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l atrazine-D5':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Venloschol_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_KIWK Venloschol')
#         df2.to_excel(writer, sheet_name='KIWK Venloschol')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')
        
# def test_KIWKRoerdalslenk():
#     WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Roerdalslenk_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Export KoW 2.0',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 24)],
#         'slice_data': [slice(1, n_row), slice(1, 24)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter omschrijving':'Feature',
#             'Eenheid': 'Unit',
#             'Gerapporteerde waarde': 'Value', # Gerapporteerde waarde, right?!
#             'Monstername datum': 'Datetime',
#             'Analyse': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Roerdalslenk_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_KIWK Roerdalslenk')
#         df2.to_excel(writer, sheet_name='KIWK Roerdalslenk')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')       
        
# def test_KIWKHeelBeegden():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Heel Beegden_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 20].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 21].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Export KoW 2.0',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 24)],
#         'slice_data': [slice(1, n_row), slice(1, 24)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter omschrijving':'Feature',
#             'Eenheid': 'Unit',
#             'Gerapporteerde waarde': 'Value', # Gerapporteerde waarde, right?!
#             'Monstername datum': 'Datetime',
#             'Analyse': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Opkomende stoffen KIWK Heel Beegden_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_KIWKHeelBeegden')
#         df2.to_excel(writer, sheet_name='KIWKHeelBeegden')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')             
        
# def test_WBGR():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Kennisimpuls kwaliteitsdata_WBGR_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1', sheet_name='Resultaten')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 11].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Resultaten',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 12)],
#         'slice_data': [slice(1, n_row), slice(1, 12)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter':'Feature',
#             'Eenheid': 'Unit',
#             'Resultaat': 'Value', # Gerapporteerde waarde, right?!
#             'Datum': 'Datetime',
#             'Beschrijving': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Kennisimpuls kwaliteitsdata_WBGR_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_WBGR')
#         df2.to_excel(writer, sheet_name='WBGR')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')             
        
# def test_WMD():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Kennisimpuls kwaliteitsdata_WMD_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1', sheet_name='Resultaten WMD')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 11].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Resultaten WMD',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 12)],
#         'slice_data': [slice(1, n_row), slice(1, 12)],
#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpunt': 'LocationID',
#             'Parameter':'Feature',
#             'Eenheid': 'Unit',
#             'Resultaat': 'Value', # Gerapporteerde waarde, right?!
#             'Datum': 'Datetime',
#             'Beschrijving': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Kennisimpuls kwaliteitsdata_WMD_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_WMD')
#         df2.to_excel(writer, sheet_name='WMD')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')             
        
# def test_BOexport_bewerkt():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/BOexport_bewerkt_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 12].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 26].dropna()))
 
#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'BOexport_bewerkt',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 41)],
#         'slice_data': [slice(2, n_row), slice(1, 41)],
#         'map_header': {
#             **io.default_map_header(),
#             'sampling.point': 'LocationID',
#             'component':'Feature',
#             'eenheid': 'Unit',
#             'value.result': 'Value', # Gerapporteerde waarde, right?!
#             'sampled.date': 'Datetime',
#             'sample.id': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/BOexport_bewerkt_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_BOexport')
#         df2.to_excel(writer, sheet_name='BOexport')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')             
        
# test_BOexport_bewerkt()

# def test_LIMS_Ruw_2017_2019():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/LIMS_Ruw_2017_2019_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 6].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 9].dropna()))

#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Export Worksheet',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 10)],
#         'slice_data': [slice(1, n_row), slice(1, 10)],

#         'map_header': {
#             **io.default_map_header(),
#             'POINTDESCR': 'LocationID',
#             'ANALYTE':'Feature',
#             'UNITS': 'Unit',
#             'FINAL': 'Value', # Gerapporteerde waarde, right?!
#             'SAMPDATE': 'Datetime',
#             'TESTNO': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l Hxdcn-d34':'µg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/LIMS_Ruw_2017_2019_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_LIMS_Ruw_2017_2019')
#         df2.to_excel(writer, sheet_name='LIMS_Ruw_2017_2019')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')             
        

# def test_Oasen():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/preprocessed/Oasen_preprocessed.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 8].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[slice(2, n_row), 9].dropna()))

#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'data2009-2019',
#         'shape': 'stacked',
#         'slice_header': [1, slice(1, 14)],
#         'slice_data': [slice(1, n_row), slice(1, 14)],

#         'map_header': {
#             **io.default_map_header(),
#             'Monsterpuntcode': 'LocationID',
#             'Omschrijving (Parameter)':'Feature',
#             'Eenheid (Parameter)': 'Unit',
#             'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
#             'Monsternamedatum': 'Datetime',
#             'Naam': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map, 'µg/l paraoxon':'µg/l', 'µg/l C6H5OH': 'µg/l','mg/l Na-lauryl-SO4':'mg/l'},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/Oasen_processed.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_Oasen')
#         df2.to_excel(writer, sheet_name='Oasen')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')       


# def test_VitensMacro():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/preprocessed/Vitens_PP_WP_Macro_2009_2020.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, slice(8, None)].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[2, slice(8, None)].dropna()))

#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Sheet1',
#         'shape': 'wide',
#         'slice_header': [1, slice(1, 8)],
#         'slice_feature': [1, slice(8, 25)],
#         'slice_unit': [2, slice(8, 25)],
#         'slice_data': [slice(3, n_row), slice(1, 14)],

#         'map_header': {
#             **io.default_map_header(),
#             # 'Monsterpuntcode': 'LocationID',
#             # 'Omschrijving (Parameter)':'Feature',
#             # 'Eenheid (Parameter)': 'Unit',
#             # 'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
#             'Datum': 'Datetime',
#             'Naam': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/VitensMacro.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_VitenMacro')
#         df2.to_excel(writer, sheet_name='VitensMacro')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')  


# def test_VitensOMIVE():
#     # WD = Path(tests.__file__).parent / 'provincie_data_long_preprocessed.csv'
#     # WD = r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/Opkomende stoffen KIWK Zuid_preprocessed.csv'
#     WD = r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/preprocessed/Vitens_PP_WP_OMIVE_2009_2020.xlsx'
#     df_temp = pd.read_excel(WD, header=None, encoding='ISO-8859-1')
#     # define the nrow here 
#     n_row = None    
#     feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, slice(8, 819)].dropna()))
#     unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=list(df_temp.iloc[2, slice(8, 819)].dropna()))

#     # create a df to record what has been mapped and what has not
#     df_map = pd.DataFrame((feature_map.keys(),feature_map.values(),unit_map.keys(),unit_map.values()), index=['Feature','Mapped feature','Unit','Mapped unit']).transpose()
#     if not not feature_unmapped:
#         df_map = df_map.join(pd.DataFrame(feature_unmapped, columns=['Unmapped feature']))
#     if not not unit_unmapped:
#         df_map = df_map.join(pd.DataFrame(unit_unmapped, columns=['Unmapped unit']))

#     dct2_arguments = {
#         'file_path': WD,
#         'sheet_name': 'Sheet1',
#         'shape': 'wide',
#         'slice_header': [1, slice(1, 8)],
#         'slice_feature': [1, slice(8, None)],
#         'slice_unit': [2, slice(8, None)],
#         'slice_data': [slice(3, n_row), slice(1, None)],

#         'map_header': {
#             **io.default_map_header(),
#             # 'Monsterpuntcode': 'LocationID',
#             # 'Omschrijving (Parameter)':'Feature',
#             # 'Eenheid (Parameter)': 'Unit',
#             # 'Waarde numeriek': 'Value', # Gerapporteerde waarde, right?!
#             'Datum': 'Datetime',
#             'Naam': 'SampleID',  # Analyse !?
#         },
#         'map_features': {**feature_map,'pH(1)':'pH'},
#         'map_units': {**unit_map},
#     }
#     df2 = io.import_file(**dct2_arguments)[0]
#     df2_hgc = io.stack_to_hgc(df2)
#     # with pd.ExcelWriter(r'D:/DBOX/Dropbox/008KWR/0081Projects/kennisimpulse/KIWK_Zuid_processed.xlsx') as writer:          
#     with pd.ExcelWriter(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/VitensOMIVE.xlsx') as writer:          
#         df2_hgc.to_excel(writer, sheet_name='hgc_VitenOMIVE')
#         # df2.to_excel(writer, sheet_name='VitensOMIVE')
#         df_map.to_excel(writer, sheet_name='mapAndUnmap')  
#     df2.to_csv(r'C:\Users\beta6\Documents\Dropbox\008KWR\0081Projects\kennisimpulse/VitensOMIVE_ref.csv')    
        
        