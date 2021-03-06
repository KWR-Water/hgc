# -*- coding: utf-8 -*-
"""
Created on Sep 3
Testing a simple example
@author: Xin Tian 
"""

import pandas as pd
from hgc import ner 
from hgc import io
from pathlib import Path

def test_exm_stacked():
    """
    ----------------------
    Step 1: ner.generate_feature_map()
    ----------------------
    First map the features in the original file, to feature names recognized by HGC.
    """

    # compile a list of features by slicing the original file
    lst_features = list(pd.read_excel('./tests/example1.xlsx', sheet_name='stacked')['Feature'])

    # automatically detect features using text recognition
    feature_map, feature_unmapped, df_feature_map = ner.generate_feature_map(entity_orig=lst_features)

    # check if features are correctly mapped
    assert(feature_map == {'chloride': 'Cl', 'nitrate (filtered)': 'NO3', 'manganese': 'Mn', 'nietrate': 'NO3'})

    # check for which features the algorithm was not able to find a match that met the minimum resemblance.
    assert(feature_unmapped == ['EC new sensor'])

    # The dataframe can be used to check in more detail the scores how well the original features were matched to HGC features. 
    # This can be handy if you want to identify common errors and update the underlying database.
    df_feature_map.head(5)

    """
    In this case we find that the algorithm was not able to find a match for one 
    of the features ('EC new sensor'). Hence, we need to adjust the mapping manually.
    """

    # manually adjust the mapping by merging with a user defined dictionary (optional)
    feature_map2 = {**feature_map, 'EC new sensor': 'ec_field'} 

    """
    ----------------------
    Step 2: hgc.io. generate_unit_map()
    ----------------------
    Next, we need to make a mapping for the units, using the same approach as for the features. 
    """
    lst_units = list(pd.read_excel(Path(__file__).cwd()/'tests/example1.xlsx', sheet_name='stacked')['Unit'])
    unit_map, unit_unmapped, df_unit_map = ner.generate_unit_map(entity_orig=lst_units)
    assert(unit_map == {'mg-N/L': 'mg/L N', 'mg/L': 'mg/L', 'ug/L': 'μg/L', 'μS/cm': 'μS/cm'})

    """
    ----------------------
    Step 3: hgc.io.import_file()
    ----------------------
    The third step is to read the original file and and convert the data to the desired 
    datamodel. This requires that we first indicate where to find the data and how to 
    convert it.
    """

    # Arguments defining where to find data
    slice_header = [0, slice(0, 6)]  # row 0
    slice_data = [slice(1, None)]  # row 1 till end of file. "None" indicates "end" here. 

    # Arguments how to convert the data

    # map_header -->  mapping how to adjust headers name
    # Note: The headers 'Value', 'Unit' and 'SampleID' are compulsory. Other headers can be any string
    map_header = {**io.default_map_header(), 
                'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}

    # map_features --> see step 1

    # map_units --> see step 2

    # feature_units -->  mapping of the desired units for each feature
    # For instance, we can inspect the default units for Cl, NO3 and ec_field
    assert(io.default_feature_units()['Cl'] == 'mg/L')
    assert(io.default_feature_units()['NO3'] == 'mg/L')
    assert(io.default_feature_units()['ec_field'] == 'mS/m')

    # column_dtype --> desired dtypefor columns
    # we will use the default dtype
    print(io.default_column_dtype())  # use default values

    """
    Now the we have defined all the arguments, let's import the data
    """

    df = io.import_file(file_path=str(Path(__file__).cwd()/'tests/example1.xlsx'),
                        sheet_name='stacked',
                        shape='stacked',
                        slice_header= slice_header,
                        slice_data=slice_data,
                        map_header=map_header,
                        map_features=feature_map2,
                        map_units=unit_map)[0]
    df.head(3) # imported data                     
    df_1 = io.import_file(file_path=str(Path(__file__).cwd()/'tests/example1.xlsx'),
                        sheet_name='stacked',
                        shape='stacked',
                        slice_header= slice_header,
                        slice_data=slice_data,
                        map_header=map_header,
                        map_features=feature_map2,
                        map_units=unit_map)[1]
    df_1.head(3) # duplication
    df_2 = io.import_file(file_path=str(Path(__file__).cwd()/'tests/example1.xlsx'),
                        sheet_name='stacked',
                        shape='stacked',
                        slice_header= slice_header,
                        slice_data=slice_data,
                        map_header=map_header,
                        map_features=feature_map2,
                        map_units=unit_map)[2]                        
    df_2.head(3) # nan values

    """
    ----------------------
    Step 4: hgc.io.to_hgc()
    ----------------------
    Finally, we need to pivot the stacked data to the wide format used by HGC.
    The default is to use 'LocationID', 'Datetime' and 'SampleID' as index.
    """
    df_hgc = io.stack_to_hgc(df)

def test_exm_wide(): 
    """
    ===================
    Example: import wide data
    ===================

    Next, we will import the same data, but from a ‘wide’ shaped file.
    Note that it is also possible to use a dataframe instead of excel or csv as input
    for hgc.io.import_file(). This requires using the argument “dataframe” instead of “file_name”.
    An advantage of this approach is to prevent repeatedly reading the input file .
    """

    df_temp = pd.read_excel(Path(__file__).cwd()/'tests/example1.xlsx', sheet_name='wide', header=None) # ignore headers!

    # step 1: generate feature map
    feature_map2, feature_unmapped2, df_feature_map2 = ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, 5:]))
    assert(feature_map2 == {'chloride': 'Cl', 'manganese': 'Mn', 'nietrate': 'NO3', 'nitrate (filtered)': 'NO3'})

    # step 2: generate unit map
    unit_map2, unit_unmapped2, df_unit_map2 = ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, 5:]))
    assert(unit_map2 == {'mg-N/L': 'mg/L N', 'mg/L': 'mg/L', 'ug/L': 'μg/L', 'μS/cm': 'μS/cm'})

    # step 3: import file
    df2 = io.import_file(dataframe=df_temp,
                            shape='wide',
                            slice_header=[3, slice(2, 5)],
                            slice_feature=[2, slice(5, None)],
                            slice_unit=[3, slice(5, None)],
                            slice_data=[slice(4, None)],
                            map_header={**io.default_map_header(), 'loc.': 'LocationID',
                                        'date': 'Datetime', 'sample': 'SampleID'},
                            map_features={**feature_map2, 'EC new sensor': 'ec_field'},
                            map_units=unit_map2)[0]

    # step 4: convert to wide format
    df2_hgc = io.stack_to_hgc(df2)

