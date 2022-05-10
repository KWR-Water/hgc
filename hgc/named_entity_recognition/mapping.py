# -*- coding: utf-8 -*-
"""
Routine for recognizing hydrochemical features and units using NER.
Xin Tian, Martin van der Schans, Martin Korevaar
KWR,
Last edit: Nov 11, 2020
"""
import copy
import numpy as np
import pandas as pd
import pubchempy as pcp
import re
import scipy.interpolate

from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from googletrans import Translator

from hgc.constants.iodefaults import load_feature_dicts, load_unit_dicts


# # maintenance_flag = 'n'
# # %% Defaults

dict_features_units, dict_features_category, dict_alias_features = load_feature_dicts()
dict_alias_units = load_unit_dicts()




# %% support functions



def _get_cas_from_compound(Compound):
    """get list of CAS nrs that match PubChemPy Object"""
    cas = []
    for syn in compound.synonyms + ['14797-55-9']:
        match = re.match('(\d{2,7}-\d\d-\d)', syn)
        if match:
            cas.append(match.group(1))

    return cas

# %% NER methods


def _exact_match(df_orig, df_entity, entity_col, **kwargs):
    """Check whether a feature/unit name exactly matches the alias (synonym) of desired features/ units."""
    # select features that are not yet matched
    mask = (df_orig['Success'] == False)
    df1 = df_orig[mask].reset_index(drop=True)
    df1 = df1[set(df1.columns) - set(df_entity.columns)]  # drop overlapping columns to prevent error with merge in next step

    # merge orginal feature/unit and alias of desired feature/unit
    if len(df1) > 0:
        df2 = df1.merge(df_entity, how='left', left_on=entity_col + '_orig', right_on='Alias')
        df2.loc[~df2['Alias'].isnull(), 'Success'] = True
        df2.loc[~df2['Alias'].isnull(), 'Method'] = 'exact'
        df3 = pd.concat([df_orig[~mask], df2])
    else:
        df3 = df_orig

    print('exact match completed:', df3['Success'].sum(), 'of', len(df3), ' ', entity_col, 'successfully matched')

    return df3


def _ascii_match(df_orig, df_entity, entity_col, **kwargs):
    """Same as "_exact_match(), but after removing non ascii symbols from both original features/units and alias of desired features/ units."""
    # select features that are not yet matched
    mask = (df_orig['Success'] == False)
    df1 = df_orig[mask].reset_index(drop=True)
    df1 = df1[set(df1.columns) - set(df_entity.columns)] # drop overlapping columns to prevent error with merge in next step

    # merge orginal feature/unit and alias of desired feature/unit
    if len(df1) > 0:
        df2 = df1.merge(df_entity, how='left', left_on=entity_col + '_orig2', right_on='Alias2')
        df2.loc[~df2['Alias'].isnull(), 'Success'] = True
        df2.loc[~df2['Alias'].isnull(), 'Method'] = 'ascii'
        df3 = pd.concat([df_orig[~mask], df2])
    else:
        df3 = df_orig

    print('ascii match completed:', df3['Success'].sum(), 'of', len(df3), ' ', entity_col, 'successfully matched')

    return df3


