"""
To convert part of the feature names to standard ones in default_features_alias.xlsx
Xin Tian
KWR, October 2020
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


def _fill_df_pubchem(df0, idx):
    empty_check = all([not elem for elem in idx])
    if empty_check:
        df1_proc = pd.DataFrame()
    else:        
        compounds = [pcp.Compound.from_cid(idx0[0].cid) if idx0 != [] else [] for idx0 in idx ]
        formulae = [compound.molecular_formula if compound != [] else [] for compound in compounds]
        iupac_name = [compound.iupac_name if compound != [] else [] for compound in compounds]
        synonyms = [compound.synonyms if compound != [] else [] for compound in compounds]
        cids = [compound.cid if compound != [] else [] for compound in compounds]
        # smiles = [compound.smile if compound != [] else [] for compound in compounds]
        df0.loc[[not not elem for elem in idx],'formulae'] = pd.Series(formulae)[[not not elem for elem in idx]]
        df0.loc[[not not elem for elem in idx],'iupac'] = pd.Series(iupac_name)[[not not elem for elem in idx]]
        df0.loc[[not not elem for elem in idx],'synonyms'] = pd.Series(synonyms)[[not not elem for elem in idx]]
        df0.loc[[not not elem for elem in idx],'compounds'] = pd.Series(compounds)[[not not elem for elem in idx]]
        df0.loc[[not not elem for elem in idx],'cid'] = pd.Series(cids)[[not not elem for elem in idx]]
    return df0

def convert_feature_to_standard_pubchem(df):
    # create an empty df for later use
    dummyarray = np.empty((len(df),6))
    dummyarray[:] = np.nan
    df0 = pd.DataFrame(dummyarray, columns=['iupac','synonyms','compounds','formulae','cid', 'flag'])
    
    # deal with second column with CAS number 
    print('2nd')
    df2 = df.iloc[:,1].copy()
    df2 = pd.Series(df2).replace('nan', np.nan)
    # df2[mask1] = None
    df2 = [str(string).lstrip("'") if string is not np.nan else np.nan for string in df2] # remove ' from the beginning of the cas number
    idx2 = [pcp.get_compounds(component, 'name') if component is not np.nan else [] for component in df2] 
    df0 = _fill_df_pubchem(df0, idx2)
    mask2 = [not not elem for elem in idx2]
    df0.loc[mask2,'flag'] = 'from column B'

    # deal with the third column with mix number 
    print('3rd')
    df3 = df.iloc[:,4].copy()
    df3[mask2] = np.nan
    idx3 = [pcp.get_compounds(component, 'name') if component is not np.nan else [] for component in df3] 
    df0 = _fill_df_pubchem(df0, idx3)
    mask3 = [not not elem for elem in idx3]
    df0.loc[mask3, 'flag'] = 'from column E'

    # deal with first column with given names
    print('1st')
    df1 = df.iloc[:,0].copy()   
    df1[list(pd.Series(mask3) | pd.Series(mask2))] = np.nan
    name2trans = list(df1)
    name_transed_cls = [Translator().translate(name, src='nl', dest='en') if name is not np.nan else [] for name in name2trans]
    # name_transed_cls = name2trans
    idx1 = [pcp.get_compounds(component.text, 'name') if not not component else [] for component in name_transed_cls]     
    df0 = _fill_df_pubchem(df0, idx1)
    mask1 = [not not elem for elem in idx1]
    df0.loc[mask1,'flag'] = 'from column A'

    return df0









