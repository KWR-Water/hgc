# -*- coding: utf-8 -*-
"""
Routine to read water quality data of different formats and transform to HGC format
Xin Tian, Martin van der Schans
KWR, April-July 2020
Edit history: 24-08-2020: by Xin, check unit conversion, 
"""

import copy
import logging
import numpy as np
import pandas as pd
# from unit_converter.converter import convert, converts
import molmass
from pathlib import Path
from hgc import constants # for reading the default csv files
from hgc.constants.constants import mw, units_wt_as

# %% hgc.io.defaults
def default_feature_units():
    """
    Generate a dictionary with the desired prefixes-units (values) for all feature defined in HGC (keys).

    Returns
    -------
    Dictionary

    Example
    -------
    {'Fe': 'mg/L', 'Al': 'µg/L'}

    """
    # load default alias table
    df = pd.read_csv(Path(constants.__file__).parent / 'default_features_alias.csv', encoding='utf-8', header=0)
    mask = ~(df['DefaultUnits'].isnull())
    dct_alias = dict(zip(df['Feature'][mask], df['DefaultUnits'][mask]))
    # extract feature names and get units defined in HGC
    feature = df['Feature']
    DefaultUnits = [units_wt_as(key) for key in feature] # OR use command: list(map(units_wt_as, feature))
    dct_hgc = {k: v for k, v in dict(zip(feature, DefaultUnits)).items() if v is not None}
    # combine dictionaries for default units. If defined in HGC, use it. Otherwise use whatever defined in the alias table. 
    dct = {**dct_alias,
           **dct_hgc, 
           'ph_field': '1', # give pH unit 1 to prevent error --> check in the future release
           'ph_lab': '1',
           'ph': '1',
           }
    return dct


def default_unit_conversion_factor():
    """
    Generate a dictionary of conversion factors for several unit-prefixes.

    Returns
    -------
    Dictionary :
        Conversion factors (values) for several unit-prefixes (keys).

    Example
    -------
    {'g/L': 1., 'mg/L': 0.001, 'μg/L': 1e-6}

    """
    # units, prefix and conversion factors generated by this function
    units = ['1', 'm', 'g', 'L', 'S', 'V', 'mol']
    prefixes = {'p': 1e-12, 'n': 1e-9, 'μ': 1e-6, 'm': 1e-3, 'c': 0.01, 'k': 1000,
                '100m' : 0.1, '50m': 0.05}

    # make a dictionary of all combinations of units/ prefixes (keys) and
    # conversion values (values) {mL: 0.001, L: 1, etc.}
    dct = dict(zip(units, len(units) * [1.]))  # units without prefix get conversion factor "1"
    for unit in units:  # loop through all combinations of units and prefixes
        for key, value in prefixes.items():
           dct[key + unit] = value

    dct = {**dct, '%': .01} # for correction percentage

    return dct

# @Tin, MartinK:
# The following defaults need to be called (and adjusted) by the user.
# For example: header_format = {**default_header_format(), locationID: 'integer'}}.
# Is it necessary to define them as functions e.g. default_na_values()?
# or can they be constants e.g. DEFAULT_NA_VALUES?


def default_column_dtype():
    """
    Generate a dictionary with the default data type of columns.

    Returns
    -------
    Dictionary
        Header or column name (keys) and dtype (values)

    Default
    -------
    {
    'LocationID': 'str',
    'Datetime': 'datetime',
    'SampleID': 'str',
    'Feature': 'str',
    'Unit': 'str',
    'Value': 'float64',
    }

    """
    dct = {
        'LocationID': 'str',
        'Datetime': 'datetime',
        'SampleID': 'str',
        'Feature': 'str',
        'Unit': 'str',
        'Value': 'float64',
    }
    return dct


def default_map_header():
    """
    Generate a dictionary with the mapping of headers in the original file (keys) equal headings in output df (values).

    Returns
    -------
    Dictionary
        Header or column name in original file (keys) and header of output df (values).

    Default
    -------
    {
    'LocationID': 'LocationID',
    'Datetime': 'Datetime',
    'SampleID': 'SampleID',
    'Feature': 'Feature',
    'Unit': 'Unit',
    'Value': 'Value',
    }

    """
    dct = {
        'LocationID': 'LocationID',
        'Datetime': 'Datetime',
        'SampleID': 'SampleID',
        'Feature': 'Feature',
        'Unit': 'Unit',
        'Value': 'Value',
    }
    return dct


