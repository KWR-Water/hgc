# -*- coding: utf-8 -*-
"""
Routine to import default 
Xin Tian, Martin van der Schans
KWR, April-July 2020
"""
import pandas as pd
import scipy.interpolate
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def default_features():
    """Generate a default dataframe with features and alias (synonyms)."""
    return pd.read_csv(r'.\hgc\constants\default_features_alias.csv', encoding='ISO-8859-1', header=0)

def default_units():
    """Generate a default dataframe with units and alias (synonyms)."""
    return pd.read_excel(r'.\hgc\constants\default_units_alias.xlsx', header=0)

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
    
def strings2remove_from_units(features2remove=default_features, other_strings2remove=['eenh', 'nvt']):
    """Generate a list of unwantes strings that are somtimes combined with the units.
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
    # generate a list of default features (only ions, atoms and other)
    try:
        mask = default_features['Category'].isin(['atoms', 'ions', 'other'])
    except:
        mask = default_features()['Category'].isin(['atoms', 'ions', 'other'])
    try: 
        lst = list(set(list(default_features['Feature'][mask])))
    except:
        lst = list(set(list(default_features()['Feature'][mask])))
    # retain N, P and S (for mg-N/L, mg-P/L, etc.)
    lst = list(set(lst) - set(['N', 'P', 'S']))
    # add a white space before feature and make lower case
    lst = [' ' + x.lower() for x in lst]
    lst = list(set(lst + other_strings2remove))
    # sort long to short string, to ensure that longest string is entirely removed
    lst.sort(key=len, reverse=True)
    return lst