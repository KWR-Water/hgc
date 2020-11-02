# -*- coding: utf-8 -*-
"""
Routine to read and clean water quality data of wide/stacked formats 
Xin Tian, Martin van der Schans
KWR, April-July 2020
Last edit: July 27. Not upodating any more and use the new version. 
"""
import pandas as pd
import numpy as np
import logging
import os
import math
# from unit_converter.converter import convert, converts
import re
from molmass import Formula

# %% HGC.IO.defaults
# New definition of NaN. Based on default values of python with the following exception:
# 'NA' is left out to prevent NA (Sodium) being read as NaN.
NA_VALUES = ['#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
             '1.#IND', '1.#QNAN', 'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null']
# The following dictionary should be extracted from HGC.constants and augmented (or overruled) by the user
DATAMODEL_HGC = {
    'HGC_default_feature_units': {
        'Fe': 'mg/L',
        'SO4': 'mg/L',
        'Al': 'µg/L',
    },
}
UNIT_CONVERSION = {
    'mm':0.001, 'cm':0.01, 'm':1.0, 'km':1000, # add length here
    'ng':1e-9, 'μg':0.000001, 'mg':0.001, 'g':1.0, 'kg':1000, # add mass here
    'mL':0.001, 'L':1.0, # add volumn here
    'μS':1e-6, 'mS':0.001, 'S':1.0, # add conductivity here
    'mV': 0.001, 'V':1.0, # add voltage here
    'μmol':1e-6, 'mmol':0.001, 'mol':1.0, # add mol here
    }
# The following keyworded arguments can be adjusted and merged with the configuration dictionary by the user
KWARGS = {
    'na_values': NA_VALUES,
    'encoding': 'ISO-8859-1',
    'delimiter': None,
}
DEFAULT_FORMAT = {
    'Value': 'float64', 
    'Feature': 'string', 
    'Unit': 'string', 
    'Date': 'date', 
    'LocationID': 'string', 
    'SampleID': 'string', 
    'X': 'float64', 
    'Y': 'float64',
    }
# %% define sub-function to be called by the main function 
def read_file(file_path='', sheet_name=0, na_values=NA_VALUES, encoding='ISO-8859-1', delimiter=None, **kwargs):
    """
    Read pandas dataframe or file.
    Parameters
    ----------
    file_path : dataframe or string
        string must refer to file. Currenlty, Excel and csv are supported
    sheet_name : integer or string
        optional, when using Excel file and not reading first sheet
    na_values : list
        list of strings that are recognized as NaN
    """
    logger.info('Reading input file(s) now...')
    if isinstance(file_path, pd.DataFrame):
        # skipping reading if the input is already a df
        df = file_path
        # print('dataframe read: ' + [x for x in globals() if globals()[x] is file_path][0])
        logger.info('A dataframe has been imported')     
    elif isinstance(file_path, str):
        file_extension = file_path.split('.')[-1]
        # filename, file_extension = os.path.splitext(file_path)
        if (file_extension == 'xlsx') or (file_extension == 'xls'):
            try:
                df = pd.read_excel(file_path,
                                   sheet_name=sheet_name,
                                   header=None,
                                   index_col=None,
                                   na_values=na_values,
                                   keep_default_na=False,
                                   encoding=encoding)
                logger.info('A excel spreadsheet has been imported')
            except:
                df = []
                logger.error('Encountered an error when importing excel spreadsheet')
        elif file_extension == 'csv':
            try:
                df = pd.read_csv(file_path,
                                 encoding=encoding,
                                 header=None,
                                 index_col=None,
                                 low_memory=False,
                                 na_values=na_values,
                                 keep_default_na=False,
                                 delimiter=delimiter)
                logger.info('A csv has been imported')
            except:
                df = []
                logger.error('Encountered an error when importing csv')
        else:
            df= []
            logger.error('Not a recognizable file. Need a csv or xls(x) file.')
    else:
        df= []
        logger.error(['This file path is not recognized: '+file_path])
    return df

def _get_slice(df, arrays):
    """    Get values by slicing    """
    if isinstance(arrays[0], list):  # check if the array is nested
        series = pd.Series([], dtype='object')
        for array in arrays:
            series = series.append(df.iloc[array[0], array[1]].rename(0))
    elif len(arrays) == 1:  # only row specified
        series = df.iloc[arrays[0]]
    else:  # row and column specified
        series = df.iloc[arrays[0], arrays[1]]
    return series