def default_na_values():
    """
    Generate list of values that are recognized as NaN.

    The list is based on the default values of python, but with 'NA' left
    out to prevent NA (Sodium) being read as NaN

    Returns
    -------
    List

    """
    lst = ['#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
           '1.#IND', '1.#QNAN', 'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null']
    return lst


# %% HGC.IO utils


def read_file(file_path='', sheet_name=0, na_values=[], encoding='', delimiter=None, **kwargs):
    """Read excel of csv file."""
    file_extension = file_path.split('.')[-1]
    if (file_extension == 'xlsx') or (file_extension == 'xls'):
        try:
            df = pd.read_excel(file_path,
                               sheet_name=sheet_name,
                               header=None,
                               index_col=None,
                               na_values=na_values,
                               keep_default_na=False,
                               encoding=encoding)
            # logger.info('file read: ' + file_path)
        except:
            df = pd.DataFrame()
            # logger.error('WARNING file not read: ' + file_path)
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
            # logger.info('file read: ' + file_path)
        except:
            df = pd.DataFrame()
            # logger.error('WARNING file not read: ' + file_path)
    else:
        df = pd.DataFrame()
        # logger.error('WARNING file extension not recognized: ' + file_path)
    return df


def _get_slice(df, arrays):
    """Get row values by slicing."""
    if df.empty:
        raise ValueError('df cannot be empty')

    if isinstance(arrays[0], list):  # check if the array is nested
        series = pd.Series([], dtype='object')
        for array in arrays:
            series = series.append(df.iloc[array[0], array[1]].rename(0))
    elif len(arrays) == 1:  # only row specified
        series = df.iloc[arrays[0]]
    else:  # row and column specified
        series = df.iloc[arrays[0], arrays[1]]
    return series


def get_headers_wide(df, slice_header='', slice_feature='', slice_unit='', **kwargs):
    """Get column headers for a wide-format dataframe."""
    # create series with headers
    header_sample = _get_slice(df, slice_header).astype(str)  # !!!!!!!!!!!!!!! SERIES STRING
    header_feature = _get_slice(df, slice_feature).astype(str)
    header_unit = _get_slice(df, slice_unit).astype(str)
    # get headers at 2 levels
    ncols = len(df.columns)
    level0 = pd.Series(ncols * [''])
    level0[header_sample.index] = header_sample
    level0[header_feature.index] = header_feature
    level1 = pd.Series(ncols * [''])
    level1[header_unit.index] = header_unit
    # add series by multi-index headers
    df.columns = pd.MultiIndex.from_arrays([level0, level1])
    return df, header_sample, header_feature, header_unit


def get_headers_stacked(df, slice_header='', **kwargs):
    """Get column headers for a stacked-format dataframe."""
    # create series with headers
    header_sample = _get_slice(df, slice_header)
    # add column names
    ncols = len(df.columns)
    level0 = pd.Series(ncols * [''])
    level0[header_sample.index] = header_sample
    df.columns = level0
    return df, header_sample


def slice_rows_with_data(df, slice_data=None, **kwargs):
    """Get data based on pre-defined slicing blocks."""
    if isinstance(slice_data[0], list):  # check if the array is nested
        df2 = pd.DataFrame([])
        for array in slice_data:
            df2 = pd.concat([df2, df.iloc[array[0]]], axis=0)
    elif len(slice_data) == 1:  # only row specified
        df2 = df.iloc[slice_data[0]]
    return df2


def rename_headers_wide(df, map_header={}, **kwargs):
    """Rename columns by pre-defined names for wide format."""
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
    # logger.info('Headers from the wide-format dataframe have been retrieved')
    return df


def rename_headers_stacked(df, map_header={}, **kwargs):
    """Rename columns by pre-defined names for stacked format."""
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
    # logger.info('Headers from the stacked-format dataframe have been retrieved')
    return df


def _map_header_2_multilevel(map_header):
    """Convert dictionary with mapping of columns to multiindex."""
    map_header2 = {}
    for key, value in map_header.items():
        map_header2[(key, '')] = (value, '')
    return map_header2


def melt_wide_to_stacked(df, map_header={}, **kwargs):
    """Turn wide format to stacked format."""
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
    # logger.info('Turned wide format to stacked format')
    return df2


