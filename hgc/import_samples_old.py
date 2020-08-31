# -*- coding: utf-8 -*-
"""
Routine to read stacked/wide format data

Created on Wed Apr 15 14:31:20 2020
"""
import numpy as np
import numpy.matlib
import pandas as pd 
from matplotlib.path import Path
import os
import time
from collections import Counter


def read_stacked_data(df_pre,owner_name,data_start_row,data_start_column,header_row):
    '''function made to read stacked data
    '''
    # get column names
    column_names_long=list(df_pre.columns)
    
    # get nrows and ncoloumns if needed for later use
    nrow=df_pre.count
    ncol=len(column_names_long)
        
    # add a new column with input of owner's name, derived from File name
    if 'OWNER' not in df_pre.columns:
        df_pre['OWNER']=owner_name

    df_data=df_pre    
    # remove redundant string in the column of Unit
    # df_temp=pd.DataFrame(df_pre['UNITS'].str.split(expand=True))
    # df_data=df_pre.assign(Unit=df_temp.loc[:,0])    
    
    return df_data

def clear_column_names(columns_names):
    new_columns_names=columns_names.values  
    for i in range(len(new_columns_names)):
        new_columns_names[i]=str(new_columns_names[i])
        new_columns_names[i]=new_columns_names[i].replace('.','')
        new_columns_names[i]=new_columns_names[i].replace('(','')
        new_columns_names[i]=new_columns_names[i].replace(')','')
        new_columns_names[i]=new_columns_names[i].replace('-','')
        new_columns_names[i]=new_columns_names[i].replace('+','')
        new_columns_names[i]=new_columns_names[i].replace(' ','')
        new_columns_names[i]=new_columns_names[i].replace('_','')
        new_columns_names[i]=new_columns_names[i].replace('*','')
        new_columns_names[i]=new_columns_names[i].replace(',','')
        new_columns_names[i]=new_columns_names[i].replace("'","")
        new_columns_names[i]=new_columns_names[i].replace('/','')
    return new_columns_names