def _levenshtein_match(df_orig, df_entity, entity_col, **kwargs):
    """Match using the least Levenshtein Distance (fuzzywuzzy algorithm)."""
    # select features that are not yet matched
    mask = (df_orig['Success'] == False)
    df1 = df_orig[mask].reset_index(drop=True)
    df1 = df1[set(df1.columns) - set(df_entity.columns)] # drop overlapping columns to prevent error with merge in next step

    if len(df1) > 0:
        # determine which Alias2 of the desired feature/unit best matches the original feature/ unit
        choices = df_entity['Alias2']
        entity_orig2alias = []
        n = len(df_orig)
        i = len(df_orig) - len(df1) + 1  # number of features/ units already matched
        for query in df1[entity_col + '_orig2']:
            entity_orig2alias.append(process.extractOne(query, choices, scorer=fuzz.token_sort_ratio))
            if i % 20 == 0:
                print('levenshtein try match ', i, 'of', n, ' ', entity_col)
            i += 1

        # check if feature/ unit was successfully matched
        df2 = pd.concat([df1, pd.DataFrame(entity_orig2alias, columns=['Alias2', 'Score', 'Index_orig'])],
                        axis=1).drop('Index_orig', axis=1)
        df3 = df2.merge(df_entity, how='left', left_on='Alias2', right_on='Alias2')
        df3.loc[(df3['Score'] >= df3['MinScore']), 'Success'] = True
        df3.loc[(df3['Score'] >= df3['MinScore']), 'Method'] = 'levenshtein'
        df4 = pd.concat([df_orig[~mask], df3])
    else:
        df4 = df_orig

    print('levenshtein match completed:', df4['Success'].sum(), 'of', len(df4), ' ', entity_col, 'successfully matched')

    return df4


def _pubchempy_match(df_orig, df_entity, entity_col, source_language='NL', strip_bracket=False, **kwargs):
    """Check whether a feature/unit name can match a pre-defined alias/synonym in pubchem after translating to English."""

    if entity_col != 'Feature':
        print("ERROR: pubchempy matching can only be performed on 'Features'")

    # select features that are not yet matched
    mask = (df_orig['Success'] == False)
    df1 = df_orig[mask].reset_index(drop=True)
 #   df1 = df1[set(df1.columns) - set(df_entity.columns)] # drop overlapping columns to prevent error with merge in next step

    if len(df1) > 0:
        # remove all symbols in feature between brackets
        if strip_bracket == True:
            df1['Feature_orig3'] = df1['Feature_orig'].str.replace(r'\(.*\)', '').str.rstrip()
        else:
            df1['Feature_orig3'] = df1['Feature_orig']

        # list Features to be translated
        features = list(df1['Feature_orig3'])

        if isinstance(source_language, str):
            # Call google translator. Repeat multiple times in case it fails for the first time due to API issues.
            attempt = 1
            while attempt <= 10:
                try:
                    translated_objects = Translator().translate(features, src=source_language, dest='EN')
                    features_english = [x.text for x in translated_objects]
                    print('Calling google translate API was successful after %i attemp(s).' % (attempt))
                    break
                except:
                    attempt += 1
                if attempt == 10:
                    print('WARNING: Calling google translate API failed after %i attemp(s).' % (attempt) +\
                        'Try it again later. pubchempy matching continues WITHOUT translation')
                    features_english = features
        else:
            features_english = features

        # use pubchempy to find component index (cid), cas and iupac of pupchem-database
        lst_cid = []
        lst_iupac = []
        Lst_cas = []

        n = len(df_orig)  # total number of features
        i = len(df_orig) - len(df1) + 1  # number of features already matched

        for feature in features_english:
            try:
                compounds = pcp.get_compounds(feature, 'name')  # find all compounds that match
                compound = pcp.Compound.from_cid(compounds[0].cid)  # use first in case get_compounds produces a list
                cid = compound.cid
                iupac = compound.iupac_name
                cas = _get_cas_from_compound(compound)[0]

            except:  # unknow reason that pcp cannot find component # To be improved#
                cid = ''
                iupac = ''
                cas = ''

            lst_cid.append(cid)
            lst_iupac.append(iupac)
            lst_cas.append(cas)

            if i % 20 == 0:
                print('pubchempy try match ', i, 'of', n, ' ', entity_col)
            i += 1

        # update dataframe
        df1['Feature_orig4'] = features_english  # Feature after translation
        df1['IUPAC_pubchem'] = lst_iupac
        df1['CID_pubchem'] = lst_cid
        df1['CAS_pubchem'] = lst_cas

        # Try to get feature by join with default database, else make IUPAC the Feature
        df1 = df1.merge(df_entity, how='left', left_on='IUPAC_pubchempy', right_on='IUPAC')

        # Log which features are succesfully matched
        mask_succes = df1['Feature'] != ''
        df1.loc[mask_succes, 'Success'] = True
        if strip_bracket == True:
            df1.loc[mask_succes, 'Method'] = 'pubchempy_stripbrackets'
        else:
            df1.loc[mask_succes, 'Method'] = 'pubchempy'

        # merge dataframe
        df2 = pd.concat([df_orig[~mask], df1])
    else:
        df2 = df_orig

    print('pubchempy match completed:', df2['Success'].sum(), 'of', len(df2), ' ', entity_col, 'successfully matched')

    return df2


