# Script to generate table with default values and alias used by hgc.named_entity_recognition.mapping
# and store it as pickle.
# Note: Excel makes errors when saving as CSV
# For example: some symbols (e.g. latin symbols) are saved incorretly as "?"

# %% Import packages

import datetime
import hgc.named_entity_recognition.mapping as mapping
import itertools
import numpy as np
import openpyxl
import os
import pandas as pd
import pickle
import pubchempy as pcp
import re
import time

from googlesearch import search
from google_trans_new import google_translator
from pathlib import Path
from ratelimit import limits, sleep_and_retry

# %% Defaults

PATH = Path(__file__).parent  # set work directory to current module
os.chdir(PATH)

PATH_FILE_EXCEL = PATH / 'default_features_alias 20210205.xlsx'
PATH_FILE_PKL = PATH / 'default_feature_properties.pkl'
PATH_FILE_PKL_NL2EN = PATH / 'di_nl2en.pkl'  # dictionary Dutch --> English
PATH_FILE_PKL_A2PC = PATH / 'di_alias2pubchem.pkl'  # dictionary English --> PubChem
SHEET_ALIAS = 'Alias'
SHEET_TRANS = 'NL2EN' # translated terms
SHEET_PROP = 'Properties'
SHEET_2HGC = 'HGCinput'
COLS_ALIAS_EN = ['HGC', 'MicrobialParameters', 'OtherEnglishAlias']
COLS_ALIAS_NL =['OtherDutchAlias', 'SIKB', 'NVWA', 'REWAB']
COLS_CAS = ['Other_CASnumber', 'SIKB_CASnumber', 'NVWA_CASnumber', 'REWAB_CASnumber']

PERIOD_PUBCHEM = .1  # time in seconds between each call to pubchem API
PERIOD_GOOGLETRANS = .21  # time in seconds between each call to google translate API
PERIOD_GOOGLESEARCH = .1  # time in seconds between each call to google searchengine API

# %% Functions


def _split_string_in_dfcol_to_list(df=None, cols=[]):
    """Convert all items in selected columns of dataframe to list. Assumes vertical bar "|" as splitter."""
    for col in cols:
        items = []
        for item in df[col]:
            if len(item) > 0:
                item = [x.strip() for x in item.split('|')]
            else:
                item = []
            items.append(item)
        df[col] = items


def _split_df_to_list(df=None):
    """Convert all items in dataframe to list, using vertical bar "|" as splitter."""
    for col in df.columns:
        items = []
        for item in df[col]:
            if len(item) > 0:
                item = [x.strip() for x in item.split('|')]
            else:
                item = []
            items.append(item)
        df[col] = items


def _list_in_df_to_lists(df):
    """Convert columns of dataframe to a single list. All items in all columns must contain lists."""
    lst = list(itertools.chain.from_iterable(
        [list(itertools.chain.from_iterable(list(filter(None, (df[col]))))) for col in df.columns]))
    return lst


@sleep_and_retry
@limits(calls=1, period=PERIOD_GOOGLETRANS)
def _ratelimit_googletranslate():
    """Empty function to limit calls to googletrans API."""
    return


@sleep_and_retry
@limits(calls=1, period=PERIOD_PUBCHEM)
def _ratelimit_pubchem():
    return


@sleep_and_retry
@limits(calls=1, period=PERIOD_GOOGLESEARCH)
def _ratelimit_googlesearch():
    return


def translate_string(string_source, source_language='nl', dest_language='en', max_attempt=3):
    """Translate a string of text.

    Parameters
    ----------
    max_attempt: int
        Maximum number of attempts to reach API-server of translator.
    """
    attempt = 0
    while attempt < max_attempt:
        try:
            _ratelimit_googletranslate()
            string_dest = google_translator().translate(string_source, lang_src=source_language, lang_tgt=dest_language)
            break
        except:
            attempt += 1
            if attempt >= max_attempt:
                string_dest = False
                print('WARNING: translation failed after %x attemps. Check API or exceedance of quota' % (attempt))

    return string_dest


