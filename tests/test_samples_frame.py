import sys
import logging

import hgc
from hgc.samples_frame import SamplesFrame
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest


def test_hgc_namespace_is_added():
    ''' Test whether the HGC methods are added to
        dataframes that are created
    '''
    with mock.patch.object(SamplesFrame, "_validate") as mocked_validate:
        mocked_validate.return_value = True
        df = pd.DataFrame()
        df.hgc


def test_init_samples_frame():
    #caplog.set_level(logging.INFO)
    #logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(message)s', level=logging.DEBUG)
    #logging.getLogger().addHandler(logging.StreamHandler())
    df = pd.read_excel('./examples/data/dataset_invalid_columns.xlsx', skiprows=[1])
    assert df.hgc.is_valid == False
    

def test_make_valid(): 
    df = pd.read_excel('./examples/data/dataset_invalid_columns.xlsx', skiprows=[1])
    df.hgc.make_valid()

    assert df.hgc.is_valid == True


def test_get_ratios_invalid_frame():
    df = pd.DataFrame() 
    with pytest.raises(ValueError):
        df.hgc.get_ratios()


def test_get_ratios():
    df = pd.read_excel('./examples/data/dataset_basic.xlsx', skiprows=[1])
    df_ratios = df.hgc.get_ratios()

    assert isinstance(df_ratios, pd.core.frame.DataFrame)


def test_consolidate():
    df = pd.read_excel('./examples/data/dataset_basic.xlsx', skiprows=[1])
    df.consolidate()