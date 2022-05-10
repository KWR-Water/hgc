"""
Functions used to cleanup features and units
"""

import itertools
import numpy as np
import pandas as pd


def _split_string_in_dfcol_to_list(df=None, cols=[], separator='|'):
    """ Convert all items in selected columns of dataframe to list. Assumes vertical bar "|" as splitter."""
    for col in cols:
        items = []
        for item in df[col]:
            if len(item) > 0:
                item = [x.strip() for x in item.split(separator)]
            else:
                item = []
            items.append(item)
        df[col] = items


def _list_in_df_to_lists(df):
    """ Convert columns of dataframe to a single list. All columns must contain lists."""
    nestlst = [list(df.explode(col)[col]) for col in df.columns]  # 1 list per columns]
    lst = list(itertools.chain.from_iterable(nestlst))
    return lst


def _check_cols_in_df(lst_cols, df):
    """ Check if list of column names are present in dataframe. """        
    cols_missing = list(set(lst_cols) - set(df.columns))
    if len(cols_missing) > 0:
        raise KeyError('columns missing in dataframe: {}'.format(cols_missing))


def strings2remove_from_features():
    """Generate a list of unwanted strings that are sometimes used with the features."""
    # in list order: first use longer string, then shorter version.
    lst = [' icpms', ' icpaes', ' gf aas', ' icp', ' koude damp aas', ' koude damp',  # whitespace, string
           ' berekend', 'opdrachtgever', ' gehalte', ' kretl',
           ' tijdens meting',
           ' gefiltreerd', ' na filtratie', ' filtered', ' gef', ' filtratie',
           ' na destructie', 'destructie', ' na aanzuren', ' aanzuren',
           ' bij ',  # whitespace, string, whitespace
           ]
    return lst


def strings2remove_from_units(features2remove=[],
                              features2retain=['N', 'P', 'S', 'Si'],
                              other_strings2remove=['eenh', 'nvt'],
                              **kwargs):
    """Generate a list of strings that interfere with text recognition of Units.

    For the algorithm, it is easier to recognice Units after removing the Feature.
    for example: "mg-As/L" is easier to recognize as "mg/L" after removing "As"
    However, certain Features must be retained if they are expressed as atom.
    for example: "mg-N/L NO3" has a different meaning than "mg/L NO3"

    This list is specifically made after examining a couple of files from Dutch water companies.
    It may need to be adjusted for other datasets.

    Parameters
    ----------
    features2remove: list
        default: Features used by HGC ('atoms', 'ions', 'other')
    features2retain: list
        default: ['N', 'P', 'S', 'Si']
    other_strings2remove : list
        list with other strings that need to be removed from the list of units.

    Returns
    -------
    list of unwanted strings.

    """
    lst = list(set(features2remove) - set(features2retain)) + other_strings2remove

    # remove leading space if there is any and then add a white space before feature and make lower case
    lst = [string.lstrip() for string in lst]
    lst = [' ' + x.lower() for x in lst]

    # sort long to short string, to ensure that longest string is entirely removed
    lst.sort(key=len, reverse=True)

    return lst


def strings2replace():
    """Dictionary with symbols that need to be replaced before text recognition."""
    dct = {'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
           'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
           'μ': 'u', 'µ': 'u', '%': 'percentage'}
    return dct


def strings_filtered():
    """Generate a list of strings that can be used to recognize if a sample is filtered."""
    # Note: put whitespace before string, lowercase, only letters and symbols.
    lst = [' gefiltreerd', ' na filtratie', ' filtered', ' filtration', ' gef', ' filtratie']
    return lst


def _cleanup_alias(df=None, col='', col2='', string2whitespace=[],
                   string2replace={}, string2remove=[], strings_filtered=[], **kwargs):
    """
    Process features/ units to ascii symbols.

    Replace selected symbols by a whitespace
    Replace selected symbols/ strings by other symbols
    Force to lower case
    Remove duplicates
    Remove all rather than ascii letters and numbers
    Remove unwanted strings (e.g. icpms)
    Trim whitespace and remove double whitespace

    Parameters
    ----------
    df : dataframe
    col : string
        name of column containing the alias of entities
    col2 : string
        name of new column to generate containing the alias after cleanup.
    string2whitespace : list
        symbols that should be replaced by a whitespace
    string2replace : dictionary
        symbols/ strings that should be replaced by other symbols
    string2remove : list
        symbols/ strings to remove

    """
    # replace strings/ symbol by whitespace
    df[col2] = df[col]
    if isinstance(string2whitespace, list):
        for string in string2whitespace:
            df[col2] = df[col2].str.replace(string, ' ')

    # replace strings/ symbols by other symbol
    if isinstance(string2replace, dict):
        for key, value in string2replace.items():
            df[col2] = df[col2].str.replace(key, value)

    # remove non-ascii
    # Note: fuzzywuzzy only uses numbers and ascii letters (a-z; A-Z) and replaces all other symbols
    # by whitespace. this may lead to a large number of tokens (words) that are easy to match.
    # Therefore, the script removes these other symbols to prevent an excess amount of whitespaces.
    df[col2] = df[col2].str.lower()
    df[col2] = df[col2].str.encode('ascii', 'ignore').str.decode('ascii')  # remove non-ascii
    df[col2] = df[col2].str.replace('[^0-9a-zA-Z\s]', '')
    df[col2] = df[col2].astype(str)

    # Check if sample was filtered (do this step before removing strings)
    if len(strings_filtered) > 0:
        df.loc[:, 'Filtered'] = np.where(df[col2].str.contains('|'.join(strings_filtered)), True, False)

    # remove strings
    if isinstance(string2remove, list):
        for string in string2remove:
            df[col2] = df[col2].str.replace(string, '')

    # trime whitespace and remove double whitespace
    df[col2] = df[col2].str.lstrip(' ').str.rstrip(' ').str.replace('\s+', ' ', regex=True)

    return df




