# -*- coding: utf-8 -*-
"""
Routine for recognizing features and units using NER.
Martin van der Schans, Xin Tian
KWR, April-July 2020
"""
import pandas as pd
import scipy.interpolate
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from hgc.import_default import default_features, default_feature_minscore, default_units
from hgc.import_default import default_feature_minscore, strings2remove_from_units, default_unit_minscore

# %% load defaults from hgc
default_features = default_features()
default_units = default_units()
default_feature_minscore = default_feature_minscore()
default_unit_minscore = default_unit_minscore()
strings2remove_from_units = strings2remove_from_units()

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

def _melt_table(df=None, id_vars='', value_vars=[]):
    """Melt a table with multiple columns to 2 columns, use identifier column also as value column.

    Parameters
    ----------
    df : dataframe
    id_var : string
        column to use as both identifier and value for pd.melt
    value_var : lst
        columns to use as value for pd.melt

    """
    df[id_vars + '2'] = df[id_vars]
    df2 = pd.melt(df, id_vars=id_vars, value_vars=value_vars + [id_vars + '2'],
                  value_name='Alias')[[id_vars, 'Alias']].reset_index(drop=True)
    return df2

def _expand_dataframe(df=None):
    """Split rows with multiple Alias to multiple rows."""
    # drop row where the Alias is missing
    df = df[~df['Alias'].isnull()]
    # Split the Alias string to a list when separated by ";"
    df['Alias'] = df['Alias'].str.split(';')
    # expand the DataFrame so that rows with list of values are split over multiple rows
    df = df.explode('Alias')
    return df

def _cleanup_alias(df=None, col='', col2='', string2whitespace=[], string2replace={}, string2remove=[]):
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
    # remove strings
    if isinstance(string2remove, list):
        for string in string2remove:
            df[col2] = df[col2].str.replace(string, '')
    # trime whitespace and remove double whitespace
    df[col2] = df[col2].str.lstrip(' ').str.rstrip(' ').str.replace('\s+', ' ', regex=True)
    return df