def translate_list(lst_source, source_language='nl', dest_language='en'):
    """Translate list of strings from source language to destination language, item by item."""
    lst_dest = []
    counter = 0
    for string_source in lst_source:
        string_dest = translate_string(string_source, source_language=source_language, dest_language=dest_language)
        if counter % 25 == 0:
            print('translation progress: ' + str(counter) + ' of ' + str((len(lst_source))))
        if string_dest is not False:
            lst_dest.append(string_dest)
            counter += 1
        else:
            print('WARNING: stop translation')
            break
    return lst_dest


def translate_list_by_chunck(lst_source, source_language='nl', dest_language='en', max_chunksize=5000):
    """Translate list of strings from source language to destination language.
    Speed is enhanced for lists of short items by joining multiple items to larger strings before translating.

    Parameters
    ----------
    lst_source: list
        List of strings to be translated.
        Not recommended for strings with length almost equal or larger than max_chuncksize
    source_language: str
        Source language (for notation, check the module passed in the methods argument)
    dest_language: str
        Destination language
      max_chunksize: int
        maximum number of characters per request

    Return
    ------
    lst_dest: list
        List of translated strings.
    """
    if lst_source == []:
        lst_dest = []
    else:
        # step 1: Join list to single string with " | " as separator.
        i = 1
        while i * '|' in ' '.join(str(x) for x in lst_source):  # check if i * "|"  exists
            i += 1  # if exists: make separator longer --> "||" etc.
        sep = ' ' + i * '|' + ' '  # add leading and trailing white space to separator.
        str_source = sep.join(str(x) for x in lst_source)

        # Step 2: Divide the string into chuncks, smaller than max_chuncksize
        start = 0
        end = 0
        chuncks_source = []  # list of joined strings to be translated
        # find cutoff point so that each chunck has less characters than the max chuncksize allowed by translate API's
        while end < len(str_source):
            s = str_source[start:start + max_chunksize]
            if (s.rfind(sep) == -1) and (len(s) < max_chunksize):  # no separator found in short chunck
                end = len(str_source)
            elif s.rfind(sep) == -1:  # no separator found in long chunck
                end = start + max_chunksize
                print('WARNING: item in list > chunck size -> Check if position of items in list_dest matches list_source')
            elif len(s) < max_chunksize:
                end = len(str_source)
            else:
                end = start + s.rfind(sep) + len(sep)
            chunck = str_source[start:end]
            start = end
            chuncks_source += [chunck]

        # step 3: Translate all chuncks
        counter = 0
        continue_translate = True  # keep track of which methods tried for translation (currently on googletrans)
        chuncks_dest = ''
        for chunck in chuncks_source:
            if chunck is list:
                chunck = chunck[0]  # convert to string
            if continue_translate is False:  # in case translation failed for previous chunk
                chunck2 = chunck  # use untranslated string
            else:
                chunck2 = translate_string(chunck, source_language=source_language, dest_language=dest_language)
                if chunck2 is False:
                    chunck2 = chunck
                    continue_translate = False
                    print('WARNING: stop translating')
                if counter % 10 == 0:
                    print('translation progress: ' + "{0:.1%}".format(counter / (len(chuncks_source))))
            chuncks_dest += chunck2  # add chunck to chunks
            counter += 1

        # Step 4: convert translated string back to list
        lst_dest = chuncks_dest.split(sep)
        lst_dest = [string.strip() for string in lst_dest]  # remove leading and trailing white space

    return lst_dest


def _get_casnumber_from_compound(compound, return_first=False):
    """Get list of CAS numbers that match PubChemPy object (compound)."""
    lst_cas = []
    for syn in compound.synonyms:
        match = re.match('(\d{2,7}-\d\d-\d)', syn)
        if match:
            lst_cas.append(match.group(1))
    if return_first is True:
        try:
            lst_cas = lst_cas[0]
        except:
            lst_cas = ''
    return lst_cas