# %% main functions
def generate_feature_map(entity_orig=[],
                         alias_entity={
                             **dict_alias_features['Feature'],
                             # **dict_alias_features['AliasEnglish'],
                             # **dict_alias_features['AliasDutch'],
                             },
                         entity_col='Feature',
                         string2whitespace=[],
                         string2replace=strings2replace(),
                         string2remove=strings2remove_from_features(),
                         strings_filtered=strings_filtered(),
                         match_method=['exact', 'ascii', 'pubchempy', 'levenshtein', 'pubchempy_stripbrackets'],
                         entity_minscore={1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75},
                         source_language='NL',
                         **kwargs):
    """
    Generate a mapping of original features to user defined (HGC compatible) features. See explanation under Notes.

    WARNING: it is recommended to always perform a visual check whether the mapping is correct.
    Especially for features matched with "Levenshtein" that perform close to the mimimum entity score.

    Parameters
    ----------
    entity_orig: list
        List with names of original features.
    alias_entity: dictionary,
        keys: Alias (synonyms) of the HGC-compatible features that will be matched to the original features.
            values: the HGC-compatible Features
        Example: {'iron': 'Fe', 'manganese': 'Mn'} -> iron and mangenese will be mapped to Fe and Mn
        Default:  a selection of "dict_alias_features()"
        The default is optimised to identify features for a combination of Dutch and English.
    entity_col: string
        Can be adjusted when using the function for something else than Features. For example "Units"
        default: 'Feature'
    string2whitespace: list
        List of strings/ symbols to replace by whitespace before performing named entity recognition (NER).
        WARNING: Case sensitive and also recognizes non ascii symbols
        Eefault: string2whitespace()
    string2replace: dictionary
        Dictionary with symbols/ strings to replace by another symbol before performing named entity recognition (NER).
        WARNING: Case sensitive and also recognizes non ascii symbols
        Eefault: string2replace()
    string2remove: list
        List of strings/ symbols to remove before performing named entity recognition (NER).
        WARNING: use only white space, numbers (0-9) and lowercase ascii letters (a-z).
        For example: "icpms" instead of "ICP-MS".
        Eefault: string2remove()
    strings_filtered: list
        List of strings that are used to recognize if a sample is filtered.
        WARNING: use only white space, numbers (0-9) and lowercase ascii letters (a-z).
        Default: strings_filtered()
    match_method: list
        'exact' : match original featres that are exacty the same as features/ alias entered by argument "alias_entity"
        'ascii' : same as 'exact' but after adjusting original features and HGC-aliases by:
            (1) Removing non ascii symbols.
            (2) Adjusting text entered under the arguments string2whitespace, string2replace and string2remove.
        'levenshtein' : same as 'ascii', but using the least Levenshtein Distance (fuzzywuzzy algorithm) to find
            which alias best matches the original feature. The minimum score entered by argument "entity_minscore" is
            used to evaluate if this match is good enough.
        'pubchempy' : use google translation and pubchempy (synonyms) to map original features to IUPAC name
        'pubchempy_stripbrackets' : same as 'pubchempy', but first remove tekst between brackets.
        Default: ['exact', 'ascii', 'pubchempy', 'levenshtein','pubchempy_stripbrackets']
        WARNING: 'levenshtein' and 'pubchempy' typically require long calculation time
        WARNING: 'pubchempy' generates features that are not defined in the argument 'dict_alias_feature'
    entity_minscore: dictionary
        Dictionary that controls the minimum score for feature recognition with 'Levenshtein'.
        This minimum score is a function of the feature's length and is generally higher for shorter features.
        keys: length of feature or unit (number of symbols; integer)
        values: minimum score required for a positive recognition (0-100 scale; integers)
        Example:
            {3:100, -> feature with length of 3 symbols must match 100%
            8:75} -> feature with lengt of 8 symbols must match for 75%
        Default: {1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75}
    source_language: 'string' or False
        if String: Translate feature from specified language to English when applying the 'pubchempy' match_method
            the string must be a language recognized under the "src" argument of googletrans.translator module
        if False: no translation when applying 'pubchempy' match_method
        Default: 'NL'

    Returns
    -------
    entity_map : dictionary
        mapping of original features/ units to features/ units used by HGC.
    entity_unmapped : list
        list of original features/ units that were not successfully matched to new features/ units.
    df_entity_map : dataframe
        dataframe with entire result of mapping and scores.
        column "Entity_orig" -> names/ features in original file
        column "Entity_orig2" -> "Entity_orig" after cleanup (only ascii, symbols removed/ replaced)
        column "Entity_orig3" -> "Entity_orig" after removing symbols between brackets
        column "Entity_orig4" -> "Entity_orig3" translated to English
        column "Entity" -> desired, HGC compatible feature/ unit
        column "Alias" -> Alias of desired feature/ unit
        column "Alias2" -> "Alias" after cleanup (only ascii, symbols removed/ replaced)
        column "Alias2_length" -> number of characters
        column "MinScore" -> minimum required similarity score (when using 'levenshtein'),
            . the minscore depends on the number of characters
        column "Score" -> similarity score afternamed_entity_recognition.utils matching with 'levenshtein'
        column "Succes" -> True if a feature/ unit was successfully matched
        column "MatchMethod" --> method used to successfully match the feature/ unit

    Notes
    -----
    The funtion has various built in Named Entity Recognition (NER) techniques to match original
    features to HGC-compatible features.

    "exact"
    First, the script checks whether the original features match

    'Levenshtein'
    Is a Named Entity Recognition (NER) that uses Levenshtein Distance to calculate the differences
    between original entities and a database. This database "dict__alias_features()" with both HGC-compatible
    and other features commonly used

    Original features are matched to the HGC-entity to which they
    have the least distance. A match is only successful if the score based on the Levenshtein Distance remains above
    a certain threshold. The user can use default HGC-compatible entities or specify own entities.

    'pubchempy'
    Uses functionality of pubchempy module to find IUPAC names. Primarily suitable for OMP's.'

    """
    print('start generating', entity_col, ' map...it may take a few minutes depending on the number of entries.')

    # generate a dataframe with the desired features/units and their alias
    df_entity = pd.DataFrame.from_dict({'Alias': list(alias_entity.keys()), entity_col: list(alias_entity.values())})
    df_entity.drop_duplicates(subset='Alias', inplace=True)
    df_entity.reset_index(inplace=True, drop=True)
    df_entity = _cleanup_alias(df=df_entity,  # get default alias w.r.t. features or units
                               col='Alias',
                               col2='Alias2',  # new column/name
                               string2replace=string2replace,
                               string2whitespace=string2whitespace,
                               string2remove=string2remove,
                               strings_filtered=[])

    # generate a dataframe with the original features/ units and their names after cleanup
    df_orig = pd.DataFrame(set(entity_orig), columns=[entity_col + '_orig'])
    df_orig.drop_duplicates(subset=entity_col + '_orig', inplace=True)
    df_orig.reset_index(inplace=True, drop=True)
    df_orig = _cleanup_alias(df=df_orig,
                             col=entity_col + '_orig',
                             col2=entity_col + '_orig2',
                             string2replace=string2replace,
                             string2whitespace=string2whitespace,
                             string2remove=string2remove,
                             strings_filtered=strings_filtered)
    if 'Filtered' not in df_orig.columns:
        df_orig['Filtered'] = np.nan

    # define minimum score for 'Levenstein' match_method
    f_minscore = _interp1d_fill_value(x=entity_minscore.keys(), y=entity_minscore.values())
    df_entity['Alias2_length'] = df_entity['Alias2'].astype(str).map(len)
    df_entity['MinScore'] = f_minscore(df_entity['Alias2_length'])

    # make columns to log matching
    df_orig['MatchMethod'] = False
    df_orig['Success'] = False

    # loop through matching methods
    for method in match_method:
        if method == 'exact':
            df_orig = _exact_match(df_orig, df_entity, entity_col)
        elif method == 'ascii':
            df_orig = _ascii_match(df_orig, df_entity, entity_col)
        elif method == 'levenshtein':
            df_orig = _levenshtein_match(df_orig, df_entity, entity_col)
        elif method == 'pubchempy':
            df_orig = _pubchempy_match(df_orig, df_entity, entity_col, source_language=source_language, strip_bracket=False)
        elif method == 'pubchempy_stripbrackets':
            df_orig = _pubchempy_match(df_orig, df_entity, entity_col, source_language=source_language, strip_bracket=True)
        else:
            print('ERROR: ', method, 'is not recognized')

    # sometimes, an Alias2 can be matched to multiple Alias --> show only first option
    df_entity_map = df_orig.drop_duplicates(subset=[entity_col + '_orig'])
    df_entity_map.reset_index(inplace=True, drop=True)

    # generate a dictionary/ list with the successful and unsuccessful matched entities
    mask = (df_entity_map['Success'] == True)
    entity_map = dict(zip(df_entity_map[entity_col + '_orig'][mask], df_entity_map[entity_col][mask]))
    entity_unmapped = list(df_entity_map[entity_col + '_orig'][~mask])

    print('completed generating', entity_col, 'map.')

    return entity_map, entity_unmapped, df_entity_map


