# -*- coding: utf-8 -*-
def test_hwl():
    """
    Created on Wed Sep 23 15:14:48 2020

    @author: griftba
    """
    import pandas as pd
    import hgc
    from hgc import ner 
    from hgc import io
    from pathlib import Path

    #pip install -U git+https://github.com/KWR-Water/hgc.git@HGC.io

    #    df_temp = pd.read_excel(r'./Chem_Data_bas.xlsx', sheet_name='Raai 2019-2020', header=None) # ignore headers!

    # step 1: generate feature map
    file_name = r'D:\DBOX\Dropbox\008KWR\0081Projects\QSAR_NER\testing_bas\Chem_Data_bas.xlsx'
    lst_features = list(pd.read_excel(file_name, sheet_name='Raai 2019-2020')['Parameter'])
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=lst_features)
    lst_units = list(pd.read_excel(file_name, sheet_name='Raai 2019-2020')['Unit'])
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=lst_units)
    slice_header = [0, slice(0, 8)]  # row 0
    slice_data = [slice(1, None), slice(0, 8)]
    dct2_arguments = {
        'file_path': file_name,
        'sheet_name': 'Raai 2019-2020',
        'shape': 'stacked',
        'slice_header': slice_header,
        'slice_data': slice_data,
        'map_header': {
            **io.default_map_header(), 'Date': 'Datetime', 'Sample': 'SampleID', 'Parameter':'Feature',
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df2 = io.import_file(**dct2_arguments)[0]


    dct2_arguments = {
        'file_path': file_name,
        'sheet_name': 'Raai 2019-2020',
        'shape': 'stacked',
        'slice_header': slice_header,
        'slice_data': slice_data,
        'map_header': {
            **io.default_map_header(), 'Date': 'Datetime', 'Sample': 'SampleID', 'Parameter':'Feature',
        },
        'map_features': feature_map,
        'map_units': unit_map,
    }
    df2_2 = io.import_file(**dct2_arguments)[2] 

    df2_DLV = hgc.io.stack_to_hgc(df2)

    df2_DLV.to_csv('DLV_raai2019_2020.csv')


    df2_DLV.hgc.make_valid()
    is_valid = df2_DLV.hgc.is_valid
    is_valid

    # Recognized HGC columns
    hgc_cols = df2_DLV.hgc.hgc_cols
    print(hgc_cols)

    sum_anions = df2_DLV.hgc.get_sum_anions_stuyfzand()

    water_types = df2_DLV.hgc.get_stuyfzand_water_type()
    print(water_types)
    bex = df2_DLV.hgc.get_bex()
    bex