def _googlesearch_pubchem(query):
    websites = []
    _ratelimit_googlesearch()
    for j in search(query + ' pubchem.ncbi.nlm.nih.gov', tld="co.in", num=5, stop=5, pause=PERIOD_GOOGLESEARCH):
        websites.append(j)
    for web in websites:
        if 'https://pubchem.ncbi.nlm.nih.gov/compound' in web:
            substance_google = web.split('/')[-1]
            break

    return substance_google


def find_pubchem_compound(identifier='', method='pubchem'):
    compounds_lst = []  # loop through all matching compounds
    try:
        _ratelimit_pubchem()
        if identifier.isdigit():  # if integer, then treat as PubChem CID.
            compounds = pcp.get_compounds(identifier, 'cid')
        else:
            compounds = pcp.get_compounds(identifier, 'name')  # find all compounds that match
        for compound in compounds:
            compound = pcp.Compound.from_cid(compound.cid)
            compounds_lst.append({
                'PubChemCID': compound.cid,
                'IUPAC': compound.iupac_name,
                'CASlist': _get_casnumber_from_compound(compound),  # PubChem sometime returns multiple CASnumbers
                'CASnumber': _get_casnumber_from_compound(compound, return_first=True),  # use first if multiple CAS numbers
                'Method': method,
                'Identifier': identifier,
            })
    except:
        pass

    return compounds_lst


def find_pubchem_list(lst=[]):
    """Find compound on PubChem for list of parameters (in English).

    Return
    ------
    dct: dictionary
        example: {NO3: {'PubChemCID':943, IUPAC:'nitrate', 'CASlist': ['14797-55-8'], 'CASnumber':'14797-55-8'},
                  'PO4': {'PubChemCID': ..., IUPAC: 'phosphate'', 'CASlist': [....], 'CASnumber':...}} etc.
    """
    di = {}
    n = len(lst)  # total number of features
    i = 0
    for item in lst:
        di[item] = find_pubchem_compound(identifier=item)
        if di[item] == []:
            try:
                di[item] = find_pubchem_compound(identifier=_googlesearch_pubchem(item), method='googlesearch')
            except:
                pass
        if i % 20 == 0:
            print('pubchempy match feature ', i, 'of', n)
        i += 1

    return di


def save_sheet_to_excel(df, file_path, sheet_name):
    """Add (overwrite) dataframe as sheet to existing excel file."""
    writer = pd.ExcelWriter(file_path, engine='openpyxl')

    # delete sheet if it already exists
    if os.path.exists(file_path):
        book = openpyxl.load_workbook(file_path)
        writer.book = book
        try:
            del book[sheet_name]
        except:
            pass

    df.to_excel(writer, sheet_name=sheet_name, index=False)
    writer.save()
    writer.close()


# %% MAIN


starttime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
print(starttime)

# Read Excel and pickle
df_alias = pd.read_excel(PATH_FILE_EXCEL, sheet_name=SHEET_ALIAS, encoding='ISO-8859-1', skiprows=4).fillna('')
df_trans = pd.read_excel(PATH_FILE_EXCEL, sheet_name=SHEET_TRANS, encoding='ISO-8859-1', skiprows=0).fillna('')
# df_prop = pd.read_excel(PATH_FILE_EXCEL, sheet_name=SHEET_PROP, encoding='ISO-8859-1', skiprows=0).fillna('')
di_alias2pubchem = pickle.load(open(PATH_FILE_PKL_A2PC, "rb"))

# convert all items to lists in columns with CAS and Alias
_split_string_in_dfcol_to_list(df=df_alias, cols = COLS_ALIAS_NL + COLS_ALIAS_EN + COLS_CAS)

# select Dutch alias to translate
mask = df_alias[COLS_ALIAS_EN].sum(axis=1).apply(lambda c: c == [])  # select rows without English Alias
lst_source = _list_in_df_to_lists(df=df_alias.loc[mask, COLS_ALIAS_NL])  # list Dutch alias in row without English Alias
lst_source2 = list(set(lst_source) - set(df_trans['NL_alias']))  # select alias not yet translated in NL2EN Dbase