def mapping_headers(df, map_header={}, **kwargs):
    """Map headers according to pre-defined dictionary."""
    # to do:
    # add to previous step generate sampleid if not defined based on location +
    # datetime (stacked) or rownr (wide)

    # to do:
    # make a list of headers that overlap after mapping
    # e.g. identical keys, or keys that map existing unmapped headers

    # make a list of headers that are mapped and not mapped
    mapped_headers_before = list(set(map_header.keys()) & set(df.columns))
    mapped_headers_after = list(map(map_header.get, mapped_headers_before))
    unmapped_headers = list(set(df.columns) - set(mapped_headers_before))
    # rename columns in df
    df.rename(columns=map_header, inplace=True)
    # write log
    # logger.info('Mapping headers now...')
    # logger.info('The following headers have been mapped from {0} to {1}'.\
    #             format(mapped_headers_before, mapped_headers_after))
    # logger.info('The following headers have been kept as they are {0}'.format(unmapped_headers))
    # check if the file contains the esstial columns
    for col in ['SampleID', 'Feature', 'Value']:
        try:
            df[col]
        except:
            raise Exception('ERROR. column missing :' + col)
    return df


def mapping_features(df, map_features={}, **kwargs):
    """Map feature names according to pre-defined dictionary."""
    # make a list of features that are mapped
    features_before = list(set(map_features.keys()) & set(df['Feature']))
    features_after = list(map(map_features.get, features_before))
    unmapped_features = list(set(df['Feature']) - set(features_before))
    # rename features in df
    df['Feature_orig'] = df['Feature']
    df['Feature'] = df['Feature'].replace(map_features)

    # write log
    # logger.info('Mapping features now...')
    # logger.info('The following features have been mapped from {0} to {1}'.\
    #             format(features_before, features_after))
    # logger.info('The following features have been kept as they are {0}'.format(unmapped_features))
    return df


def mapping_original_units(df, map_units={}, **kwargs):
    """Map original units according to pre-defined dictionary."""
    # make a list of units that are mapped
    units_before = list(set(map_units.keys()) & set(df['Unit']))
    units_after = list(map(map_units.get, units_before))
    unmapped_units = list(set(df['Unit']) - set(units_before))
    # rename original units to units recognized by hgc
    df['Unit_orig'] = df['Unit']
    df['Unit_orig0'] = df['Unit_orig'].map(map_units).fillna(df['Unit_orig'])
    # write log
    # logger.info('Mapping units now...')
    # ## logger.info('The following units have been mapped from {0} to {1}'.\
    # ##             format(units_before, units_after))
    # logger.info('The following headers have been kept as they are {0}'.format(unmapped_units))
    return df


def mapping_new_units(df, feature_units={}, **kwargs):
    """Map new units (used by hgc) according to a pre-defined dictionary."""
    df['Unit'] = df['Feature'].map(feature_units).fillna(df['Unit'])
    # to do: add logging which features were not mapped to new units !!!!!!!!!!!!!!!!!!!!!!
    return df


