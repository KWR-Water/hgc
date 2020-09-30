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


def _fill_df_pubchem(df0, name_transed_cls, idx):
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
    
    # deal with first column with given names
    df1 = df.iloc[:,0].copy()   
    name2trans = list(df1)
    name_transed_cls = Translator().translate(name2trans, src='nl', dest='en')
    idx1 = [pcp.get_compounds(component.text, 'name') for component in name_transed_cls] 
    df0 = _fill_df_pubchem(df0, name_transed_cls, idx1)
    mask1 = [not not elem for elem in idx1]
    df0.loc[mask1,'flag'] = 'from 1st column'

    # deal with second column with CAS number 
    df2 = df.iloc[:,1].copy()
    df2[mask1] = None
    df2 = [str(string).lstrip("'") for string in df2] # remove ' from the beginning of the cas number
    idx2 = [pcp.get_compounds(component, 'name') for component in df2] 
    df0 = _fill_df_pubchem(df0, name_transed_cls, idx2)
    mask2 = [not not elem for elem in idx2]
    df0.loc[mask2,'flag'] = 'from 2nd column'
    
    # deal with the third column with mix number 
    df3 = df.iloc[:,2].copy()
    df3[list(pd.Series(mask1) | pd.Series(mask2))] = None
    idx3 = [pcp.get_compounds(component, 'name') if component is not None else [] for component in df3] 
    df0 = _fill_df_pubchem(df0, name_transed_cls, idx3)
    mask3 = [not not elem for elem in idx3]
    df0.loc[mask3, 'flag'] = 'from 3rd column'

    return df0










    return df0   