# translate Dutch alias to English and save translations
lst_dest2 = translate_list_by_chunck(lst_source=lst_source2)
di_trans = {
    **dict(zip(df_trans['NL_alias'], df_trans['EN_alias'])),
    **dict(zip(lst_source2, lst_dest2)),  # newly translated terms
}
save_sheet_to_excel(pd.DataFrame({'NL_alias': list(di_trans.keys()), 'EN_alias': list(di_trans.values())}), PATH_FILE_EXCEL, SHEET_TRANS)
pickle.dump(di_trans, open(PATH_FILE_PKL_NL2EN, "wb"))

# update alias df with English translations
mask = df_alias[COLS_ALIAS_EN].sum(axis=1).apply(lambda c: c == [])  # row without English Alias
mask2 = df_alias[COLS_ALIAS_NL].sum(axis=1).apply(lambda c: c == [])  # row without Dutch Alias
x = df_alias[COLS_ALIAS_NL][~mask2 & mask].sum(axis=1).map(lambda x: x[0])  # Dutch items in rows without English Alias
y = x.map(di_trans).reindex(range(0, len(df_alias))).replace(np.nan, "")  # English translation
z = df_alias['OtherEnglishAlias'] + y.apply(lambda c: [c])  # merge English translation with existing English Alias
df_alias['OtherEnglishAlias'] = z.apply(lambda c: list(filter(None, c)))  # update column, remove empty list

end_translate_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
print(end_translate_time)

# Select Alias to retrieve from PubChem
di_alias2pubchem = pickle.load(open(PATH_FILE_PKL_A2PC, "rb"))  # load existing database
lst_alias = _list_in_df_to_lists(df_alias[COLS_ALIAS_EN + COLS_CAS])  # all Alias
lst_alias2 = list(set(lst_alias) - set(di_alias2pubchem.keys()))  # Alias without pubchem info

# retrieve compound info from PubChem and save database
di = find_pubchem_list(lst=lst_alias2)
di_alias2pubchem = {
    **di_alias2pubchem,
    **di
}
pickle.dump(di_alias2pubchem, open(PATH_FILE_PKL_A2PC, "wb"))

end_pcp_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
print(end_pcp_time)


