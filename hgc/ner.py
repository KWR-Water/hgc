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
from googletrans import Translator
import pubchempy as pcp


# maintenance_flag = 'n'
# %% Defaults
def entire_feature_alias_table():
    """Get a dataframe with HGC features and various columns with alias (synonyms) for these features.

    Return
    ------
    Dataframe :
        The dataframe has a "Feature" column. And various other columns with Alias
        for these features including CAS, SIKB, Dutch Alias, English Alias.
        Each cell contains one or more alias (e.g. iron; FeII).
        These aliases must be separated by "|".
    """
    file_path = Path(constants.__file__).parent / 'default_features_alias.csv'
    df = pd.read_csv(file_path, encoding='utf-8', header=0) 
    return df


def entire_unit_alias_table():
    """ Get a dataframe with units recognized by HGC and various columns with alias (synonyms) for these units.

    Return
    ------
    Dataframe :
        The dataframe has a "Unit" column. And various other columns with Alias.
        Each cell contains one or more alias (e.g. "mg-N/L"; "mgN/ L").
        These aliases must be separated by "|". 

    """
    file_path = Path(constants.__file__).parent / 'default_units_alias.csv'
    df = pd.read_csv(file_path, encoding='utf-8', header=0)
    return df


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
        Repeat the <entity_col> here if you want to add the entity to the list of
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
    # Deep copy here
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
    df2['Alias'] = df2['Alias'].str.split('|')  # split cell to list. Note "|" is used as a seperator!!
    df2 = df2.explode('Alias')
    df2['Alias'] = df2['Alias'].str.strip()
    df2.dropna(inplace=True)

    # drop empty Alias values
    df2 = df2.loc[~(df2['Alias'] == '')]

    # if entity_col in alias_cols:
    #     df.drop('Entity_temp', axis=1, inplace=True)
    # else:
    #     df.rename({'Entity_temp': entity_col}, axis=1, inplace=True)

    return df2


def generate_feature_alias():
    """
    Get a df with default HGC features and their aliases. 
    Previously called: default_feature_alias_dutch_english
    """
    
    df0 = generate_entity_alias(
            df=entire_feature_alias_table(),
            entity_col='Feature',
            alias_cols=['Feature', 'IUPAC',
                        'UserDefined_Dutch', 'UserDefined_English',
                        'SIKBcode', 'SIKBomschrijving']) # those alias cols should be corresponding the headers of the default csv file. 
    return df0


def generate_unit_alias():
    """
    Get a df with default HGC units and aliases.
    Previously called: default_unit_alias
    """
    df0 = generate_entity_alias(
            df=entire_unit_alias_table(),
            entity_col='Unit', 
            alias_cols=['Unit', 'Alias (Dutch)', 'Alias (English)']) # those alias cols should be corresponding the headers of the default csv file.
    return df0


def default_feature_minscore():
    """
    Threshold score for accepting a matched feature name.
    Relation between word length (keys) and minimum score for named entity recognition of features (values).
    """
    dct = {
        1: 100, # exactly matching
        3: 100, # exactly matching
        4: 75, # at most one mismatching
        5: 80, # at most one mismatching
        6: 66, # at most two mismatching
        8: 75  # at most two mismatching
    }
    return dct


def default_unit_minscore():
    """
    Threshold score for accepting a matched unit.
    Relation between word length (keys) and minimum score for named entity recognition of units (values).
    """
    dct = {
        1: 100, # exactly matching
        3: 100, # exactly matching
        4: 75, # at most one mismatching
        6: 66, # at most two mismatching
        8: 75, # at most two mismatching
        10: 70 # at most three mismatching
    }
    return dct


def strings2remove_from_features():
    """
    Generate a list of unwanted strings that are sometimes used with the features.
    This list is specifically made after examining a couple of files from Dutch water companies.
    It may need to expanded for a broader use in the future. #To be improved#
    """
    # in list order: first use longer string, then shorter version. 
    lst = [' icpms', ' icpaes', ' gf aas', ' icp', ' koude damp aas', ' koude damp',  # whitespace, string
           ' berekend', 'opdrachtgever', ' gehalte',
           ' tijdens meting',
           ' gefiltreerd', ' na filtratie', ' filtered', ' gef', ' filtratie',
           ' na destructie', 'destructie', ' na aanzuren', ' aanzuren',
           ' bij ',  # whitespace, string, whitespace
           ]
    return lst


