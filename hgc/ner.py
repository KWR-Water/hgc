# -*- coding: utf-8 -*-
"""
Routine for recognizing features and units using NER.
Xin Tian, Martin van der Schans
KWR, April-July 2020
"""

import copy
import numpy as np
import pandas as pd
import scipy.interpolate
from pathlib import Path
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from hgc import constants

# %% Defaults

# @Tin: adapt the following function so that the table gets installed with the package.
def entire_feature_alias_table():
    """Dataframe with HGC features and various columns with alias (synonyms) for these features.

    Return
    ------
    Dataframe :
        The dataframe has a "Feature" column. And various other columns with Alias
        for these features including CAS, SIKB, Dutch Alias, English Alias.
        Each cell contains one or more alias (e.g. iron; FeII).
        These aliases must be separated by a semicolumn ";".

    """
    file_path = Path(constants.__file__).parent / 'default_features_alias.csv'
    df = pd.read_csv(file_path, encoding='utf-8', header=0) # SHOULD NOT BE LOCAL DRIVE !!!!!!!!!!!
    return df


# @Tin: adapt the following function so that the table gets installed with the package.
def entire_unit_alias_table():
    """Dataframe with units recognized by HGC and various columns with alias (synonyms) for these features.

    Return
    ------
    Dataframe :
        The dataframe has a "Unit" column. And various other columns with Alias.
        Each cell contains one or more alias (e.g. "mg-N/L"; "mgN/ L").
        These aliases must be separated by a semicolumn ";".

    """
    file_path = Path(__file__).cwd() / 'hgc/constants/default_units_alias.csv'
    df = pd.read_csv(file_path, encoding='utf-8', header=0) # SHOULD NOT BE LOCAL DRIVE !!!!!!!!!!!
    return df


entire_feature_alias_table = entire_feature_alias_table()
entire_unit_alias_table = entire_unit_alias_table()


def generate_entity_alias(df=None, entity_col='', alias_cols=''):
    """Melt a dataframe with multiple "Alias" columns to one "Features"/ "Units" column and one "Alias" column.

    This function can be used to generate a user defined lookup table for feature_alias or unit_alias

    Parameters
    ----------
    df : Dataframe
        Usually the "entire_feature_alias_table" or "entire_unit_alias_table"
    entity_col: string
        column containing the desired "Features" or "Units" (used by HGC)
    alias_cols: list
        list of columns containing synonyms (ALIAS) of the desired features or units
        Each cell contains one or more alias (e.g. iron; FeII).
        These aliases must be separated by a semicolumn ";".
        Repeat the <entity_col> here if you want to add the ntity to the list of
        alias.

    Return
    ------
    df : Dataframe
        column with same name as parameter <entity_col> ("Feature" or "Unit")
        coumn "Alias"

    Note
    ----
    The dataframe must NOT contain a column "entity_temp"

    """
    # @Tin, MartinK: following line is needed to prevent error with reloading? why? 
    # Somehow the df is changed when calling it again.
    df1 = copy.deepcopy(df)
    
    # rename entity column (because melt() gives error if "entity_col" overlaps with "alias_col")
    if entity_col in alias_cols:
        df1['Entity_temp'] = df1[entity_col]
    else:
        df1.rename({entity_col: 'Entity_temp'}, axis=1, inplace=True)

    # Melt multiple Alias columns to 1 column.
    df2 = pd.melt(df1, id_vars='Entity_temp', value_vars=alias_cols,
                  value_name='Alias')[['Entity_temp', 'Alias']].reset_index(drop=True)
    df2.rename({'Entity_temp': entity_col}, axis=1, inplace=True)

    # drop row where the Alias is missing
    df2 = df2[~df2['Alias'].isnull()]

    # Split rows with multiple Alias to multiple rows.
    df2['Alias'] = df2['Alias'].str.split(';')  # split cell to list
    df2 = df2.explode('Alias')
    df2['Alias'] = df2['Alias'].str.strip()
    df2.dropna(inplace=True)

    # drop duplicate Alias values
    df2 = df2.loc[~(df2['Alias'] == '')]

    # To do:
    # log non-unique "Alias" values if there are different corresponding Features/ Units.

    # if entity_col in alias_cols:
    #     df.drop('Entity_temp', axis=1, inplace=True)
    # else:
    #     df.rename({'Entity_temp': entity_col}, axis=1, inplace=True)

    return df2