def get_headers_wide(df, slice_sample='', slice_feature='', slice_unit='', **kwargs):
    """    Get column headers for a wide-format dataframe.    """
    # create series with headers
    header_sample = _get_slice(df, slice_sample)
    header_feature = _get_slice(df, slice_feature)
    header_unit = _get_slice(df, slice_unit)
    # get headers at 2 levels
    ncols = len(df.columns)
    level0 = pd.Series(ncols * [''])
    level0[header_sample.index] = header_sample
    level0[header_feature.index] = header_feature
    level1 = pd.Series(ncols * [''])
    level1[header_unit.index] = header_unit
    # add series by multi-index headers
    df.columns = pd.MultiIndex.from_arrays([level0, level1])
    logger.info('Got column headers for a wide-format dataframe.')
    return df, header_sample, header_feature, header_unit

def get_headers_stacked(df, slice_sample='', **kwargs):
    """    Get column headers for a stacked-format dataframe.    """
    # create series with headers
    header_sample = _get_slice(df, slice_sample)
    # add column names 
    ncols = len(df.columns)
    level0 = pd.Series(ncols * [''])
    level0[header_sample.index] = header_sample
    df.columns = level0   
    return df, header_sample

def slice_rows_with_data(df, slice_data=None, **kwargs):
    """    Getting needed data by pre-defined slicing blocks    """
    df2 = pd.DataFrame([])
    # # if isinstance(slice_data, list):
    # #     df2 = df.iloc[slice_data[0][0], :]
    # # else:
    # #     logger.error('Slicing_data must be a list')
    # df2 = df.iloc[slice_data[0]]
    # logger.info('Got needed data by pre-defined slicing blocks')
    df2 = df.iloc[slice_data[0][0], :]
    return df2

def _map_header_2_multilevel(map_header):
    """    Convert dictionary with mapping of columns to multiindex.    """
    map_header2 = {}
    for key, value in map_header.items():
        map_header2[(key, '')] = (value, '')
    return map_header2

def rename_headers_wide(df, map_header={}, **kwargs):
    """    Rename columns by pre-defined names for wide format.    """
    # remove duplicate columns, only keep the column that shows for the first time!
    df = df.groupby(level=[0, 1], axis=1).first()
    # remove columns without headers
    mask1 = df.columns.get_level_values(0).isin([''] + list(np.arange(0, len(df.columns))))
    cols1 = np.array(list(df))[mask1]
    cols2 = list(set(zip(list(cols1[:, 0]), list(cols1[:, 1]))))
    df.drop(cols2, axis=1, inplace=True)
    # remove columns that are in values but absent from keys
    keys = map_header.keys()
    values = map_header.values()  
    col_in_val_not_in_key = list(set(df.columns.levels[0]) & set(values) - set(keys))
    df.drop(col_in_val_not_in_key, axis=1, inplace=True)
    logger.info('Headers from the wide-format dataframe have been retrieved')
    return df

def rename_headers_stacked(df, map_header={}, **kwargs):
    """    Rename columns by pre-defined names for stacked format    """
    # remove duplicate columns, only keep the column that shows for the first time!
    df = df.groupby(level=[0], axis=1).first()
    # remove columns without headers
    mask1 = df.columns.get_level_values(0).isin([''] + list(np.arange(0, len(df.columns))))
    cols1 = np.array(list(df))[mask1]
    cols2 = list(cols1)
    df.drop(cols2, axis=1, inplace=True)
    # remove columns that are in values but absent from keys
    # (to prevent identical column names when mapping column names)
    keys = map_header.keys()
    values = map_header.values()  
    col_in_val_not_in_key = list(set(df.columns) & set(values) - set(keys))
    df.drop(col_in_val_not_in_key, axis=1, inplace=True)
    logger.info('Headers from the stacked-format dataframe have been retrieved')
    return df