def read_wide_data(df_pre,owner_name,data_start_row,data_start_column,header_row,unit_row):
    '''function made to read wide-format data
    '''
    # get column names
    new_columns_names=list(df_pre.iloc[header_row[0],data_start_column[0]:data_start_column[1]]) \
                        +list(df_pre.iloc[header_row[1],data_start_column[1]:])
    
    # get parameter units
    para_unit=list(df_pre.iloc[unit_row,data_start_column[1]:])

    # divide the table into two parts: headers and main values
    df_pre_main=(df_pre.loc[data_start_row:,:])
    
    # get the part that only has data
    # empty_row_index = df_pre_main_data[df_pre_main_data.isnull().all(1)].index

    # compute nr of rows and columns if necessary 
    nrow=df_pre_main.shape[0]
    ncol=df_pre_main.shape[1]    
 
    # change column names for the first few columns and get first few rows
    # such that turning wide format to long can be based on column names
    column_name_1=pd.Series(new_columns_names[data_start_column[0]:data_start_column[1]]) # get names of first 12 columns
    if column_name_1.isna().sum() >=2:
        raise Exception('More than 2 columns are without header. Please clarify them.')
    column_name_1=column_name_1.fillna('Unknown')
    column_name_1=pd.Series((column_name_1))
    column_name_2=pd.Series(new_columns_names[data_start_column[1]:]) # get names of the remaining columns
    
    if column_name_2.isna().sum() >= 2:
        raise Exception('Too many columns with no columns names. Please add column names')
    else: 
        column_name_2=column_name_2.fillna('Na')
    column_name_2=pd.Series(['Value>>']*len(column_name_2))+column_name_2 # add 'Value' in front of parameter names
    column_name_2=pd.Series(clear_column_names(column_name_2))
    
    # deal with duplicate names
    dups = {}
    for i, val in enumerate(column_name_2):
        if val not in dups:
            # Store index of first occurrence and occurrence value
            dups[val] = [i, 1]
        else:
            # Special case for first occurrence
            if dups[val][1] == 1:
                column_name_2[dups[val][0]] += str(dups[val][1])
            # Increment occurrence value, index value doesn't matter anymore
            dups[val][1] += 1
            # Use stored occurrence value
            column_name_2[i] += str(dups[val][1])
          
    #redefine column names
    new_columns_names=pd.concat([column_name_1,column_name_2],axis=0)
    df_pre_main.columns=new_columns_names

    # df_pre_main = df_pre_main.iloc[0:20,0:]    
    
    # deal with each column seperately to avoid memory error
    tic = time.time()
    df_pre_main_headercol=df_pre_main.iloc[:,data_start_column[0]:data_start_column[1]]
    df_long = pd.DataFrame()
    unit_long=[]
    for i in range(data_start_column[1],ncol):
        df_pre_main_temp = df_pre_main.iloc[:,i]
        column_name = df_pre_main_temp.name
        df_pre_main_temp = pd.concat([df_pre_main_headercol,df_pre_main_temp],axis = 1)
        df_pre_main_temp = df_pre_main_temp.dropna(subset = [column_name], axis = 0)
        if len(df_pre_main_temp) > 0:
            # turn wide format to long format
            df_long_temp=pd.wide_to_long(df_pre_main_temp,stubnames='Value',i=column_name_1.values,j='Component',sep='>>',suffix='\w+')
            unit_long_temp = para_unit[i - data_start_column[1]]
            df_long_temp.loc[:,'UNITS'] = unit_long_temp
            df_long = df_long.append(df_long_temp)
        
        # unit_long_temp = list(np.tile(unit_long_temp,len(df_long)))
        # unit_long = unit_long.append(unit_long_temp)
    toc = time.time()
    print(toc-tic)
    # reset index    
    df_long=df_long.reset_index()   
    
    # add unit 
    # unit_rep=np.tile(para_unit,df_pre_main.shape[0])
    # df_long.loc[:,'UNITS']=unit_rep

    # add two field which are unknown right now
    df_long.loc[:,'OWNER']=owner_name

    return df_long

def remove_nan_reset_index(df_data):
    # remove rows that have nan as values and reset index
    if 'REPORT_VALUE' in df_data.columns:
        df_data=df_data.dropna(subset=['REPORT_VALUE'])
    elif 'VALUE' in df_data.columns:
        df_data=df_data.dropna(subset=['VALUE'])
    else:
        df_data=df_data.dropna(subset=['Value'])

    df_data=df_data.reset_index()
    return df_data
    
def get_detection_limit(df_data):
    # call function to remove nan first
    df_data=remove_nan_reset_index(df_data)
    # get units and values
    # parameter_unit=list(df_data['UNITS'])
    try: 
        parameter_value=list(df_data['REPORT_VALUE'])
        df_data['Val_pro']=df_data['REPORT_VALUE']
    except:
        df_data['REPORT_VALUE']=df_data['Value']
        df_data['Val_pro']=df_data['Value']
        parameter_value=list(df_data['REPORT_VALUE'])
    # parameter_name=list(df_data['COMPONENT'])

    # make all input element as string
    for i in range(len(parameter_value)): 
        parameter_value[i] = str(parameter_value[i]) 

    # index_limit=any('<' in minus for minus in df_long.Value)
    values_with_limit_index=[index for index, string in enumerate(parameter_value) if '<' in string]
    values_with_limit=df_data['REPORT_VALUE'][values_with_limit_index]

    # # remove < for detection limit
    values_with_limit_list=list(values_with_limit)
    values_with_limit_list=[s.replace('<','') for s in values_with_limit_list]
    df_data.loc[values_with_limit_index,'Det_lim']=values_with_limit_list

    values_with_limit_new_value=['< detection limit']
    df_data.loc[values_with_limit_index,'Val_pro']=values_with_limit_new_value
    
    return df_data