# generate a list of default features (only for ions, atoms and others)
def generate_feature2remove(default_table = entire_feature_alias_table(), default_list = ['atoms', 'ions', 'other']):
    """
    Generate a list of features to remove. 
    Use the default table/list ('atoms', 'ions', 'other') if no input is given by users.
    """

    mask = default_table['Category'].isin(default_list)
    features2remove = list(set(list(default_table['Feature'][mask]))) # NH4
    return features2remove


def strings2remove_from_units(features2remove = generate_feature2remove(entire_feature_alias_table()),
                              other_strings2remove = ['eenh', 'nvt']):
    """
    Generate a list of unwantes strings that are sometimes combined with the units.

    The function generates a list of strings that needs to be removed from the original units
    before performing named entity recogntion. 
    The list is based on the default_units and other strings
    Note this list is also specifically made after examining a couple of files from Dutch water companies. #To be improved#

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
    # retain N, P, S and Si (e.g., from mg-N/L, mg-P/L, etc.)
    lst = list(set(features2remove) - set(['N', 'P', 'S', 'Si']))

    # remove leading space if there is any and then add a white space before feature and make lower case
    lst = [string.lstrip() for string in lst]
    lst = [' ' + x.lower() for x in lst]

    lst = list(set(lst + other_strings2remove))

    # sort long to short string, to ensure that longest string is entirely removed
    lst.sort(key=len, reverse=True)

    return lst


def _strings_filtered():
    """
    Generate a list of strings that can be used to recognize if a sample is filtered.
    Note: put whitespace before string, lowercase, only letters and symbols.
    """
    lst = [' gefiltreerd', ' na filtratie', ' filtered', ' filtration', ' gef', ' filtratie']
    return lst

def _exact_match(df_entity_orig, df_entity_alias, entity_col):
    """
    Check whether a feature/unit name exactly matched a pre-defined alias/synonym. 
    If so, save the matched items in df1 and raise a score of 101. 
    Otherwise, pass the unrecognizable items to df_entity_orig1

    Note: whatever matching method is selected, this step is a compulsory step to be implemented. 

    Parameters
    ----------
    df_entity_orig : dataframe
        orginal df with feature/unit names.

    df_entity_alias : dataframe
        alias to be matched with.
    
    entity_col : string
        'feature' or 'Unit

    Returns
    -------
    df1 : dataframe with items that can be matched.    
    df_entity_orig1: dataframe with items that can be matched at this step.    
    """ 

    # combine intersection of orginals and alias
    df1 = df_entity_orig.merge(df_entity_alias, how='left',
                               left_on=entity_col + '_orig', right_on='Alias') 

    # use df_entity_orig1 to store features without alias while use df1 to store those with alias
    df_entity_orig1 = df1.loc[df1['Alias'].isnull()][[entity_col + '_orig', entity_col + '_orig2', 'Filtered']].reset_index(drop=True)
    df1 = df1.loc[~df1['Alias'].isnull()].reset_index(drop=True).drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)   
    
    # mark 101 for those exactly matching, also indicating this is step 1
    if len(df1) != 0:
        df1.loc[:, "Score"] = 101 

    return df1, df_entity_orig1

def _ascii_match(df_entity_orig1, df_entity_alias, entity_col, match_method, df1):
    """
    Check whether a feature/unit name can 'ascii-ly' (column _orig2) match a pre-defined alias/synonym. 
    If so, save the matched items in df2 and raise a score of 102. 
    Otherwise, pass the unrecognizable items to df_entity_orig2

    Parameters
    ----------
    df_entity_orig1 : dataframe
        orginal df with feature/unit names.

    df_entity_alias : dataframe
        alias to be matched with.
    
    entity_col : string
        'feature' or 'Unit

    match_method : method for matching
        if method is in ['levenshtein', 'ascii', 'languageTrans'], this step will be implemented
    
    df1 : dataframe
        what has been processed from the previous step

    Returns
    -------
    df2 : dataframe with items that can be matched.    
    df_entity_orig2: dataframe with items that can be matched at this step.    
    """ 

    if match_method in ['levenshtein', 'ascii', 'languageTrans']:

        # continue merging the rest of df1 with alias2 (with ascii)
        df2 = df_entity_orig1.merge(df_entity_alias, how='left',
                                left_on=entity_col + '_orig2', right_on='Alias2')

        # still use df_entity_orig2 to store features without alias while use df2 to store those with alias
        df_entity_orig2 = df2.loc[df2['Alias'].isnull()][[entity_col + '_orig', entity_col + '_orig2', 'Filtered']].reset_index(drop=True)
        df2 = df2.loc[~df2['Alias'].isnull()].reset_index(drop=True).drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)  
        
        # mark 102 for those matching ascii cleanups, indicating the 2nd step
        if len(df2) != 0:
            df2.loc[:, "Score"] = 102

    else:
        df_entity_orig2 = df_entity_orig1 # if not method specified, skip step2 and keep using orig 1 
        df2 = pd.DataFrame([], columns=df1.columns) # and make df2 empty then 
    
    return df2, df_entity_orig2
    

def _fuzzy_match(df_entity_orig3, df_entity_alias, entity_col, match_method, df1, df2, df3, f_minscore):
    """
    Check whether a feature/unit name can 'fuzzi-ly' match a pre-defined alias/synonym. 
    If so, save the matched items in df3 and raise a score according the number of matching characters. 
    Later, the score will be compared to the threshold. Only the ones higher than the threshold will be kept.
    Otherwise, pass the unrecognizable items to df_entity_orig3

    Parameters
    ----------
    df_entity_orig3 : dataframe
        orginal df with feature/unit names.

    df_entity_alias : dataframe
        alias to be matched with.
    
    entity_col : string
        'feature' or 'Unit

    match_method : method for matching
        if method is in ['levenshtein'], this step will be implemented
    
    df1, df2, df3 : dataframes
        what have been processed from the previous step

    Returns
    -------
    df3 : dataframe with items that can be matched.    
    df_entity_orig3: dataframe with items that can be matched at this step.    
    """ 

    if match_method in ['levenshtein']:
        
        # use fuzzywuzzy to calculate similarity
        choices = df_entity_alias['Alias2']
        feature_orig2alias = []
        i = len(df1) + len(df2) + len(df3)
        for query in df_entity_orig3[entity_col + '_orig2']:
            feature_orig2alias.append(process.extractOne(query, choices, scorer=fuzz.token_sort_ratio)) # note: if input is series, return index too
        df4t = pd.concat(
            [df_entity_orig3, pd.DataFrame(feature_orig2alias, columns=['Alias2', 'Score', 'Index_orig'])],
            axis=1).drop('Index_orig', axis=1)
        df4t = df4t.merge(df_entity_alias, on='Alias2').drop_duplicates(subset=[entity_col + '_orig']).reset_index(drop=True)

        # save the ones whose scores are higher than the threshold
        if not df4t.empty:
            df4t.loc[:,'Alias2_length'] = df4t['Alias'].astype(str).map(len)
            df4t.loc[:,'MinScore'] = f_minscore(df4t['Alias2_length'])
            df4t.loc[:,'Success'] = np.where(df4t['Score'] >= df4t['MinScore'], True, False)
        else: 
            df4t.loc[:,'Alias2_length'] = []
            df4t.loc[:,'MinScore'] = []
            df4t.loc[:,'Success'] = [] 
        mask = df4t['Success'] == True
        df4 = df4t[mask].drop(['Alias2_length', 'MinScore', 'Success'], axis=1) # save those in df4t only, but not in df4 to keep df4 the same structure as df3
        if not all(mask):
            if entity_col == 'Feature':       
                df_entity_orig4 = df4t[np.logical_not(mask)][['Feature_orig', 'Feature_orig2', 'Filtered']]
            elif entity_col == 'Unit':
                df_entity_orig4 = df4t[np.logical_not(mask)][['Unit_orig', 'Unit_orig2', 'Filtered']]
        else:
            if entity_col == 'Feature':       
                df_entity_orig4 = pd.DataFrame([], columns=['Feature_orig', 'Feature_orig2', 'Filtered'])
            elif entity_col == 'Unit':
                df_entity_orig4 =  pd.DataFrame([], columns=['Unit_orig', 'Unit_orig2', 'Filtered'])

    else:
        df4 = pd.DataFrame([], columns=df1.columns) # otherwise, make all df's empty 
        df_entity_orig4 = df_entity_orig3       
        df4t =  pd.DataFrame()

    return df4, df_entity_orig4, df4t


def _translate_matching(df_entity_orig2, match_method, entity_col, trans_from = 'NL', trans_to = 'EN',  bracket = 'with'):
    """
    Check whether a feature/unit name can match a pre-defined alias/synonym in pubchem after google translation. 
    Frist use google translate to convert Dutch (default) alias to English, then use exact match for names in pubchempy.
    Language default: to translate Dutch to English. Other languages are also supported. Check Google for language codes.
    
    If matched, save the matched items in df3 and raise a score 103 (with information from brackets) 
    or 105 (without information from brackets). Otherwise, pass the unrecognizable items to df_entity_orig3

    Parameters
    ----------
    df_entity_orig2 : dataframe
        orginal df with feature/unit names.

    match_method : method for matching
        if method is in ['levenshtein', 'languageTrans'], this step will be implemented
       
    entity_col : string
        'feature' or 'Unit

    trans_from : string
        original language, default is 'NL' 
    
    trans_to : string
        destination language, default is 'EN'
    
    bracket : string
        option to include information from brackets or not choose from 'with' and 'without'

    Returns
    -------
    df3 : dataframe with items that can be matched.    
    df_entity_orig3: dataframe with items that can be matched at this step.    
    """ 

    # saved for testing
    # df_entity_orig2.Feature_orig[0] = '1,2,3-trimethylbenzeen'
    # df_entity_orig2.Feature_orig[1] = '1,2,3,4-tetramethylbenzeen'
    # df_entity_orig2.loc[2,'Feature_orig'] = 'nothing'
    if match_method in ['levenshtein', 'languageTrans'] and entity_col == 'Feature': # Note only implemented on feature 
        # process the information in brackets first, include or exclude.
        if bracket == 'with':
            pass
        elif bracket == 'without':
            df_entity_orig2.loc[:,'Feature_orig'] = df_entity_orig2.loc[:,'Feature_orig'].str.replace(r'\(.*\)', '').str.rstrip()
        else:
            print('Keyword for "bracket" is unknow. It can be either "with" or "without" only. We use default "with" then.')

        # get a list to be translated
        name2trans = list(df_entity_orig2.Feature_orig)
        
        # Next, call google translator two times in case it fails for the first time due to API issues. 
        attemp = 1
        while attemp <= 10: # google api may fail randomly, just try it for 10 times
            try:
                name_transed_cls = Translator().translate(name2trans, src=trans_from, dest=trans_to)
                print('Calling google translate API was successful after %i attemp(s).' % (attemp))
                flag = 'y'
                break
            except:
                attemp += 1
            if attemp == 10:
                print('Calling google translate API failed after %i attemp(s). Try it again later.' % (attemp))
                flag = 'n'
    
        # get compound index (cid) from the translated/original names
        if flag == 'y':
            idx = [pcp.get_compounds(component.text, 'name') for component in name_transed_cls] 
        elif flag == 'n': # keep the lopp here as strang thing may happen with pubchem...
            idx = []
            for component in name2trans:
                try:
                    idx.append(pcp.get_compounds(component, 'name'))
                except: # unknow reason that pcp cannot find component # To be improved#
                    idx.append([])
            # idx = [pcp.get_compounds(component, 'name') for component in name2trans] 

        # get  
        empty_check = all([not elem for elem in idx])
        if empty_check: 
            df3 = pd.DataFrame()
            df_entity_orig3 = copy.deepcopy(df_entity_orig2)
        else:        
            compounds = [pcp.Compound.from_cid(idx0[0].cid) if idx0 != [] else [] for idx0 in idx ]
            iupac_name = [compound.iupac_name if compound != [] else [] for compound in compounds]
            # reconstruct df_trans as the df1 and df2
            df_trans = copy.deepcopy(df_entity_orig2)
            df_trans.loc[:,'Feature'] = iupac_name
            df_trans.loc[:,'Alias'] = iupac_name
            df_trans.loc[:,'Alias2'] = iupac_name
            df_trans.loc[:,'Index_orig'] = None # not needed as df_entity_alias is not called here

            # for i in range(len(df_trans['iupac'])):
            #     df_trans['synonyms'][i] = '; '.join([elem for elem in synonyms[i]])
            # default_trans_feature = generate_entity_alias(df=df_trans,entity_col='iupac',alias_cols=['iupac', 'before_trans','synonyms']).reset_index(drop=True)
            # default_trans_feature.rename(columns={'iupac':'Feature'}, inplace = True)
            # df4 = df_entity_orig2.merge(default_trans_feature, how='left',
            #                        left_on='Feature_orig', right_on='Alias') # combine intersection of two df's

            # get the succefully matched parts whose Feature is not empty
            mask = [not not item for item in df_trans['Feature']]
            df3 = df_trans[mask]
            if len(df3) != 0:
                if bracket == 'with':
                    df3.loc[:,'Score'] = 103 # indicating step 3
                elif bracket == 'without': 
                    df3.loc[:,'Score'] = 105 # indicating step 5  

            df_entity_orig3 = df_trans[np.logical_not(mask)][['Feature_orig', 'Feature_orig2', 'Filtered']]

    else:
        df_entity_orig3 = df_entity_orig2 # if not method specified, skip step2 and keep using orig 1 
        df3 = pd.DataFrame()

    return df3, df_entity_orig3

# %% main function
def _interp1d_fill_value(x=[], y=[]):
    """
    Generate a linear point-2-point interpolatation function with fixed fill value outside x-range.

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
    Remove all rather than ascii letters and numbers
    Remove unwanted strings (e.g. icpms)
    Trim whitespace

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
                
    # fuzzywuzzy only uses numbers and ascii letters (a-z; A-Z) and replaces all other symbols by whitespace
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
                        strings_filtered_gem=[],
                        entity_minscore={},
                        language_from_to=['NL', 'EN'],
                        match_method='levenshtein'):
    """
    Generate a map to convert a list of original entities (features/ units) to HGC compatible features.
    Called by generate_feature_map and generate_unit_map

    The funtion uses Named Entity Recognition (NER) techniques to match original entities to the entities used by HGC.
    It is based on the fuzzywuzzy module. And it uses Levenshtein Distance to calculate the differences between
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

    language_from_to : list
        Translate from 1st language to the 2nd one

    match_method: string {'exact', 'ascii', 'levenshtein', 'languageTrans'}
        'exact' : match original entity and Alias only when the strings are exactly the same.
        This is the recommended method for matching CAS number.
        'ascii' : match after removing non ascii symbols from original entities and aliases.
        'levenshtein' : match using the least Levenshtein Distance (fuzzywuzzy algorithm).
        'languageTrans' : use google translation and pubchem to match
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
    # generate the dataframe with the desired features/units
    df_entity_alias = _cleanup_alias(df=df_entity_alias, # get default alias w.r.t. features or units
                                     col='Alias',
                                     col2='Alias2', # new column/name
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
                                    strings_filtered=strings_filtered_gem)
    if 'Filtered' not in df_entity_orig.columns:
        df_entity_orig['Filtered']=np.nan
  
    # define score threshold
    f_minscore = _interp1d_fill_value(x=entity_minscore.keys(), y=entity_minscore.values())

    # Step 1: Exact match entities merge df with alias 1 (without ascii)
    df1, df_entity_orig1 = _exact_match(df_entity_orig, df_entity_alias, entity_col)

    # Step 2: match after ascii cleanup of entities
    df2, df_entity_orig2 = _ascii_match(df_entity_orig1, df_entity_alias, entity_col, match_method, df1)

    # Step 3: Use google translate to convert Dutch/other names to English names
    # NOTE: the threshold score is implemented INSIDE step 3, unsuccessful matching will not count and will be stored in df_entity_orig3
    df3, df_entity_orig3 = _translate_matching(df_entity_orig2, match_method, entity_col, trans_from = language_from_to[0], trans_to = language_from_to[1], bracket = 'with')

    # Step 4: match entities using least Levenshtein distance
    df4, df_entity_orig4, df4_check_score = _fuzzy_match(df_entity_orig3, df_entity_alias, entity_col, match_method, df1, df2, df3, f_minscore)

    # step 5: deal with those cannot be dealt with by step 3&4 due to brackets
    df5, df_entity_orig5 = _translate_matching(df_entity_orig4, match_method, entity_col, trans_from = language_from_to[0], trans_to = language_from_to[1], bracket = 'without')

    # now combine all three dataframes and (optionally?) add minimum score
    df_entity_map = pd.concat([df1, df2, df3, df4, df5, df_entity_orig5], axis=0, ignore_index=True)
    # df_entity_map['MinScore'] = f_minscore(df_entity_map['Alias'].astype(str).map(len))

    # sometimes, an Alias2 can be matched to multiple Alias --> show only first option
    df_entity_map.drop_duplicates(subset=[entity_col + '_orig'], inplace=True)
    df_entity_map.reset_index(inplace=True, drop=True)

    # generate a dictionary/ list with the succesful and unsuccesful matched entities
    mask = ~np.isnan(df_entity_map['Score']) # If there is a score, it means the matching is acceptable. No score means no good matching. 
    entity_map = dict(zip(df_entity_map[entity_col + '_orig'][mask], df_entity_map[entity_col][mask]))
    entity_unmapped = list(df_entity_map[entity_col + '_orig'][~mask])

    return entity_map, entity_unmapped, df_entity_map
    
    
def generate_feature_map(entity_orig=[],
                         df_entity_alias=generate_feature_alias(),
                         entity_col='Feature',
                         string2whitespace=[],
                         string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                                         'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                                         'μ': 'u', 'µ': 'u', '%': 'percentage'},
                         string2remove=strings2remove_from_features(),
                         strings_filtered_gfm=_strings_filtered(),
                         entity_minscore=default_feature_minscore(),
                         match_method='levenshtein'):
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping features."""
    print('Recognizing feature names now...it may take up to a few minutes based on the size of the file.')

    feature_map, feature_unmapped, df_feature_map =\
        generate_entity_map(entity_orig=entity_orig,
                            df_entity_alias=df_entity_alias,
                            entity_col=entity_col,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            strings_filtered_gem=strings_filtered_gfm,
                            entity_minscore=default_feature_minscore(),
                            match_method=match_method)
    print('Feature recognition is done.')

    return feature_map, feature_unmapped, df_feature_map


def generate_unit_map(entity_orig=[],
                      df_entity_alias=generate_unit_alias(),
                      entity_col='Unit',
                      string2whitespace=['/', '-'],
                      string2replace={'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                                      'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                                      'μ': 'u', 'µ': 'u', '%': 'percentage'},
                      string2remove=strings2remove_from_units(),
                      strings_filtered_gum=[],
                      entity_minscore=default_unit_minscore(),
                      match_method='levenshtein'):                      
    """Convenience function based on "generate_entity_map" but with recommended defaults for mapping units."""
    print('Recognizing units now...it may take up to a few minutes based on the size of the file.')

    # removing leading white spaces in the string
    entity_orig_lstrip = [string.lstrip() for string in entity_orig]

    unit_map, unit_unmapped, df_unit_map =\
        generate_entity_map(entity_orig=entity_orig_lstrip,
                            df_entity_alias=df_entity_alias,
                            entity_col=entity_col,
                            string2whitespace=string2whitespace,
                            string2replace=string2replace,
                            string2remove=string2remove,
                            strings_filtered_gem=strings_filtered_gum,
                            entity_minscore=entity_minscore,
                            match_method=match_method)
    print('Unit recognition is done.')

    return unit_map, unit_unmapped, df_unit_map