def melt_wide_to_stacked(df, map_header={}, **kwargs):
    """    Turn wide format to stacked format    """
    # Convert mapping to multilevel index
    map_header2 = _map_header_2_multilevel(map_header)
    # Drop columns that are not present in dataframe
    map_header3 = list(set(map_header2) & set(df.columns))
    # Convert to stacked shape
    df2 = pd.melt(df, id_vars=map_header3, var_name=['Feature', 'Unit'], value_name='Value')
    # Convert multiindex to single index (some headers still have a multi-index after melt)
    col2 = []
    for col in df2.columns:
        if isinstance(col, tuple):
            col2.append(col[0])
        else:
            col2.append(col)
    df2.columns = col2
    logger.info('Turned wide format to stacked format')
    return df2

def mapping_headers(df, map_header={}, **kwargs):
    '''    Mapping headers according to pre-defined dictionary    '''
    # make a list of headers that are mapped and not mapped
    mapped_headers_before = list(set(map_header.keys()) & set(df.columns))
    mapped_headers_after = list(map(map_header.get, mapped_headers_before))
    unmapped_headers = list(set(df.columns) - set(mapped_headers_before))
    # rename columns in df
    df.rename(columns=map_header, inplace=True)
    # write log
    logger.info('Mapping headers now...')
    logger.info('The following headers have been mapped from {0} to {1}'.\
                format(mapped_headers_before, mapped_headers_after))
    logger.info('The following headers have been kept as they are {0}'.format(unmapped_headers))    
    return df

def mapping_featurenames(df, map_features={}, **kwargs):
    """    Mapping feature names according to pre-defined dictionary    """
    # make a list of features that are mapped 
    features_before = list(set(map_features.keys()) & set(df['Feature'])) 
    features_after = list(map(map_features.get, features_before))
    unmapped_features = list(set(df['Feature']) - set(features_before))
    # rename features in df    
    df['Feature'].replace(map_features, inplace=True)
    try: 
        df['SampleID']
    except:
        raise Exception('SampleID is missing. Must define it.')
    # write log    
    logger.info('Mapping features now...')
    logger.info('The following features have been mapped from {0} to {1}'.\
                format(features_before, features_after))
    logger.info('The following headers have been kept as they are {0}'.format(unmapped_features))
    return df

def mapping_units(df, map_units={}, **kwargs):
    """    Mapping unit names according to pre-defined dictionary    """
    # make a list of units that are mapped 
    units_before = list(set(map_units.keys()) & set(df['Unit'])) 
    units_after = list(map(map_units.get, units_before))
    unmapped_units = list(set(df['Unit']) - set(units_before))
    # rename units in df    
    df['Unit'].replace(map_units, inplace=True)
    # write log    
    logger.info('Mapping units now...')
    # logger.info('The following units have been mapped from {0} to {1}'.\
    #             format(units_before, units_after)) 
    logger.info('The following headers have been kept as they are {0}'.format(unmapped_units))   
    return df

def deal_with_mol_in_unit(df, DATAMODEL_HGC, unit_conversion={}, user_defined_feature_units={}, **kwargs):
    '''
    To deal with units that contain mol or umol
    This step is done before converting units to standard HGC units
    '''
    # record old unit for mols
    df['Unit_old_mol'] = df['Unit']    
    # spilt units and store in a df
    unit0 = df['Unit'].where(pd.notnull(df['Unit']), None)
    unit0 = unit0.replace([r''],[None])
    unit0_split = _list_to_array([re.split('/| ', str(unit)) for unit in unit0])
    unit0_split = pd.DataFrame(unit0_split, columns=['Col0', 'Col1','Col2'])
    # create a empty column for storing ration_mol
    ratio_mol=[None]*len(unit0)
    # get default dictionary
    unit_default = {**DATAMODEL_HGC['HGC_default_feature_units'], **user_defined_feature_units}
    # replace mmol by mg and get ratio for conversion
    for i in range(len(unit0)):
        if df['Feature'][i] in unit_default.keys() and 'mol' in unit0_split.iloc[i,0]:
            ratio_mol[i] = Formula(df['Feature'][i]).mass # has to use a loop as Formula does not support vector operation with nan
            unit0_split.iloc[i,2] = df['Feature'][i]
            unit0_split.iloc[i,0] = unit0_split.iloc[i,0].replace('mol', 'g')
    # put units back from split
    unit1_0 = unit0_split.Col0
    unit1_1 = pd.Series(['/' + str(str_unit) for str_unit in unit0_split.Col1]).replace([r'/None'],'')
    unit1_2 = ' '+ unit0_split.Col2.fillna('')
    unit1 = unit1_0 + unit1_1 + unit1_2
    unit1 = unit1.replace([r'None/ '],[None])
    # get a ratio
    df['ratio_mol'] = ratio_mol
    # write new unit for mols
    df['Unit'] = unit1    
    # write log
    logger.info('"mol" has been mapped to "g"')
    return df  

