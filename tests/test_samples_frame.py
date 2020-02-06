import hgc
from hgc.samples_frame import SamplesFrame
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest


def test_valid_samples_frame():
    #caplog.set_level(logging.INFO)
    #logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(message)s', level=logging.DEBUG)
    #logging.getLogger().addHandler(logging.StreamHandler())
    df = pd.read_csv('./examples/data/dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    assert df.hgc.is_valid == True

def test_valid_samples_frame_excel():
    #caplog.set_level(logging.INFO)
    #logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(message)s', level=logging.DEBUG)
    #logging.getLogger().addHandler(logging.StreamHandler())
    df = pd.read_excel('./examples/data/dataset_basic.xlsx', skiprows=[1])
    assert df.hgc.is_valid == True

def test_invalid_samples_frame():
    #caplog.set_level(logging.INFO)
    #logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(message)s', level=logging.DEBUG)
    #logging.getLogger().addHandler(logging.StreamHandler())
    df = pd.read_csv('./examples/data/dataset_invalid_columns.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    assert df.hgc.is_valid == False


def test_make_valid():
    df = pd.read_csv('./examples/data/dataset_invalid_columns.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df.hgc.make_valid()

    assert df.hgc.is_valid == True


def test_get_ratios_invalid_frame():
    df = pd.DataFrame()
    with pytest.raises(ValueError):
        df.hgc.get_ratios()


def test_get_ratios():
    df = pd.read_csv('./examples/data/dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df_ratios = df.hgc.get_ratios()

    assert isinstance(df_ratios, pd.core.frame.DataFrame)


def test_consolidate():
    df = pd.read_csv('./examples/data/dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df.hgc.consolidate(use_so4=None, use_o2=None)


@pytest.mark.skip(reason="work in progress")
def test_molar_weight():
    raise NotImplementedError
    c = constants


def test_get_sum_anions_stuyfzand():
    df = pd.DataFrame() 
    df.hgc.get_sum_anions_stuyfzand()


def test_get_sum_cations_stuyfzand():
    df = pd.DataFrame() 
    df.hgc.get_sum_anions_stuyfzand()


def test_get_stuyfzand_water_type():
    df = pd.read_excel('./examples/data/dataset_basic.xlsx', skiprows=[1])
    df_out = df.hgc.get_stuyvesant_water_type()


def test_get_bex():
    df = pd.DataFrame([[15., 1.1, 1.6, 19.]], columns = ('Na', 'K', 'Mg', 'Cl')) 
    df.hgc.make_valid()
    bex = df.hgc.get_bex()
    assert np.round(bex[0], 2)  == 0.24