def unit_conversion_ratio(df, unit_conversion_factor={}, feature_units={}, **kwargs):
    """Compute conversion factor between original units and new units (used by hgc)."""
    # generate a temporary dataframe to compute ratios
    df2 = df[[]]

    # split units into inidivual symbols (incl. prefix) and fill NaN
    df2[['orig1', 'orig2', 'orig3']] = df['Unit_orig0'].fillna('').str.split(r"/| ", expand=True, n=2).reindex(columns=range(3))
    df2[['new1', 'new2', 'new3']] = df['Unit'].fillna('').str.split(r"/| ", expand=True, n=2).reindex(columns=range(3))
    df2['unit_conversion_correct'] = True

    for orig, new in {'orig1': 'new1', 'orig2': 'new2'}.items():
        # force column to string (for example 1/m --> '1', 'm')
        df2[orig] = df2[orig].fillna('').astype(str)
        df2[new] = df2[new].fillna('').astype(str)

        # replace non-dimensional units by "1"
        df2[orig] = df2[orig].replace(['n', '-', '', ' '], '1').astype(str)
        df2[new] = df2[new].replace(['n', '-', '', ' '], '1').astype(str)

        # find where to correct for "mol"
        maska = df2[orig].str.contains("mol")
        maskb = df2[new].str.contains("mol")
        mask = maska | maskb

        # compute ratio mol --> gram
        features = df['Feature'][mask].unique()
        map_molwt = {}
        for feature in features:
            try:
                map_molwt[feature] = molmass.Formula(feature).mass
            except:  # in case feature is not a chemical formula
                map_molwt[feature] = np.nan

        df2[orig + 'ratio'] = np.where(maska, df['Feature'].map(map_molwt), 1.)
        df2[new + 'ratio'] = np.where(maskb, df['Feature'].map(map_molwt), 1.)

        # log errors
        df2.loc[df2[orig + 'ratio'].isnull(), 'unit_conversion_correct'] = False
        df2.loc[df2[new + 'ratio'].isnull(), 'unit_conversion_correct'] = False

        # replace mol by gram (to prevent error in next step) and remove N, P, S
        df2[orig] = df2[orig].str.replace('mol', 'g')
        df2[new] = df2[new].str.replace('mol', 'g')
        df2['orig3'][maska] = ''
        df2['new3'][maskb] = ''

        # compute unit conversion ratio
        df2[orig + 'ratio'] = df2[orig + 'ratio'] * df2[orig].map(unit_conversion_factor)
        df2[new + 'ratio'] = df2[new + 'ratio'] * df2[new].map(unit_conversion_factor)

        # log errors. If orig and new both np.nan --> replace ratio's by 1
        df2.loc[df2[orig + 'ratio'].isnull() | df2[new + 'ratio'].isnull(), 'unit_conversion_correct'] = False
        df2.loc[(df2[orig] == '') & (df2[new] == ''), [orig + 'ratio', new + 'ratio']] = 1.

        # there is no error if the units are on purpose empty (eg ph)
        df2.loc[(df['Unit'] == '1') & (df['Unit_orig0'] == '1'), 'unit_conversion_correct'] = True

    # force column to string
    df2['orig3'] = df2['orig3'].fillna('').astype(str)
    df2['new3'] = df2['new3'].fillna('').astype(str)

    # find where to compute N, P, S, correction factor (for example mg/L N --> mg/L)
    mask3a = df2['orig3'] != ''
    mask3b = df2['new3'] != ''
    mask3 = mask3a | mask3b

    df2.loc[mask3 & ~mask3a, 'orig3'] = df['Feature']
    df2.loc[mask3 & ~mask3b, 'new3'] = df['Feature']

    # compute weight of atoms/ features
    atoms = pd.unique(df2[['orig3', 'new3']][mask3].values.ravel())
    map_molwt3 = {}
    for atom in atoms:
        if atom == 'PO4_ortho':
            atom = 'PO4'
        try:
            map_molwt3[atom] = molmass.Formula(atom).mass
        except:  # in case atom is not a chemical formula
            map_molwt3[atom]  = np.nan

    df2['orig3ratio'] = np.where(mask3, df2['orig3'].map(map_molwt3), 1.)
    df2['new3ratio'] = np.where(mask3, df2['new3'].map(map_molwt3), 1.)

    # log errors
    df2.loc[df2['orig3ratio'].isnull(), 'unit_conversion_correct'] = False
    df2.loc[df2['new3ratio'].isnull(), 'unit_conversion_correct'] = False

    # Compute ratio, set ratio to 1 if original and desired unit are equal
    df['Ratio'] = ((df2['orig1ratio'] / df2['new1ratio']) * (df2['new2ratio'] / df2['orig2ratio']) * (df2['new3ratio'] / df2['orig3ratio']))
    df['Ratio'] = np.where((df['Unit_orig'] == df['Unit']) | (df['Unit_orig0'] == df['Unit']), 1., df['Ratio'])

    return df


# # for testing
# import numpy as np
# import pandas as pd
# df = pd.DataFrame({'Feature': ['NO3', 'NO3', 'NO3', 'NO3', 'NO3', 'NO3', 'NO3', np.nan],
#                   'Unit_orig0': ['mg/L', 'ng/L', 'ng/L N', 'ng/L N', 'mg/L', 'mol/L', 'x', np.nan],
#                   'Unit': ['mg/L', 'mg/L', 'mg/L', 'mg/L N', 'ng/L N',  'ng/L N','' , np.nan],
#                     'Value': [45, '45', '<34', '<<34', -34, '--35', '', np.nan]})