def default_feature_alias_dutch_english():
    """Table with default HGC features and aliases."""
    df = generate_entity_alias(
            df=entire_feature_alias_table,
            entity_col='Feature',
            alias_cols=['Feature', 'IUPAC (Dutch)', 'IUPAC (English)',
                        'User defined (Dutch)', 'User defined (English)',
                        'SIKB_Code', 'SIKB_Omschrijving'])
    return df


def default_unit_alias():
    """Table with default HGC units and aliases."""
    df = generate_entity_alias(
            df=entire_unit_alias_table,
            entity_col='Unit',
            alias_cols=['Unit', 'Alias (Dutch)', 'Alias (English)'])
    return df


default_feature_alias_dutch_english = default_feature_alias_dutch_english()
default_unit_alias = default_unit_alias()


def default_feature_minscore():
    """Relation between word length (keys) and minimum score for named entity recognition of features (values)."""
    dct = {
        1: 100,
        3: 100,
        4: 90,
        5: 85,
        6: 80,
        8: 75
    }
    return dct


def default_unit_minscore():
    """Relation between word length (keys) and minimum score for named entity recognition of units (values)."""
    dct = {
        1: 100,
        5: 100,
        6: 90,
        7: 85,
        8: 80,
        10: 75
    }
    return dct


def strings2remove_from_features():
    """Generate a list of unwanted strings that are sometimes used with the features."""
    # in list order: first use longer string, then shorter version. 
    lst = [' icpms', ' icpaes', ' gf aas', ' icp', ' koude damp aas', ' koude damp',  # whitespace, string
           ' berekend', 'opdrachtgever', ' gehalte',
           ' tijdens meting',
           ' gefiltreerd', ' na filtratie', ' filtered', ' gef', ' filtratie',
           ' na destructie', 'destructie', ' na aanzuren', ' aanzuren',
           ' bij ',  # whitespace, string, whitespace
           ]
    return lst


# generate a list of default features (only ions, atoms and other)
mask = entire_feature_alias_table['Category'].isin(['atoms', 'ions', 'other'])
features2remove = list(set(list(entire_feature_alias_table['Feature'][mask])))


def strings2remove_from_units(features2remove=features2remove,
                              other_strings2remove=['eenh', 'nvt']):
    """Generate a list of unwantes strings that are sometimes combined with the units.

    The function generates a list of strings that needs to be removed from the original units
    before performing named entity recogntion. The list is based on the default_units and other strings

    Parameters
    ----------
    features2remove : dataframe
        contains at least the columns "Features" and "Category".
    other_strings2remove : list
        list with other strings that need to be removed from the list of units.

    Returns
    -------
    list of unwanted strings.

    """
    # retain N, P, S and Si (for mg-N/L, mg-P/L, etc.)
    lst = list(set(features2remove) - set(['N', 'P', 'S', 'Si']))

    # add a white space before feature and make lower case
    lst = [' ' + x.lower() for x in lst]

    lst = list(set(lst + other_strings2remove))

    # sort long to short string, to ensure that longest string is entirely removed
    lst.sort(key=len, reverse=True)

    return lst


def strings_filtered():
    """Generate a list of strings that can be used to recognize if a sample is filtered.

    Note: put whitespace before string, lowercase, only letters and symbols."""
    lst = [' gefiltreerd', ' na filtratie', ' filtered', ' filtration', ' gef', ' filtratie']
    return lst


# @ Tin/ MartinK:
# functions are not directly callable in functions.
# Why is it necessary to first generate a variable ??

default_feature_minscore = default_feature_minscore()
default_unit_minscore = default_unit_minscore()
strings2remove_from_features = strings2remove_from_features()
strings2remove_from_units = strings2remove_from_units()
strings_filtered = strings_filtered()


