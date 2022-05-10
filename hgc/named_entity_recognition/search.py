"""
Functions used for named entity recognition
"""
import pandas as pd
import pubchempy as pcp
import re
import scipy.interpolate

from fuzzywuzzy import fuzz, process
from google_trans_new import google_translator
from ratelimit import limits, sleep_and_retry
from urllib.error import HTTPError


# %% Defaults

# speed and duration of internet queries
PERIOD_PUBCHEM = .1  # time in seconds between each call to pubchem API
PERIOD_GOOGLETRANS = .21  # time in seconds between each call to google translate API
PERIOD_GOOGLESEARCH = 61.  # time in seconds between each call to google searchengine API ####################### Extreme slow

# %% Interpolate


def _interp1d_fill_value(x=[], y=[], **kwargs):
    """
    Generate a linear point-2-point interpolatation function with fixed fill value outside x-range.

    Notes
    -----
    Use the y(xmin) to extrapolate for x < xmin.
    y(xmax) to extrapolate for x > xmax.

    """
    # order lists from small to large x
    dct = dict(sorted(zip(x, y)))
    y_below = list(dct.values())[0]  # fill value below xmin
    y_above = list(dct.values())[-1]  # fill value above xmax

    # generate interpolation function
    function = scipy.interpolate.interp1d(list(dct.keys()), list(dct.values()),
                                   bounds_error=False, fill_value=(y_below, y_above))

    return function


# %% Rate limit


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


# %% Translate


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
        i = 2
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
        
        if len(lst_source) != len(lst_dest):
            raise Exception('ERROR: translate list by chunck -> unequal number of source and english items')

    return lst_dest


# %% PubChem


def get_pubchemcompound(string):
    """get pubchem CID for integer (or integer as string) or compound name (synonym)."""
    try:
        if (isinstance(string, int)) or ((isinstance(string, str)) and (string.isdigit()) and (len(string) > 0)):  # integer, or integer as string     
            _ratelimit_pubchem()
            compounds = pcp.get_compounds(int(string), 'cid')
            identifier = string
        elif (isinstance(string, str)) and (len(string) > 0):  # string
            _ratelimit_pubchem()
            compounds = pcp.get_compounds(string, 'name')
            identifier = process.extractOne(str(string), compounds[0].synonyms, scorer=fuzz.token_sort_ratio)[0]
        else:
            raise Exception('no string or integer')
    except:
        compounds = []
        identifier = ''

    return compounds, identifier


def _get_pubchem_attributes(compound):
    """Get dictionary with CAS and names (synonyms) from PubChem Compound object).
    
    Returns
    -------
    dct: dictionary:
        example {'lst_cas': ['12-34-56', '78-9-10'}], 'cas0': '12-34-56}', 'lst_name': ['abcd', 'efgh'], 'name0': 'abcd'}
    """
    lst_cas = []
    lst_name = []
    for syn in compound.synonyms:
        try:
            lst_cas.append(re.match('(\d{2,7}-\d\d-\d)', syn.lstrip('CAS-').lstrip('CAS ').lstrip('CAS')).group(1))
        except:
            lst_name.append(syn)
        try:
            cas0 = str(lst_cas[0])
        except:  # <1 cas
            cas0 = ''
        try:
            name0 = str(lst_name[0])
        except:  # <1 name
            name0 = ''

    dct = {
        'lst_cas': lst_cas,
        'cas0': cas0,
        'lst_name': lst_name,
        'name0': name0,
    }

    return dct


def _google_pubchemcompound(query, HTTPError_status=0, domain='site:pubchem.ncbi.nlm.nih.gov/compound '):
    """Search pubchem/compounds with google.

    Parameters
    ----------
    query : string
    HTTPError_status : int
        0 -> perform search
        !0 -> pass
    domain: string
        indicate in which domain to search. defualt = 'site:pubchem.ncbi.nlm.nih.gov/compound '

    Returns
    -------
    google_result :
        tuple -> if ERROR
        string -> if succesfull or no result.
    """
    if HTTPError_status != 0:
        google_result = ('HTTPError in previous iteration',)
    else:
        _ratelimit_googlesearch()
        try:
            google_result = googlesearch.lucky(domain + query).split('/')[-1]
        except HTTPError as err:
            google_result = ('HTTPError', str(err))  # Return urllib.error.HTTPError (err) as string to prevent error in dictionary with "cannot serialize io.Buffered object"
            HTTPError_status = 1
            pass
        except StopIteration:
            google_result = ''  # google does not yield search result
            pass
        except:
            google_result = ('Unspecified ERROR',)
            pass
    return google_result, HTTPError_status