def convert_units_get_ratio(df, DATAMODEL_HGC, unit_conversion={}, user_defined_feature_units={}, **kwargs):
    """
    Covnert units to stardard ones defined by HGC and compute conversion ratio.
    If not recognisable, keep them as they are.
    Before conversion, the name of the feature, if any, has to be extracted from the unit.
    e.g. mg/L N --> mg/L (*molmass(NH4)/molmass(N))
        μg/l --> 1e-3 mg/L, ...
    To implement unit conversion,
    two external modules are called:    
        unit_converter, which is used for conversion
        molemass, which is used to compute mol weigh   
    """    
    # save old units
    df['Unit_old_unit'] = df['Unit']
    # combine two dictionaries from users and hgc default. Users' format has HIGHER priority. 
    unit_default = {**DATAMODEL_HGC['HGC_default_feature_units'], **user_defined_feature_units}
    # get unit from data, nan labeled as none, to be identical to unit1
    unit0 = df['Unit'].where(pd.notnull(df['Unit']), None)
    # get desired formats of units from user's definition or ghc's default
    unit1 = pd.Series(list(map(unit_default.get, df['Feature']))).replace('', np.nan)
    # Note: if a unit is not defined by user or hgc, use the unit from the data
    unit1 = unit1.fillna(unit0)
    unit1_output = unit1 #_list_to_array([re.split(' ', str(unit)) for unit in unit0])[:,0]
    # unit1 = unit1.where(pd.notnull(unit1), None)
    # split the column units into three parts based on / and space. Currently, the symbol_list must have two elements: / and space
    unit0_split = _list_to_array([re.split('/| ', str(unit)) for unit in unit0])
    unit0_split = pd.DataFrame(unit0_split, columns=['Col0', 'Col1','Col2'])
    unit0_split.Col2.replace('', np.nan, inplace=True) # fill the nan by feature names    
    unit0_split.Col2.fillna(df['Feature'], inplace=True) # fill the nan by feature names    
    unit1_split = _list_to_array([re.split('/| ', str(unit)) for unit in unit1])
    unit1_split = np.column_stack((unit1_split[:,0:2], df['Feature'].values))
    unit1_split = pd.DataFrame(unit1_split, columns=['Col0', 'Col1','Col2'])
    unit1_split.Col2.fillna(df['Feature'], inplace=True) # fill the nan by feature names    
    # get conversion ratio for units
    ratio_col0 = _compute_convert_ratio(list(unit0_split.iloc[:,0]), list(unit1_split.iloc[:,0]), unit_conversion)    
    ratio_col1 = _compute_convert_ratio(list(unit1_split.iloc[:,1]), list(unit0_split.iloc[:,1]), unit_conversion)
    # compute molar mass for both units, have to write a loop to reach each 
    MolarMass0 = list()
    MolarMass1 = list()
    for i in range(len(unit0_split)):
        try:
            MolarMass0.append(Formula(unit0_split.iloc[i,2]).mass)
        except:
            MolarMass0.append(1) # make it as 1 if the feature name is not recognisable
    for i in range(len(unit1_split)):
        try:
            MolarMass1.append(Formula(unit1_split.iloc[i,2]).mass)            
        except:
            MolarMass1.append(1) # make it as 1 if the feature name is not recognisable
    ratio_col2 = pd.Series(MolarMass1)/pd.Series(MolarMass0) 
    # multiple ratios
    ratio = ratio_col0*ratio_col1*ratio_col2*df['ratio_mol'].fillna(1)
    ratio = ratio.fillna(1)
    # save old and write new columns
    df['ratio_unit'] = ratio_col0*ratio_col1*ratio_col2
    df['ratio'] = ratio
    df['Unit'] = unit1_output
    # write log
    logger.info('Units have been converted to stardard ones if the corresponding features are defined in default dict')
    return df