# evaluate each row: what CAS and CID to use
series_acol = df_alias[COLS_ALIAS_EN].sum(axis=1)
series_ccol = df_alias[COLS_CAS].sum(axis=1)
di_append = {
    'cas_expected': [],
    'cid_expected': [],
    'warnings': [],
}
for row in range(len(df_alias)):
    warning = []
    di_ccol = {}
    di_acol = {}

    # get CAS and CID from CAS_columns
    ccol_caslist = []  # CAS entered in default table
    ccol_cidlist = []  # CID belonging to CAS
    for cas_item in series_ccol[row]:
        for di in di_alias2pubchem[cas_item]:
            if 'PubChemCID' not in di:
                cid = ''
            else:
                cid = di['PubChemCID']
            # ccol_cidlist.append(cid)
            if cid in di_ccol:
                di_ccol[cid] += [cas_item]
            else:
                di_ccol[cid] = [cas_item]
            ccol_caslist += [cas_item]
            ccol_cidlist += [cid]

    # get CAS and CID from Alias_columns
    acol_caslist = []
    acol_cidlist = []
    for alias_item in series_acol[row]:
        for di in di_alias2pubchem[alias_item]:
            if 'CASlist' not in di:
                cas = []
            elif (len(di['CASlist']) == 0):
                cas = []
            elif (len(ccol_caslist) == 0):  # CAS_column empty
                cas = di['CASlist']
            elif len(list(set(di['CASlist']) & set(ccol_caslist))) == 0:
                cas = []
                warning += ['CAS derived from English alias not found in CAS_column: ' + str(acol_caslist) + '. ']
            else:
                cas = list(set(di['CASlist']) & set(ccol_caslist))

            # Note: CID as list
            if 'PubChemCID' not in di:
                cid = []
            elif (len([di['PubChemCID']]) == False):
                cid = []
            elif (len(ccol_cidlist) == 0):
                cid = [di['PubChemCID']]
            elif len(list(set([di['PubChemCID']]) & set(ccol_cidlist))) == 0:
                cid = []
                warning += ['CID derived from Alias_column not found in CID_column: ' + str(acol_caslist) + '. ']
            else:
                cid = list(set([di['PubChemCID']]) & set(ccol_cidlist))

            # only update CAS/CID if (1) CID of Alias_columns and CAS_columns overlap or (2) CAS_columns has no CID
            if len(cid) > 0:  # cid always has length 0 or 1
                acol_cidlist += cid
                acol_caslist += cas
                if cid[0] in di_acol:
                    di_acol[cid[0]] += cas
                else:
                    di_acol[cid[0]] = cas

    # select most frequent CID
    all_cid = ccol_cidlist + acol_cidlist
    shared_cid = list(set(ccol_cidlist) & set(acol_cidlist))
    if len(shared_cid) == 0:
        shared_cid = all_cid
    cid_freq = {x: all_cid.count(x) for x in all_cid if x in shared_cid}  # dictionary with frequency of CID
    if cid_freq == {}:
        cid = ''
    else:
        cid = max(cid_freq, key=cid_freq.get)  # find CID most frequently used.

    # check if CID was found. If not --> create empty dictionary to prevent KeyError
    try:
        di_ccol[cid]
    except:
        di_ccol[cid] = []
    try:
        di_acol[cid]
    except:
        di_acol[cid] = []

    # select most frequent CAS (for previsouly selected CID)
    all_cas = di_ccol[cid] + di_acol[cid]  # Note:
    shared_cas = list(set(di_ccol[cid]) & set(di_acol[cid]))
    if (len(shared_cas) == 0) & (len(di_ccol[cid]) == 0):  # no CID in CAS_columns
        shared_cid = di_acol[cid]  # --> use only Alias_column
    elif (len(shared_cas) == 0):  # (1) no CID in Alias_column (2) or both CAS_column and Alias_column have CID but they do not overlap
        shared_cid = di_ccol[cid]  # --> use only CAS_column
    cas_freq = {x: all_cas.count(x) for x in all_cas if x in shared_cas}
    if cas_freq == {}:
        cas = ''
    else:
        cas = max(cas_freq, key=cas_freq.get)

    di_append['cas_expected'].append(cas)
    di_append['cid_expected'].append(cid)
    di_append['warnings'].append(warning)


df = pd.concat([df_alias, pd.DataFrame(di_append)], axis=1)

row = 5943



# di_alias2pubchem['benzene'][0]['CASlist']
# di_alias2pubchem['71-43-2'][0]['name']
# df_alias.iloc[1075]

# di_alias2pubchem['cefotaxime']  # 3 x CID
# di_alias2pubchem['63527-52-6']  # 6 x CID
# df_alias.iloc[3203]

# a = pcp.get_compounds('Terpene-m', 'name')
# a[0].cid
# a[0].synonyms

# c = pcp.get_compounds('129874-08-4', 'name')
# c[0].cid
# c[0].synonyms


# _googlesearch_pubchem('terpenes')



# df_alias[COLS_ALIAS_EN + COLS_CAS].sum(axis=1)



# flag rows with non-overlapping CID
# for each row: check if CID is same, if multiple CID: check most likely CID based on CAS

# if row has same CID and CAS --> merge. Unless DoNotUsePubchemName



# something went wrong in translation ######################################
# lst_dest = lst_dest[:2046] + ['carbamazepine epoxide 10.11'] + ['methylbenzylaniline naphthylamine'] + lst_dest[2047:]