def generate_entity_map(entity_orig=None,
                        df_entity_to=default_features,
                        entity_col='',
                        alias_cols=[],
                        string2whitespace=[],
                        string2replace={},
                        string2remove=[],
                        entity_minscore={}):
    """
    Generate a map to convert a list of original entities (features/ units) to HGC compatible features.

    The funtion uses Named Entity Recognition (NER) techniques to match original entities to the entities used by HGC.
    It is based on the fuzzywuzzy module. And uses Levenshtein Distance to calculate the differences between
    original entities and HGC-compatible entities. Original entities are matched to the HGC-entity to which they
    have the least distance. A match is only succesful if the score based on the Levenstein Distance remains above
    a certain threshold.

    The user can use default HGC-compatible entities or specify onw entities.

    WARNING: it is recommended to always perform a visual check whether the mapping is correct,
    Especially for features/ units that perform close to the mimimum entity score.

    Parameters
    ----------
    entity_orig: list
        list with original names of features or units (FROM).
    df_entity_alias : dataframe
        dataframe with a column containing the new features or units (TO) and one or more columns with
        synonyms (ALIAS) that will be matched to the list of original names.
    entity_col: string
        column containing the new features or units (TO)
    alias_cols: list
        columns containing synonyms (ALIAS) of the new features or units
        Each cell containts one or more synonyms. Synonyms are separated by a semicolumn (";")
    string2whitespace: list
        list of strings/ symbols to replace by whitespace before performing named entity recognition (NER).
        WATCH OUT: Case sensitive and also recognizes non ascii symbols
    string2replace: dictionary
        dictionary with symbols/ strings to replace by another symbol before performing named entity recognition (NER).
        WATCH OUT: Case sensitive and also recognizes non ascii symbols
    string2remove: list
        list of strings/ symbols to remove before performing named entity recognition (NER).
        WATCH OUT: use only white space, numbers (0-9) and lowercase ascii letters (a-z).
        For example: "icpms" instead of "ICP-MS".
    feature_minscore: dictionary
        dictionary that controls the minimum score of NER required for feature recognition.
        This minimum score is a function of the feature's length.
        The minimum score is generally higher for shorter features.
        keys = length of feature or unit (number of symbols; integer)
        values = minimum score required for a positive recognition (0-100 scale; integer or float)

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
    df_entity_to = _melt_table(df=df_entity_to,
                               id_vars=entity_col,
                               value_vars=alias_cols)
    df_entity_to = _expand_dataframe(df=df_entity_to)
    df_entity_to = _cleanup_alias(df=df_entity_to,
                                  col='Alias',
                                  col2='Alias2',
                                  string2replace=string2replace,
                                  string2whitespace=string2whitespace,
                                  string2remove=string2remove)
    # generate a dataframe with the original features/ units
    df_entity_orig = pd.DataFrame(set(entity_orig), columns=[entity_col + '_orig'])
    df_entity_orig = _cleanup_alias(df=df_entity_orig,
                                    col=entity_col + '_orig',
                                    col2=entity_col + '_orig2',
                                    string2replace=string2replace,
                                    string2whitespace=string2whitespace,
                                    string2remove=string2remove)
    # find to which new features/ units each old feature/ unit best corresponds
    choices = df_entity_to['Alias2']
    feature_orig2alias = []
    n = len(df_entity_orig[entity_col + '_orig2'])
    i = 0
    for query in df_entity_orig[entity_col + '_orig2']:
        feature_orig2alias.append(process.extractOne(query, choices, scorer=fuzz.token_sort_ratio))
        i += 1
        print('mapping entity', i, 'of', n)

    df_entity_map = pd.concat(
        [df_entity_orig, pd.DataFrame(feature_orig2alias, columns=['Alias2', 'Score', 'Index_orig'])],
        axis=1)
    # determine which features have been succesfully matched by comparing score with
    # minimum required score based on word length.
    f_minscore = _interp1d_fill_value(x=entity_minscore.keys(), y=entity_minscore.values())

    df_entity_map = df_entity_map.merge(df_entity_to, on='Alias2')
    df_entity_map['Alias2_length'] = df_entity_map['Alias2'].astype(str).map(len)
    df_entity_map['MinScore'] = f_minscore(df_entity_map['Alias2_length'])

    df_entity_map['Succes'] = False
    df_entity_map.loc[df_entity_map['Score'] >= df_entity_map['MinScore'], 'Succes'] = True

    # sometimes, an Alias2 can be matched to multiple Alias --> show only first option
    df_entity_map.drop_duplicates(subset=[entity_col + '_orig'], inplace=True)
    df_entity_map.reset_index(inplace=True, drop=True)

    # generate a dictionary/ list with the succesfull and unsuccesfull matched entities
    mask = df_entity_map['Succes'] == True
    entity_map = dict(zip(df_entity_map[entity_col + '_orig'][mask], df_entity_map[entity_col][mask]))
    entity_unmapped = list(df_entity_map[entity_col + '_orig'][~mask])

    return entity_map, entity_unmapped, df_entity_map

def generate_feature_map(entity_orig=None,
                         df_entity_to=default_features,
                         entity_col='Feature',
                         alias_cols=['IUPAC (Dutch)', 'Alias (Dutch)', 'IUPAC (English)', 'Alias (English)'],
                         string2whitespace=[],
                         string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e', 'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i', 'μ': 'u', 'µ': 'u', '%': 'percentage'},
                         string2remove=[' icpms', ' berekend', ' icp', 'gefiltreerd', 'na filtratie', 'koude damp'],
                         entity_minscore=default_feature_minscore):
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping features."""
    feature_map, feature_unmapped, df_feature_map =\
        generate_entity_map(entity_orig=entity_orig,
                            df_entity_to=df_entity_to,
                            entity_col=entity_col,
                            alias_cols=alias_cols,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            entity_minscore=entity_minscore)
    return feature_map, feature_unmapped, df_feature_map

def generate_unit_map(entity_orig=None,
                      df_entity_to=default_units,
                      entity_col='Unit',
                      alias_cols=['Alias (Dutch)'],
                      string2whitespace=['/', '-'],
                      string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e', 'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i', 'μ': 'u', 'µ': 'u', '%': 'percentage'},
                      string2remove=strings2remove_from_units,
                      entity_minscore=default_unit_minscore):
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping units."""
    unitfeature_map, unit_unmapped, df_unit_map =\
        generate_entity_map(entity_orig=entity_orig,
                            df_entity_to=df_entity_to,
                            entity_col=entity_col,
                            alias_cols=alias_cols,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            entity_minscore=entity_minscore)

    return unitfeature_map, unit_unmapped, df_unit_map