# def _get_symbol_from_string(list0, symbol):
#     '''
#     a function defined to count the frequence of symbols from a list
#     '''
#     if isinstance(list0, int) or isinstance(list0, float):
#         list0 = [list0] # make it as a list
#     symb_count = np.empty([len(list0),len(symbol)]) # make a empty matrix
    
#     for j in range(len(symbol)):    
#         for i in range(len(list0)):
#             symb_count[i, j] = str(list0[i]).count(symbol[j]) # count number of symbols
#     return symb_count

# def _flatten(seq):
#     '''
#     to get elements from a list of lists
#     '''
#     l = []
#     for elt in seq:
#         t = type(elt)
#         if t is tuple or t is list:
#             for elt2 in _flatten(elt):
#                 l.append(elt2)
#         else:
#             l.append(elt)
#     return l

def _get_number_from_string(string):
    '''   function to get numbers from string    '''
    number0 = float(''.join([x for x in string if x.isdigit() or x == '.']))
    return number0

def split_strings_from_value(df):
    ''' 
    to spilt strings if they contain "<", ">", "-": put string symbol in separate column
    <100 --> "<" in temporary column, "100" remain in value column
    '''  
    df['Value_old_split'] = df['Value']
    df['Value_str'] = ""
    df['Value_sign'] = ""
    df['Value_num'] = ""    
    # define a list of signs
    symb_list = ['<','>','-']  
    # find number out
    for i in range(len(df)):
        df.loc[i, 'Value_str'] = str(df['Value'][i])
        try: # get number out of a string. if there is no numbers, skip
            df.loc[i, 'Value_num'] = re.findall(r'\d+(?:\.\d+)?', df.loc[i, 'Value_str'])[0] # get string for deleting 
            df.loc[i, 'Value_sign']  = df.loc[i, 'Value_str'].replace(df['Value_num'][i], '').replace('.', '') # delete number from string            
            df.loc[i, 'Value_num'] = _get_number_from_string(df.loc[i, 'Value_str']) # get real number -.3 --> - and 0.3
        except:
            pass
    df['Value'] = df['Value_num']
    df.drop(columns=['Value_num','Value_str'], inplace=True)
    # write log
    logger.info('Cleaned the columns that has invalid values')         
    return df

def _convert_format(series0, format0):
    if format0 == 'string':
        series1 = [str(i) for i in series0]
    elif format0 == 'float64':
        series1 = pd.to_numeric(series0)
    elif format0 == 'date':
        series1 = pd.to_datetime(series0)
    else:
        raise Exception('Format is not recognisable. Must be string, float64, or datetime')
    return series1

def adjust_formats(df, DEFAULT_FORMAT={}, user_defined_format_colums={}, **kwargs):
    '''
    convert to datetime, numeric, string
    first check if format for a Column is defined by user
    if not, check if column format is in HGC.IO.defaults
    else: ignore. log that format not defined
    '''
    # combine two dictionaries defined for formats, users' definition has higher priority
    format_default = {**DEFAULT_FORMAT, **user_defined_format_colums}
    # the following five features must be included in the dataframe
    df['Value'] = _convert_format(df['Value'], format_default['Value'])
    df['Feature'] = _convert_format(df['Feature'], format_default['Feature'])
    df['Unit'] = _convert_format(df['Unit'], format_default['Unit'])
    df['SampleID'] = _convert_format(df['SampleID'], format_default['SampleID'])
    df['Date'] = _convert_format(df['Date'], format_default['Date'])
    # the following three are optional
    if 'LocationID' in df.columns:
        df['LocationID'] = _convert_format(df['LocationID'], format_default['LocationID'])
    if 'X' in df.columns:
        df['X'] = _convert_format(df['X'], format_default['X'])
    if 'Y' in df.columns:
        df['Y'] = _convert_format(df['Y'], format_default['Y'])
    # write log
    logger.info('Formats have been adjusted')
    return df