def map_column_name(df_data):
    ''' Expected column (header) names: 
    SampleID	Date	LocationID	Owner Component	Detection_limit	Value	Unit
    '''

    column_name=df_data.columns
    name_dict={
        'SAMPLE_ID':'SampleID',
        'name':'SampleID',

        'SAMPLED_DATE':'Date',
        'date':'Date',

        'Location':'LocationID',
        'LOCATION':'LocationID',

        'OWNER':'Owner',

        'COMPONENT':'Component',
        
 	    'Det_lim':'Detection_limit',

         'Val_pro':'Values',

         'UNITS':'Unit',
         'UNIT':'UNIT',
    }

    # renaming
    df_data=df_data.rename(columns=name_dict)
    try:
        df_data_new=df_data[['SampleID','Date','LocationID','Owner','Component','Detection_limit','Values','Unit']]
    except:
        df_data_new=df_data[['SampleID','Date','LocationID','Owner','Component','Detection_limit','Values']]
    
    return df_data_new

def check_format(df_data):

    # check original data types
    # df_data.dtypes
    # df_data['SampleID'] = pd.to_numeric(df_data['SampleID'])
    df_data['Date'] = pd.to_datetime(df_data['Date'])

    return df_data

def remove_duplicate_row(df_data):
    df_data.drop_duplicates(keep = 'first', inplace= True)
    return df_data

def map_parameter_name(parameter_names,file_path_spreedsheet):
    return

def write_log_file(log_file_name,log_msg):
    log_object = open(log_file_name, "a+")
    log_object.write(log_msg)
    # log_object.write("\n")
    log_object.close()

def create_log_file(log_file_name):
    # create a log file; remove it if a log file already exists

    if os.path.exists(log_file_name):
        os.remove(log_file_name)
    file = open(log_file_name, "w") 
    file.close() 

def read_file(file_name,file_format):
    '''
    The main function to read excel/csv from water companies.
    '''

    log_file_name = ".\log_import_samples.txt"
    create_log_file(log_file_name)

    write_log_file(log_file_name, log_msg = 'This a file from ' + file_format.get('owner') + '\n')
    write_log_file(log_file_name, log_msg = 'The program starts......\n')

    # define an empty df
    df_data=None

    # check whether the type of file_format is a dictionary
    try: 
        type(file_format)==dict
    except TypeError:
        ValueError('File_format is not a dict. Define it as a dict')

    # get shape and owner_name
    data_shape=file_format['data_shape']
    owner_name=file_format['owner']
    data_start_row=file_format['data_start_row']
    data_start_column=file_format['data_start_column']
    header_row=file_format['header_row'] 
    unit_row=file_format['unit_row']

    # get extension from file_name 
    filename, file_extension = os.path.splitext(file_name)

    # read data based on their extensions
    write_log_file(log_file_name, log_msg = 'Reading the xls/csv file now......')

    if file_extension=='.csv':
        df_pre=pd.read_csv(file_name,index_col=None,header=None,encoding='latin1')
    elif file_extension=='.xls' or file_extension=='.xlsx':
        df_pre=pd.read_excel(file_name,index_col=None,header=None,encoding='latin1')
    else:
        ValueError('Not a recognizable file. Need a csv or xls(x) file')

    # call function to read based on the shape     
    if data_shape in ['stacked', 'STACKED', 'Stacked']:
        df_data=read_stacked_data(df_pre,owner_name,data_start_row,data_start_column,header_row)
    elif data_shape in ['wide', 'Wide', 'WIDE']:
        df_data=read_wide_data(df_pre,owner_name,data_start_row,data_start_column,header_row,unit_row)
    else:
        raise ValueError([data_shape, 'is NOT recognized. The data shape ought to be either "wide" or "stacked" '])
<<<<<<< HEAD:hgc/import_samples_old.py
    
    write_log_file(log_file_name, log_msg = 'Successful.\n')
    
    # map column names
    write_log_file(log_file_name, log_msg = 'Mapping column names now......')
    
    df_data=map_column_name(df_data) # call the function to mao columns

    write_log_file(log_file_name, log_msg = 'Successful.\n')

