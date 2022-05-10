""" load dataframes and dictionaries that contain information on the relation between
Features, Units, Categories, Alias (synonyms), CAS, PubChemCID.
"""
import hgc.named_entity_recognition.utils as ner
import numpy as np
import pandas as pd
import pickle

from hgc.named_entity_recognition.utils import _check_cols_in_df
from pathlib import Path


PATH = Path(__file__).parent
FILE_PATH_FEATURE = PATH / 'feature_map.pkl'
FILE_PATH_UNIT = PATH / 'unit_map.pkl'

COLS_FEATURE_ALIAS_EN = ['AliasEnglish', 'HGC', 'MicrobialParameters', 'OtherEnglishAlias']
COLS_FEATURE_ALIAS_NL = ['AliasDutch', 'OtherDutchAlias', 'SIKB', 'NVWA', 'REWAB']
COLS_CAS = ['ValidCas']
COLS_DBASE = ['SIKBcode', 'KIWAnumber']

COLS_UNIT_ALIAS = ['AliasEnglish', 'AliasDutch']


def load_feature_map(pickle_file_path=FILE_PATH_FEATURE):
    """ Read dataframe (pickle-file) with information on mapping of features.
        The structure of the table is described under the parameters of the
        function load_feature_dicts()."""
    try:
        df = pickle.load(open(pickle_file_path, "rb"))
    except FileNotFoundError:
        raise FileNotFoundError('File with feature_map not found: {}'.format(FILE_PATH_FEATURE))
    return df


def load_unit_map(pickle_file_path=FILE_PATH_UNIT):
    """ Read dataframe (pickle-file) with information on mapping of units.
        All columns exept "Unit" are converted to list using "|" as separator.
        Example: e.g.: mg/L| miligram/liter -> ['mg/L', 'miligram/liter']."""
    try:
        df = pickle.load(open(pickle_file_path, "rb"))
    except FileNotFoundError:
        raise FileNotFoundError('File with unit_map not found: {}'.format(FILE_PATH_UNIT))
    return df


def load_feature_dicts(df_feature_map=load_feature_map(),
                       cols_alias=['Feature'] + COLS_FEATURE_ALIAS_EN + COLS_FEATURE_ALIAS_NL + COLS_CAS):
    """
    Convert dataframe to dictionaries with mapping of Features to Units, Alias (synonyms) and Categories.

    Parameters
    ----------
    df_feature_map: pandas.DataFrame
        Columns:
            Name: Feature, dtype: str -> the features to be identified
            Name: DefaultUnit, dtype: str
            Name: Catagory, dtype: str
            Name: ValidCid, dtype: list of str (optional) -> valid CID's from PubChem database
            Name: BestCid, dtype: list of str (optional)
            Name: ValidCas, dtype: list of str (optional)) -> valid CAS numbers
            Name: BestCas, dtype: list of str (optional)
            Name: <<Alias>>, dtype: list of str (optional)
                <<Alias>> = various columns with Alias (synonyms) of "Feature".
                See parameter "cols_alias"
    cols_alias: list of strings
        list with column names containing <<Alias>>
        Note: include 'Feature' in list if you want to use them as alias

    Return
    ------
    dict_features_units: dictionary
        keys: Features
        values: Default Units
    dict_features_category: dictionary
        keys: Features
        values: Category
            All features that are supported by HGC are classified as 'ions', 'atoms', 'other'.
            For use in identification of units: check hgc.ner
            Features not supported by HGC are classified as an empty string ''.
    dict_alias_features: nested dictionary
        level0 keys:
            the following type of Alias (synonyms) are supported in the default CSV:
             'CAS', "HGC", 'MicrobialParameters', 'IUPAC', 'Alias_English',
            'Alias_Dutch', 'SIKBcode', 'SIKBomschrijving'
        Level1 keys: Alias
        Level1 values: Features

    Note: The dictionaries may include Features not supported by HGC, but that are used for Named Entity Recognition.

    """
    # check columns in df
    _check_cols_in_df(cols_alias + ['Feature', 'DefaultUnits', 'Category'], df_feature_map)

    # generate dictionaries
    dict_features_units = dict(zip(df_feature_map['Feature'], df_feature_map['DefaultUnits']))
    dict_features_category = dict(zip(df_feature_map['Feature'], df_feature_map['Category']))

    dict_alias_features = {}
    for col in cols_alias:
        if col == 'Feature':
            df = df_feature_map[['Feature']].dropna()
            dict_alias_features[col] = dict(zip(df['Feature'], df['Feature']))
        else:
            df = df_feature_map[['Feature', col]].explode(col)
            df[col] = df[col].replace('', np.nan)  # remove empty rows
            df.dropna(inplace=True)
            dict_alias_features[col] = dict(zip(df[col], df['Feature']))

    return dict_features_units, dict_features_category, dict_alias_features


def load_unit_dicts(df_unit_map=load_unit_map(),
                     cols_alias=['Unit'] + COLS_UNIT_ALIAS):
    """
    Convert dataframe to dictionaries that map Units to alias (synonyms).

    Parameters
    ----------
    df2: pandas.DataFrame
        Columns:
            Name: Unit, dtype: str -> These are the Units to be identified
            Name: <<Alias>>, dtype: list of str (optional)
                <<Alias>> = various columns with Alias (synonyms) of "Units".

    Return
    ------
    dict_alias_units: nested dictionary
        level0 keys:
            the following type of Alias (synonyms) are supported:
            'Other_English', 'Other_Dutch'
        Level1 keys: Alias
        Level1 values: Units

    Note: The dictionaries include Units not supported by HGC, but that are used for Named Entity Recognition.
    """
    # check columns in df
    _check_cols_in_df(cols_alias + ['Unit'], df_unit_map)

    # generate dictionaries
    dict_alias_units = {}
    for col in cols_alias:
        if col == 'Unit':
            df = df_unit_map[['Unit']].dropna()
            dict_alias_units[col] = dict(zip(df['Unit'], df['Unit']))
        else:
            df = df_unit_map[['Unit', col]].explode(col)
            df[col] = df[col].replace('', np.nan)  # remove empty rows
            df.dropna(inplace=True)
            dict_alias_units[col] = dict(zip(df[col], df['Unit']))

    return dict_alias_units


def dict_features_units():
    """Convenience function to partially run the function generate_default_dictionaries()."""
    return generate_feature_mapping_dictionaries()[0]