def multiple_ratio(df, DATAMODEL_HGC, user_defined_feature_units={}, **kwargs):
    """    multiple values by the conversion rate, but only for the features whose units have been defined by users or HGC    """
    unit_default = {**DATAMODEL_HGC['HGC_default_feature_units'], **user_defined_feature_units}
    # get index where features' units have been defined
    df['Whether_defined'] = False
    idx = [idx for (idx, feature) in enumerate(df['Feature']) if feature in unit_default]  
    # df['Whether_defined'] = df['Feature'].apply(lambda x : True if x in unit_default else False)
    df.loc[idx, 'Whether_defined'] = True  
    # for i in range(len(df['Feature'])):
    #     if df['Feature'][i] in user_defined_feature_units:
    #         df.loc[i,'Whether_defined'] = True
    # idx = df['Whether_defined'] == True
    df.loc[idx,'Value'] = df.loc[idx,'Value'].fillna(value=np.nan)*df.loc[idx,'ratio'].fillna(value=1) # df.dtypes         
    # write log
    logger.info('Values, whose units have been defined, have been multipled by the correpsonding ratio')
    return df        

def join_string_to_value(df):
    """
    putting numbers and signs together now
    e.g. join < symbol with Value (eg "<" + "100" = "<100")
    """
    df['Value_new']=""
    df.Value.fillna(value=np.nan, inplace=True)
    for i in range(len(df['Value_sign'])):
        if math.isnan(df['Value'][i]) == False:
            df.loc[i,'Value_new'] = df['Value_sign'][i]+str(df['Value'][i]) 
        else:
            df.loc[i,'Value_new'] = df['Value'][i]
    # rename 
    df.rename(columns={'Value_new':'Value','Value':'Value_old_join'}, inplace=True)
    # write log
    logger.info('Symbols and values have been joined into the column named "Value"')
    return df

def _compute_convert_ratio(unit_in, unit_out, unit_conversion):
    """     compute conversion ratio based on unit_in and unit_out    """
    if not isinstance(unit_in,list):      
        conversion_ratio = unit_conversion[unit_in]/unit_conversion[unit_out]
    elif isinstance(unit_in,list): 
        unit_in_dict = pd.Series(map(unit_conversion.get, unit_in))
        unit_out_dict = pd.Series(map(unit_conversion.get, unit_out))
        conversion_ratio = unit_in_dict/unit_out_dict        
    else:
        info.error('Cannot compute ratio between input unit and output unit')
    return conversion_ratio

def _list_to_array(list_of_list):
    """    Turn a list of lists to an 2D array    """
    length = max(map(len, list_of_list))
    array0 = np.array([xi+[None]*(length-len(xi)) for xi in list_of_list])
    return array0

def drop_nan_rows(df):  
    """    drop nan rows from , whose have no values    """
    df.dropna(subset = ['Value'], inplace=True)
    # df.dropna(subset = ['Unit'], inplace=True)
    logger.info('Dropped rows that has nan as values')
    return df 

def delete_duplicate_rows(df):
    """    drop duplicate rows from df    """
    df.drop_duplicates(subset = ['Feature', 'SampleID'], inplace = True, keep = 'first')
    logger.info('Dropped duplicate rows that have the same feature name and sampleid')
    return df

def rename_column(df):
    """ 
    renaming columns for debugging
    Unit_old0 : units after mapping to the HGC/user-defined ones
    Unit_old1 : units converted from mmol to mg
    Value_old0 : values before spilting
    Value_old1 : values to be joined with signs, which have been multipled by ratios
    Value_old2 : signs contained in the values
    ratio0 : ratio used for converting mmol to mg
    ratio1 : ration used for converting among different units    
    """
    df.rename(columns={'Unit_old_mol' : 'Unit_old0',
                       'Unit_old_unit' : 'Unit_old1',
                       'Value_old_split' : 'Value_old0', 
                       'Value_old_join' : 'Value_old1',
                       'Value_sign' : 'Value_old2',
                       'ratio_mol' : 'ratio0',
                       'ratio_unit' : 'ratio1',                    
                       }, inplace=True)
    # write log
    logger.info('Renamed columns of df for clarification')    
    return df