=======
>>>>>>> parent of 66c5083... Store df's in a list to save cpu time; add 2 examp:hgc/import_samples.py

    # get/add a (new) column as detection limit and adjust values accordingly too
    write_log_file(log_file_name, log_msg = 'Getting detection limits now......')

    df_data=get_detection_limit(df_data)

    write_log_file(log_file_name, log_msg = 'Successful.\n')

    
    # remove duplicate rows
    write_log_file(log_file_name, log_msg = 'Removing duplicate rows now......')

    df_date=remove_duplicate_row(df_data)

<<<<<<< HEAD:hgc/import_samples_old.py
    write_log_file(log_file_name, log_msg = 'Successful.\n')

    # check datatime format
    write_log_file(log_file_name, log_msg = 'Checking data formats now......')

    df_data=check_format(df_data)
=======
    # # map column names
    # df_data=map_column_name(df_data)

    # # check datatime format
    # df_data=check_format(df_data)


>>>>>>> parent of 66c5083... Store df's in a list to save cpu time; add 2 examp:hgc/import_samples.py

    write_log_file(log_file_name, log_msg = 'Successful.\n')

    
    # wrapping up
    write_log_file(log_file_name, log_msg = 'A dataframe has been generated. The program ends.\n')

    return df_data

# def map_unit(units_input,values,file_path_spreedsheet):
#     ''' this is a function used to map units
#     the desired format of units should be pre-defined in a spreadsheet or other known format
#     '''
#     # keep input as reference
#     units_input_ref=units_input
#     values_ref=values
    
#     # read a spreadsheet with pre-defined conversion
#     df_unit=pd.read_excel(file_path_spreedsheet,encoding='latin1')
    
#     # get units before and after conversion from the spreadsheet
#     units_before=list(df_unit.iloc[:,0]) 
#     units_after=list(df_unit.iloc[:,1])
#     magnitude=np.array(df_unit.iloc[:,2])

#     # fill nan in magnitude
#     d=np.isnan(magnitude) 
#     magnitude[d]=1.0

#     # turn both units and values to list if they are series/dataframes
#     units_input=list(units_input)
#     values=list(values)
    
#     # remove ',' in values if there is, and turn it to float if it is string
#     # if values[0] is str:
#     for i,value in enumerate(values):
#         values[i]=value.replace(',','')
#     values=[float(i) for i in values]
   
#     for id_unit_input,unit in enumerate(units_input,start=0):
#         value=values[id_unit_input]
#         if unit == 'mg/L': # skip 
#             continue
#         else:
#             if unit in (units_before): 
#                 index_unit=(units_before).index(unit)
#                 if isinstance(units_after[index_unit],str) is False:
#                     # keep unchanged if empty
#                     units_after[index_unit]=units_before[index_unit] 
#                 else: pass
#                 unit=units_after[index_unit] 
#             # replacement for both units and values
#             units_input[id_unit_input]=unit
#             values[id_unit_input]=value*magnitude[index_unit]
#     return units_input, values



# def map_column_name(df_data):
#     # remove .,-,+,(), and space in column names
#     for i in range(len(df_pre.columns)):
#         new_columns_names[i]=new_columns_names[i].replace('.','')
#         new_columns_names[i]=new_columns_names[i].replace('(','')
#         new_columns_names[i]=new_columns_names[i].replace(')','')
#         new_columns_names[i]=new_columns_names[i].replace('-','')
#         new_columns_names[i]=new_columns_names[i].replace('+','')
#         new_columns_names[i]=new_columns_names[i].replace(' ','')
#         new_columns_names[i]=new_columns_names[i].replace('_','')
#     df_pre.columns=new_columns_names  
#     # remove completely empty columns to save memory
#     index_non_null=list(~df_pre.loc[7:,:].isnull().all(axis=0))
#     df_pre=df_pre.iloc[:,index_non_null]

#     # remove some irrelevant columns
#     df_pre_main=df_pre_main.drop(['name','winning','Typesystem',
#                                 'filter','Xcoord','Ycoord',
#                                 'surflev','upfiltlev','lowfiltlev','origin'],axis=1)
#     return df_data