def split_detectionlimit_from_value(df):
    """
    Split strings ("<", ">") from values. Split ("-") only if Unit is a concentration.

    Put string symbol and value in separate columns.
    Only works if string is at the left most position.
    For example: "<100" --> "<" in temporary column, "100" remain in value column.
    minus symbol ("-") is only split is the Unit column contain "g/L".

    Parameters
    ----------
    df: dataframe
        df must contain a column 'Value' and 'Unit'

    """
    df['Value_orig'] = df['Value']
    df['Value'] = df['Value'].astype('str', errors='ignore')

    # select rows that start with < or >
    symb_list = ['<', '>', '-']
    left_symbol = df['Value'].str[0]
    mask = left_symbol.isin(list(set(symb_list) - set(['-'])))
    df['Value_sign'] = np.where(mask, left_symbol, np.nan)
    df['Value_num'] = np.where(mask, df['Value'].str[1:], df['Value'])

    # select rows that start with '-' and contain concentrations data (other data is allowed <0)
    mask2 = (pd.to_numeric(df['Value'], errors='coerce') < 0) & (df['Unit'].str.contains('g/L'))
    df['Value_sign'] = np.where(mask2, '-', df['Value_sign'])
    df['Value_num'] = np.where(mask2, -pd.to_numeric(df['Value'], errors='coerce'), df['Value_num'])

    return df


def _convert_dtype(series, dtype='', dayfirst=None):
    if dtype == 'datetime':
        series1 = pd.to_datetime(series, dayfirst=dayfirst, errors='coerce')
    elif dtype == 'float64':
        series1 = pd.to_numeric(series, errors='coerce')
    elif dtype == 'float':
        series1 = pd.to_numeric(series, downcast='float', errors='coerce')
    elif dtype in ['int', 'str']:
        series1 = series.astype(dtype, errors='ignore')
    else:
        raise Exception('ERROR: dtype format not recognized :' + str(dtype))
    return series1


def adjust_dtype(df, column_dtype={}, dayfirst=None, **kwargs):
    """Convert column to userdefined datatype.

    Parameters
    ----------
    df : dataframe
    column_dtype : dictionary
        Mapping between column name (keys) and datatype (values).
        supported dtypes (values) are: 'str', 'float', 'float64', 'datetime', 'int'
    dayfirst : string
        Use dayfirst when converting dates (see pd.datetime documentation)

    """
    # # check if the compulsary formats are correctly defined
    # if column_dtype['Feature'] == 'str':
    #     print('ERROR dtype "Feature" incorretly defined')
    # if column_dtype['Unit'] == 'str':
    #     print('ERROR dtype "Unit" incorretly defined')
    # if column_dtype['Value'] not in ['float64', 'float']:
    #     print('ERROR dtype "Value" incorretly defined')

    # assign dtype for column "Value" to "Value_num".
    column_dtype = {**column_dtype, 'Value_num': column_dtype['Value']}
    column_dtype.pop('Value', None)

    # adjust formats
    for col in df.columns:
        if col in column_dtype.keys():
            df[col] = _convert_dtype(df[col], dtype=column_dtype[col], dayfirst=dayfirst)

    # write log
    # logger.info('Formats have been adjusted')
    return df


def unit_conversion_value(df, **kwargs):
    """Multiply value by conversion ratio."""
    df['Value_num'] = df['Value_num'] * df['Ratio']
    return df


def drop_nan_value_rows(df):
    """Drop rows with NaN Value."""
    # df.dropna(subset=['Value_num'], inplace=True)  # short version
    mask = df['Value_num'].isnull()  # also drop if no unit ??
    df_dropna = df[mask]
    df = df[~mask]
    # logger.info('Dropped rows that has nan as values')
    return df, df_dropna


def join_detectionlimit_to_value(df, **kwargs):
    """Put sign and numeric value together. For example: "<" + "100" = "<100")."""
    df['Value'] = np.where(df['Value_sign'].isnull(), df['Value_num'], df['Value_sign'] + df['Value_num'].astype(str))
    return df


def delete_duplicate_rows(df):
    """Drop rows that have identical Feature and SampleID."""
    df_keep = df.drop_duplicates(subset=['Feature', 'SampleID'], keep='first')
    df_dropduplicate = df[~df.index.isin(df_keep.index)]
    # logger.info('Dropped duplicate rows that have the same feature name and sampleid')
    return df_keep, df_dropduplicate