#%% main function to run all functions
def import_file(file_path='', sheet_name='', shape='wide', slice_sample=[], slice_unit=[], slice_feature=[], slice_data=[], 
                map_header={}, map_features={}, map_units={}, unit_conversion={}, user_defined_feature_units={}, 
                user_defined_format_colums={}, **kwargs):
    """   
    Parameters
    ----------
    file_path : string,
        the path of the file to read. The default is ''.
    sheet_name : string,
        the name of the sheet to read. The default is ''.
    shape : string, 
        either wide or stacked. The default is 'wide'.
    slice_sample : list,
        the slice to get headers. The default is [].
    slice_feature : list, 
        the slice to get feature names
    slice_unit : list,
        the slice to get unit.
    slice_data : list, 
        the slice to get data(observation). 
    map_header : dict, 
        to map headers.
    map_features : dict, 
        to map feature names.
    map_units : dict, optional
        to map units. 
    unit_conversion : dict, optional
        to convert units. 
    user_defined_feature_units : dict, 
        with defined units corresponding to features. 
    user_defined_format_colums : dict, optional
        with defined formats corresponding to column names.
        
    Returns
    -------
    df : dataframe
    """
    # add a log file
    global logger
    logger = logging.getLogger('.//import_file.log')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('import_file.log')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("The program starts...")
    # the next steps depend on whether the format is wide or stacked
    # read the wide/stacked format into a dataframe

    # rebuild user_config
    user_config = {
    'file_path' : file_path,
    'sheet_name' : sheet_name,
    'shape' : shape, 
    'slice_sample' : slice_sample,
    'slice_feature' : slice_feature, 
    'slice_unit' : slice_unit,
    'slice_data' : slice_data, 
    'map_header' : map_header, 
    'map_features' : map_features, 
    'map_units' : map_units,
    'unit_conversion' : unit_conversion,
    'user_defined_feature_units' : user_defined_feature_units, 
    'user_defined_format_colums' : user_defined_format_colums,
    }
    if user_config['shape'] == 'wide':
        # execute functions that are only necessary for wide file
        df_wide = read_file(**user_config)
        df_wide, user_config['header_sample'], user_config['header_feature'], user_config['header_unit'] = get_headers_wide(df_wide, **user_config)
        df_wide = slice_rows_with_data(df_wide, **user_config)
        df_wide = rename_headers_wide(df_wide, **user_config)
        df_wide = melt_wide_to_stacked(df_wide, **user_config)
        df = df_wide.reset_index()
        df.drop(columns = 'index', inplace=True)
        logger.info('A wide-format dataframe has been generated and converted to stacked-format')
    elif user_config['shape'] == 'stacked':
        # execute functions that are only necessary for stacked file
        df_stacked = read_file(**user_config)
        df_stacked, user_config['header_sample'] = get_headers_stacked(df_stacked, **user_config)
        df_stacked = slice_rows_with_data(df_stacked, **user_config)
        df_stacked = rename_headers_stacked(df_stacked, **user_config)
        df = df_stacked.reset_index()
        df.drop(columns = 'index', inplace=True)
        logger.info('A stacked-format dataframe has been generated')
    else:
        df = []
        logger.info('Error in generating a dataframe from wide/stacked fortmat data')   
      
    # map sample hearders which are defined in user_config
    df = mapping_headers(df, **user_config)    
    # map features
    df = mapping_featurenames(df, **user_config)    
    #% deal with units from here; keep values
    # map units
    df = mapping_units(df, **user_config)    
    # deal with mol as in unit
    df = deal_with_mol_in_unit(df, DATAMODEL_HGC, **user_config)    
    # convert units
    df = convert_units_get_ratio(df, DATAMODEL_HGC, **user_config)
    #% deal with values from here; keep the remaining part
    # split string containing < or >
    df = split_strings_from_value(df)
    # adjust format for each column based on a user-defined format
    df = adjust_formats(df, DEFAULT_FORMAT, **user_config)
    # multiple ratio (only for features whose units are defined by users/HGC)
    df = multiple_ratio(df, DATAMODEL_HGC, **user_config)
    # join columns of symbols and values
    df = join_string_to_value(df)
    # drop rows with nan values
    df = drop_nan_rows(df)
    # delete duplicate rows
    df = delete_duplicate_rows(df)
    # sort the column names
    df = df.sort_index(axis=1, ascending=True)
    # rename to clarify each column of df
    df = rename_column(df)
    return df