def test_mapping_features():
    """
    ===================
    Mapping feature
    ===================

    The funtions generate_feature_map() and generate_unit_map() use Named Entity
    Recognition (NER) techniques to match original entities to the entities used by HGC.
    It is based on the fuzzywuzzy module. And uses Levenshtein Distance to calculate the differences between
    original entities and HGC-compatible entities. Original entities are matched to the HGC-entity to which they
    have the least distance. A match is only succesful if the score based on the Levenstein Distance remains above
    a certain threshold.

    For the features, a default database has been provided with the module that contains
    both features and a selection of alias (synonyms). The NER function will try find which
    alias provides the best match (= highest score) for each original feature.
    """

    # Print first lines of default database for mapping features.
    print(ner.default_feature_alias_dutch_english.head())

    """
    By default, all columns are used except for 'CAS'.
    It is possible to change the selection of colums through the argument 'alias_cols'
    In the next example, we will attempt mapping using the CAS number.
    """

    # example with mapping with CAS number
    df_feature_alias = ner.generate_entity_alias(
        df=ner.entire_feature_alias_table,
        entity_col='Feature',
        alias_cols=['CAS'])

    df_temp = pd.read_excel(Path(__file__).cwd()/'tests/example1.xlsx', sheet_name='wide', header=None) # ignore headers!
    feature_map3, feature_unmapped3, df_feature_map3 =\
        ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, 5:]),
                                    df_entity_alias=df_feature_alias,
                                    match_method='exact')

    # check if features are correctly mapped
    print(feature_map3)

    """
    The results of the mapping with CAS number are very poor compared to the previous
    mapping. This is logical in this case, since there are no CAS numbers in the
    original file.

    Note that in this case we will adjust the argument 'match_method' to 'exact'
    This works faster, but features must be spelled exactly the same as in the feature list. The mapping method can be
    adjusted with the argument .

    It is also possible to load a user defined database with the argument
    'df_entity_alias'.

    ===================
    Mapping units
    ===================

    For mapping units, similar functionalities are availabe as for mapping features.
    Only with a differente database and alias_cols

    """
    # Print first lines of default database for mapping units.
    print(ner.default_unit_alias.head())

    """
    WARNING: 
    give pH as units '1'
    same for kve, pve, etc. replace them by '1' to prevent problems with NaN errors
    """