# %% main function


def _interp1d_fill_value(x=[], y=[]):
    """
    Generate a linear interpolatation function with fixed fill value outside x-range.

    Use the y(xmin) to extrapolate for x < xmin.
    y(xmax) to extrapolate for x > xmax.
    """
    # generate dataframe
    df = pd.DataFrame(zip(x, y), columns=['X', 'Y'])
    df.sort_values(by='X', inplace=True)
    df.reset_index(drop=True, inplace=True)

    y_below = df['Y'][0]  # fill value below xmin
    y_above = df.iloc[-1, :]['Y']  # fill value below xmin

    f = scipy.interpolate.interp1d(df['X'], df['Y'], bounds_error=False, fill_value=(y_below, y_above))

    return f


def _cleanup_alias(df=None, col='', col2='', string2whitespace=[], string2replace={}, string2remove=[], strings_filtered=[]):
    """
    Process columns to ascii.

    Replace selected symbols by a whitespace
    Replace selected symbols/ strings by other symbols
    Force to lower case
    Remove duplicates
    Remove all but letters and numbers
    Remove unwanted strings (e.g. icpms)
    Trim whitespace

    Parameters
    ----------
    df : dataframe
    col : string
        name of column containing the alias of entities
    col2 : string
        name of new column to generate containing the alais after cleanup.
    string2whitespace : list
        symbols that should be replaced by a whitespace
    string2replace : dictionary
        symbols/ strings that should be replaced by other symbols
    string2remove : list
        symbols/ strings to remove

    """
    df.drop_duplicates(subset=[col], inplace=True)
    df.reset_index(inplace=True, drop=True)

    # replace strings/ symbol by whitespace
    df[col2] = df[col]
    if isinstance(string2whitespace, list):
        for string in string2whitespace:
            df[col2] = df[col2].str.replace(string, ' ')

    # replace strings/ symbols by other symbol
    if isinstance(string2replace, dict):
        for key, value in string2replace.items():
            df[col2] = df[col2].str.replace(key, value)

    # fuzzywuzzy uses only numbers and ascii letters (a-z; A-Z) and replaces all other symbols by whitespace
    # this may lead to a large number of tokens (words) that are easy to match
    # therefore, the script removes these other symbols to prevent an excess amount of whitespaces

    df[col2] = df[col2].str.lower()
    df[col2] = df[col2].str.encode('ascii', 'ignore').str.decode('ascii')  # remove non-ascii
    df[col2] = df[col2].str.replace('[^0-9a-zA-Z\s]', '')
    df[col2] = df[col2].astype(str)

    # Check if sample was filtered (do this step before removing strings)
    if len(strings_filtered) > 0:
        df['Filtered'] = np.where(df[col2].str.contains('|'.join(strings_filtered)), True, False)
        
    # remove strings
    if isinstance(string2remove, list):
        for string in string2remove:
            df[col2] = df[col2].str.replace(string, '')

    # trime whitespace and remove double whitespace
    df[col2] = df[col2].str.lstrip(' ').str.rstrip(' ').str.replace('\s+', ' ', regex=True)

    return df


