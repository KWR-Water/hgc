import pytest
import pandas as pd
# import os
from pathlib import Path
import pickle as pckl
from hgc.feature_recognition import * 
from hgc import constants
from hgc import convertFeatureNames as cf
from openpyxl.workbook import Workbook
def test_feature_map():
    file_path = Path(constants.__file__).parent / 'default_features_alias.xlsx'
    df = pd.read_excel(file_path, sheet_name='HGC_input_conv')
    df_pubchem = cf.convert_feature_to_standard_pubchem(df.iloc[:,:])
    # export it to an excel spreadsheet
    file_path = Path(constants.__file__).parent / 'default_features_alias2.xlsx'
    df_pubchem.to_excel(file_path) # cannot call xlsxwrite for some unknown reasons