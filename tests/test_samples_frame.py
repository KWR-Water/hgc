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
    #c = constants


def test_get_sum_anions_stuyfzand_1():
    """ This testcase is based on row 11, sheet 4 of original Excel-based HGC """
    df = pd.DataFrame([[56., 16., 1.5, 0.027, 0.0, 0.0, 3.4, 0.04, 7., 4.5]], columns=('Br', 'Cl', 'doc', 'F', 'HCO3', 'NO2', 'NO3', 'PO4', 'SO4', 'ph')) 
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions_stuyfzand()
    assert np.round(sum_anions[0], 2)  == 0.67

def test_get_sum_anions_stuyfzand_2():
    """ This testcase is based on sheet 5, row 12 of original Excel-based HGC """
    testdata = {
        'Br': [0],
        'Cl': [19.0],
        'doc': [4.4],
        'F': [0.08],
        'HCO3': [0.0],
        'NO2': [0.0],
        'NO3': [22.6],
        'PO4': [0.04],
        'SO4': [16.0],
        'ph': [4.3]
    }
    df = pd.DataFrame.from_dict(testdata) 
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions_stuyfzand()
    assert np.round(sum_anions[0], 2)  == 1.28

def test_get_sum_cations_stuyfzand():
    df = pd.DataFrame([[4.5, 9.0, 0.4, 1.0, 1.1, 0.1, 0.02, 1.29, 99.0, 3.0, 0.3, 3.2, 0.6, 0.6, 10.4, 7.0, 15.0]], columns=('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn')) 
    df.hgc.make_valid()
    sum_cations = df.hgc.get_sum_cations_stuyfzand()
    assert np.round(sum_cations[0], 2)  == 0.66


def test_get_stuyfzand_water_type():
    """ Testcase matches row 12, sheet 6 of HGC Excel """
    testdata = {
        'Al': [2600],
        'Ba': [44.0],
        'Br': [0.0],
        'Ca': [2.0],
        'Cl': [19.0],
        'Co': [1.2],
        'Cu': [4.0],
        'doc': [4.4],
        'F': [0.08],
        'Fe': [0.29],
        'HCO3': [0.0],
        'K': [1.1],
        'Li': [5.0],
        'Mg': [1.6],
        'Mn': [0.05],
        'Na': [15.0],
        'Ni': [7.0],
        'NH4': [0.05],
        'NO2': [0.0],
        'NO3': [22.6],
        'Pb': [2.7],
        'PO4': [0.04],
        'ph': [4.3],
        'SO4': [16.0],
        'Sr': [50],
        'Zn': [60.0]
    }
    df = pd.DataFrame.from_dict(testdata)
    df.hgc.make_valid()
    water_type = df.hgc.get_stuyfzand_water_type()
    assert water_type[0] == 'g*NaNO3o'

def test_get_bex():
    df = pd.DataFrame([[15., 1.1, 1.6, 19.]], columns=('Na', 'K', 'Mg', 'Cl')) 
    df.hgc.make_valid()
    bex = df.hgc.get_bex()
    assert np.round(bex[0], 2)  == 0.24