def generate_entity_map(entity_orig=[],
                        df_entity_alias=None,
                        entity_col='',
                        string2whitespace=[],
                        string2replace={},
                        string2remove=[],
                        strings_filtered=[],
                        entity_minscore={},
                        match_method='levenshtein'):
    """
    Generate a map to convert a list of original entities (features/ units) to HGC compatible features.

    The funtion uses Named Entity Recognition (NER) techniques to match original entities to the entities used by HGC.
    It is based on the fuzzywuzzy module. And uses Levenshtein Distance to calculate the differences between
    original entities and HGC-compatible entities. Original entities are matched to the HGC-entity to which they
    have the least distance. A match is only succesful if the score based on the Levenshtein Distance remains above
    a certain threshold.

    The user can use default HGC-compatible entities or specify own entities.

    WARNING: it is recommended to always perform a visual check whether the mapping is correct,
    Especially for features/ units that perform close to the mimimum entity score.

    Parameters
    ----------
    entity_orig: list
        List with original names of features or units (FROM).
    df_entity_alias : dataframe
        Dataframe with a column containing the new features or units (TO) and one or more columns with
        synonyms (ALIAS) that will be matched to the list of original names.
    entity_col : string
        Name of entity ("Feature" or "Unit")
    string2whitespace: list
        List of strings/ symbols to replace by whitespace before performing named entity recognition (NER).
        WATCH OUT: Case sensitive and also recognizes non ascii symbols
    string2replace: dictionary
        Dictionary with symbols/ strings to replace by another symbol before performing named entity recognition (NER).
        WATCH OUT: Case sensitive and also recognizes non ascii symbols
    string2remove: list
        List of strings/ symbols to remove before performing named entity recognition (NER).
        WATCH OUT: use only white space, numbers (0-9) and lowercase ascii letters (a-z).
        For example: "icpms" instead of "ICP-MS".
    strings_filtered: list
        List of strings that are used to recognize is a sample is filtered.
        The check is done after adjusting entity names to removing all but unwanted letters and symbols.
    
    feature_minscore: dictionary
        Dictionary that controls the minimum score of NER required for feature recognition.
        This minimum score is a function of the feature's length.
        The minimum score is generally higher for shorter features.
        keys = length of feature or unit (number of symbols; integer)
        values = minimum score required for a positive recognition (0-100 scale; integer or float)
    match_method: string {'exact', 'ascii', 'levenshtein'}
        'exact' : match original entity and Alias only when the strings are exactly the same.
        This is the recommended method for matching CAS number.
        'ascii' : match after removing non ascii symbols from original entities and aliases.
        'levenshtein' : match using the least Levenshtein Distance (fuzzywuzzy algorithm).
        Default = 'levenshtein'

    Returns
    -------
    entity_map : dictionary
        mapping of original features/ units to features/ units used by HGC.
    entity_unmapped : list
        list of original features/ units that were not succesfully matched to new features/ units.
    df_entity_map : dataframe
        dataframe with entire mapping and scores.

    """
    # generate the dataframe with the desired features/ units
    df_entity_alias = _cleanup_alias(df=df_entity_alias,
                                     col='Alias',
                                     col2='Alias2',
                                     string2replace=string2replace,
                                     string2whitespace=string2whitespace,
                                     string2remove=string2remove,
                                     strings_filtered=[])
    df_entity_alias['Index_orig'] = df_entity_alias.index

    # generate a dataframe with the original features/ units
    df_entity_orig = pd.DataFrame(set(entity_orig), columns=[entity_col + '_orig'])
    df_entity_orig = _cleanup_alias(df=df_entity_orig,
                                    col=entity_col + '_orig',
                                    col2=entity_col + '_orig2',
                                    string2replace=string2replace,
                                    string2whitespace=string2whitespace,
                                    string2remove=string2remove,
                                    strings_filtered=strings_filtered)
    if 'Filtered' not in df_entity_orig.columns:
        df_entity_orig['Filtered']=np.nan

    # Find to which new features/ units each old feature/ unit best corresponds
    n = len(df_entity_orig)
    
    # Step 1: Exact match entities 
    df1 = df_entity_orig.merge(df_entity_alias, how='left',
                               left_on=entity_col + '_orig', right_on='Alias')
    df1["Score"] = 102
    
    df_entity_orig1 = df1.loc[df1['Alias'].isnull()][[entity_col + '_orig', entity_col + '_orig2', 'Filtered']].reset_index(drop=True)
    df1 = df1.loc[~df1['Alias'].isnull()].reset_index(drop=True).drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)   
    print('number of entities matched exactly: ', len(df1), ' of ', n)

    # Step 2: match after ascii cleanup of entities
    if match_method in ['levenshtein', 'ascii']:
        df2 = df_entity_orig1.merge(df_entity_alias, how='left',
                                   left_on=entity_col + '_orig2', right_on='Alias2')
        df2["Score"] = 101
        df_entity_orig2 = df2.loc[df2['Alias'].isnull()][[entity_col + '_orig', entity_col + '_orig2', 'Filtered']].reset_index(drop=True)
        df2 = df2.loc[~df2['Alias'].isnull()].reset_index(drop=True).drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)   
        print('number of entities matched exactly after ascii cleanup: ', len(df2), ' of ', n)
    else:
        df2 = df_entity_orig1

    # Step 3: match entities using least Levenshtein distance
    if match_method in ['levenshtein']:
        choices = df_entity_alias['Alias2']
        feature_orig2alias = []
        i = len(df1) + len(df2)
        for query in df_entity_orig2[entity_col + '_orig2']:
            feature_orig2alias.append(process.extractOne(query, choices, scorer=fuzz.token_sort_ratio))
            i += 1
            print('mapping entity', i, 'of', n)
        df3 = pd.concat(
            [df_entity_orig2, pd.DataFrame(feature_orig2alias, columns=['Alias2', 'Score', 'Index_orig'])],
            axis=1).drop('Index_orig', axis=1)
        df3 = df3.merge(df_entity_alias, on='Alias2').drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)
    else:
        try:
            df_entity_orig2
        except:
            df3 = pd.DataFrame([])

    df_entity_map = pd.concat([df1, df2, df3], axis=0, ignore_index=True)

    # determine which features have been succesfully matched by comparing score with
    # minimum required score based on word length.
    f_minscore = _interp1d_fill_value(x=entity_minscore.keys(), y=entity_minscore.values())

    df_entity_map['Alias2_length'] = df_entity_map['Alias2'].astype(str).map(len)
    df_entity_map['MinScore'] = f_minscore(df_entity_map['Alias2_length'])

    df_entity_map['Succes'] = np.where(df_entity_map['Score'] >= df_entity_map['MinScore'], True, False)

    # sometimes, an Alias2 can be matched to multiple Alias --> show only first option
    df_entity_map.drop_duplicates(subset=[entity_col + '_orig'], inplace=True)
    df_entity_map.reset_index(inplace=True, drop=True)

    # generate a dictionary/ list with the succesfull and unsuccesfull matched entities
    mask = df_entity_map['Succes'] == True
    entity_map = dict(zip(df_entity_map[entity_col + '_orig'][mask], df_entity_map[entity_col][mask]))
    entity_unmapped = list(df_entity_map[entity_col + '_orig'][~mask])

    return entity_map, entity_unmapped, df_entity_map
    
    