#%% main function to run all functions
def import_file(dataframe=None, file_path='', sheet_name=0, shape='stacked',
                slice_header=[], slice_unit=[], slice_feature=[], slice_data=[],
                map_header=default_map_header(),
                map_features={},
                map_units={},
                unit_conversion_factor=default_unit_conversion_factor(),
                feature_units=default_feature_units(),
                column_dtype=default_column_dtype(),
                na_values=default_na_values(), encoding='ISO-8859-1',
                dayfirst=True, **kwargs):
    """
    Import water quality data and transform it to HGC format.
    
    The original file can contain (1) stacked shaped data, (2) wide shaped data, or (3) dataframe.

    Parameters
    ----------
    dataframe : dataframe (optional)
        Dataframe containing the data to be transformed to HGC.
        The headers should be inside the data (and NOT defined as column label)
        "Dataframe" is optional. If empty, the file referred to by file_path will be read.
    file_path : string (optional)
        The path of the excel or csv-file to read.
        Either "dataframe" or "file_path" should be defined.
    sheet_name : string, integer
        The name (string) or number (integer) of the sheet to read.
        Defaults to 0: 1st sheet as a DataFrame
        Only used when reading excel file.
    shape : {'wide', 'stacked'}, default 'stacked'
        shape of data to read
    slice_header : list/ slice
        slice where to get column headers.
        ==> Also see notes below.
    slice_feature : list/ slice,
        Slice where to get feature names.
        Only used when shape='wide'
        ==> Also see notes below.
    slice_unit : list/ slice,
        slice where to get units.
        Only used when shape='wide'
        ==> See also Notes.
    slice_data : list/ slice,
        slice where to get the data (observations). ==> Also see examples below.
    map_header : dict,
        Mapping of headers in original file (keys) to headers used by HGC (values).
        Default is that the original file contains the headers used by HGC.
    map_features : dict,
        Mapping of original features (keys) to features used by HGC (values).
    map_units : dict, optional
        Mapping of original units (keys) to units recognized by this import script (values).
        ==> Note 1: the values should be defined in SI units and note they are case sensitive.
        The values may contain units that are recognized by the script:
        mol, g, m, h, min, L, V, C, S, Bq, pve, kve, pvd, fte, n
        ==> Note 2: The values may also contain all symbols for conversion factors that are
        defined by the "unit_conversion_factor" argument (see below). e.g. μmol/L.
        ==> Note 3: the following formats can be handled:
        <prefix, optional> <units> e.g. "Bq" or "kBq"
        <prefix, optional> <units> <backslash> <prefix, optional> <units> e.g. "1/m", "mg/nL"
        <prefix, optional> <units> <backslash> <prefix, optional> <units> <whitespace> <atom> e.g. "mg/L N"
        ==> Note 4: The import script can handle "concentrations as"
        (e.g. NO3 mg-N/L, PO4 mg-P/L). They are automatically
        converted to "concentrations" (e.g. (NO3) mg/L) in subsequent steps of this
        import procedure by correcting for the molar weight difference.
        ==> Note 5: "concentrations as" should be mapped to a format with the
        "as" atom behind the units, separated by a whitespace (e.g. NO3 mg/L N,
        PO4 mg/L P). A corresponding dictionary should then be defined as follows for mapping:
        {mg-N/L: mg/L N, mg-P/L: mg/L P} (see also Note 3).
    unit_conversion_factor : dict (optional)
        to convert units of different magnitudes.
        Default is a dictionary of frequently used waterquality units that are
        generated by the function "default_unit_conversion_factor()"
    feature_units : dict (optional)
        Mapping between features (keys) and the corresponding units (units).
        To be used in case the units are not defined in the input file.
        Default is a dictionary based on the units used by HGC and that is
        generated by the function "default_feature_units()".
    column_dtype : dict, optional
        Dictionary defining for each column name (keys) what datatype to use (values).
        supported dtypes: 'datetime', 'float64', 'float', 'int', 'str'.
        Default is generated by the function "default_column_dtype()"
    na_values : list (optional)
        List of values that are recognizes as NaN.
        Default is a custom list geneated by the function "default_na_values()".
        This list does not recognize "NA" as NaN value and thus helps to prevent
        misinterpretation of "NA" as "Sodium" (=Na).
    encoding : string (optional)
        Encoding used when reading csv (see pandas.read_csv for definition)
        Default is 'ISO-8859-1'
    delimiter : string (optional)
        Delimeter used when reading csv (see pandas.read_csv for definition)
        Default is 'None'
    dayfirst : Bool (optional)
        Specify a date parse order for pandas.to_datetime().
        Default is True.

    Notes
    -----
    The slice arguments ("slice_header", "slice_feature", "slice_unit", "slice_data")
    refer to certain rows and/or columns of the imported table.
    Example: "[9, slice(2, 5)]" refers to column 2 to 5 of row 9.
    In this function, slice does not work  with ":" symbol. Instead use "None" for infinitive.
    Example: to select the entire row 9 except the first 2 columns use "[9, slice(2, None)]"

    When features/ units are entered duplicate, the behaviour depends on the data shape:
    - with stacked shaped data, only the first entry is kept.
    - with wide shape data, the feature/ unit that comes first in alphabetic order
    is kept. Note that they are ordered based on the original feature/ unit (i.e. before mapping).


    Returns
    -------
    df : dataframe
    df_dropna : dataframe
    df_dropduplicates : dataframe

    """
    # list of columns generated by the function
    # @Tin: Generate warning if these columns already exist in dataframe ?????????????????
    newcols = ['Feature_orig', 'Unit_orig', 'Unit_orig0', 'Value_orig', 'Value_num', 'Value_sign', 'Ratio']
    # generate a warning if the columns already exist

    # generate a dictionary with all arguments passed in the function
    arguments = copy.deepcopy(locals())

    # generate a log file
    # global logger
    logger = logging.getLogger(r'../import_file.log')
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('import_file.log')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("Start program...")

    # read data
    df_read = pd.DataFrame()
    if isinstance(dataframe, pd.DataFrame):
        df_read = copy.deepcopy(dataframe) # deep copy to prevent changing df
        logger.info('A dataframe has been imported')
    elif isinstance(file_path, str):
    # else:
        df_read = read_file(**arguments)

    # read the wide/stacked format into a dataframe
    if shape == 'wide':
        # execute functions that are only necessary for wide file
        df_wide, arguments['header_sample'], arguments['header_feature'], arguments['header_unit'] = get_headers_wide(df_read, **arguments)
        df_wide = slice_rows_with_data(df_wide, **arguments)
        df_wide = rename_headers_wide(df_wide, **arguments)
        df = melt_wide_to_stacked(df_wide, **arguments)
        logger.info('A wide-format dataframe has been generated and converted to stacked-format')
    elif arguments['shape'] == 'stacked':
        # execute functions that are only necessary for stacked file
        df, arguments['header_sample'] = get_headers_stacked(df_read, **arguments)
        df = slice_rows_with_data(df, **arguments)
        df = rename_headers_stacked(df, **arguments)
        df.reset_index(drop=True, inplace=True)
        logger.info('A stacked-format dataframe has been generated')
    else:
        df = []
        logger.info('datashape wide/stacked not defined')

    # map sample hearders which are defined in arguments
    df = mapping_headers(df, **arguments)
    # map features
    df = mapping_features(df, **arguments)

    # map units
    df = mapping_original_units(df, **arguments)
    df = mapping_new_units(df, **arguments)
    # compute ratio to convert units
    df = unit_conversion_ratio(df, **arguments)

    # values: split string containing < or >
    df = split_detectionlimit_from_value(df)
    # adjust format for each column based on a user-defined format
    df = adjust_dtype(df, **arguments)
    # multiply values by the previously computed unit conversion ratio
    df = unit_conversion_value(df, **arguments)
    # join columns of symbols and values
    df = join_detectionlimit_to_value(df)
    # drop rows with nan values
    df, df_dropna = drop_nan_value_rows(df)
    # delete duplicate rows
    df, df_dropduplicates = delete_duplicate_rows(df)
    # sort the column names
    df.sort_index(axis=1, ascending=True, inplace=True)

    return df, df_dropna, df_dropduplicates


def stack_to_hgc(df, index=['LocationID', 'Datetime', 'SampleID']):
    """
    Pivot stacked dataframe to wide format used by HGC.

    Parameters
    ----------
    df : Dataframe
    index : list
        columns to use as index when pivoting data
        Default = ['LocationID', 'Datetime', 'SampleID']

    Return
    ------
    Dataframe

    """
    df2 = df.pivot_table(index=list(set(df.columns) & set(index)),
                         columns='Feature', values='Value', aggfunc='first')
    return df2