def generate_unit_map(unit_orig=[],
                      alias_unit={
                          **dict_alias_units['Unit'],
                          **dict_alias_units['AliasEnglish'],
                          **dict_alias_units['AliasDutch'],
                      },
                      unit_col='Unit',
                      string2whitespace_unit=['/', '-'],
                      string2replace_unit=strings2replace(),
                      string2remove_unit=strings2remove_from_units(features2remove=[k for k, v in dict_features_category.items() if v in ['atoms', 'ions', 'other']]),
                      strings_filtered_unit=[],
                      entity_minscore_unit={1: 100, 5: 100, 6: 90, 7: 85, 8: 80, 10: 75},
                      match_method_unit=['exact', 'ascii', 'levenshtein'],
                      **kwargs):
    """
    Convenience function based on "generate_feature_map()" but with recommended defaults for mapping units.

    Parameters
    ----------
    Parameter names are modified from "generate_feature_map()".
    entity_orig -> unit_orig
    alias_entity -> alias_unit
    entity_col -> unit_col
    string2whitespace -> string2whitespace_unit
    string2replace -> string2replace_unit
    string2remove -> string2remove_unit
    strings_filtered -> strings_filtered_unit
    entity_minscore -> entity_minscore_unit
    match_method -> match_method_unit

    Returns
    -------
    unit_map, unit_unmapped, df_unit_map

    """
    # removing leading white spaces in the string
    unit_orig_lstrip = [string.lstrip() for string in unit_orig]

    unit_map, unit_unmapped, df_unit_map =\
        generate_feature_map(entity_orig=unit_orig_lstrip,
                             alias_entity=alias_unit,
                             entity_col=unit_col,
                             string2whitespace=string2whitespace_unit,
                             string2replace=string2replace_unit,
                             string2remove=string2remove_unit,
                             strings_filtered=strings_filtered_unit,
                             entity_minscore=entity_minscore_unit,
                             match_method=match_method_unit)

    return unit_map, unit_unmapped, df_unit_map