def generate_feature_map(entity_orig=[],
                         df_entity_alias=default_feature_alias_dutch_english,
                         entity_col='Feature',
                         string2whitespace=[],
                         string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                                         'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                                         'μ': 'u', 'µ': 'u', '%': 'percentage'},
                         string2remove=strings2remove_from_features,
                         strings_filtered=strings_filtered,
                         entity_minscore=default_feature_minscore,
                         match_method='levenshtein'):
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping features."""
    feature_map, feature_unmapped, df_feature_map =\
        generate_entity_map(entity_orig=entity_orig,
                            df_entity_alias=df_entity_alias,
                            entity_col=entity_col,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            strings_filtered=strings_filtered,
                            entity_minscore=default_feature_minscore,
                            match_method=match_method)

    return feature_map, feature_unmapped, df_feature_map


def generate_unit_map(entity_orig=[],
                      df_entity_alias=default_unit_alias,
                      entity_col='Unit',
                      string2whitespace=['/', '-'],
                      string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                                      'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                                      'μ': 'u', 'µ': 'u', '%': 'percentage'},
                      string2remove=strings2remove_from_units,
                      strings_filtered=[],
                      entity_minscore=default_unit_minscore,
                      match_method='levenshtein'):
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping units."""
    unit_map, unit_unmapped, df_unit_map =\
        generate_entity_map(entity_orig=entity_orig,
                            df_entity_alias=df_entity_alias,
                            entity_col=entity_col,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            strings_filtered=strings_filtered,
                            entity_minscore=entity_minscore,
                            match_method=match_method)

    return unit_map, unit_unmapped, df_unit_map
