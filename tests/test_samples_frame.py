import hgc
from hgc.samples_frame import SamplesFrame
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest

# define the fixtures
@pytest.fixture(name='test_data_bas_vdg')
def fixture_test_bas_vdg():
    """ test data as been used by Bas vdG from testing routine 060602020"""
    test_data = {
        'ph_lab': [7.5, 6.1, 7.6], 'ph_field': [4.4, 6.1, 7.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
        'temp': [10, 10, 10],
        'alkalinity':  [110, 7, 121],
        'O2':  [11, 0, 0],
        'Na': [2,40,310],
        'K':[0.4, 2.1, 2.0],
        'Ca':[40,3,47],
        'Fe': [0.10, 2.33, 0.4],
        'Mn': [0.02, 0.06, 0.13],
        'NH4': [1.29, 0.08, 0.34],
        'SiO2': [0.2, 15.4, 13.3],
        'SO4': [7,19,35],
        'NO3': [3.4,0.1,0],
        'Cl': [10,50,310]
    }
    df = pd.DataFrame(test_data)
    df.hgc.make_valid()
    return pd.DataFrame(df)

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
    df_ratios_original = pd.DataFrame(dict(
        cl_to_br=[286, None, None, 309, None, None, 275, None,
                  None, None, 322, 275, 292, 231, None, None, None, ],
        cl_to_na=[1.78, 1.27, 1.63, 1.70, 1.95, 1.71, 1.52, 1.61,
                  1.55, 2.20, 1.93, 1.38, 0.23, 0.32, 0.88, 1.45, 1.56, ],
        ca_to_mg=[0.9, 1.3, 0.7, 0.8, 0.9, 4.8, 13.6, 14.2,
                  15.0, 15.5, 19.2, 0.6, 1.0, 0.9, 1.4, 0.9, 0.4],
        ca_to_sr=[143, 40, 74, 115, 192, 130, 238, 276, 245, 267, 253, 81, 120, 122, None, None, None, ],
        fe_to_mn=[5.00, 5.80, 4.00, 38.83, 26.38, 23.33, 3.33, 3.08, 3.92, 18.89, 9.38, 17.25, 15.50, 1.42, 13.33, 18.00, 76.67],
        hco3_to_ca=[0.00, 0.00, 0.00, 1.53, 1.71, 1.16, 1.59, 1.69, 1.88, 2.07, 2.13, 8.54, 87.14, 38.32, 19.49, 8.99, 10.82, ],
        hco3_to_sum_anions=[None, 0.00, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, ],
        cod_to_doc=[0.33, 0.37, 0.12, 0.10, 0.09, 0.25, 0.27, 0.23, None, None, 0.32, 0.36, 0.40, 0.37, 0.38, 0.37, 0.38, ],
        monc=[2.69, 2.50, 3.51, 3.52, 3.55, 2.97, 2.90, 3.06, None, None, 2.67, 2.51, 2.39, 2.53, 2.48, 2.49, 2.48, ],
        suva=[None] * 17))
    df_ratios_original['2h_to_18o'] = [None] * 17

    df_ratios = df.hgc.get_ratios()


    assert isinstance(df_ratios, pd.core.frame.DataFrame)


def test_consolidate():
    df = pd.read_csv('./examples/data/dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df.hgc.consolidate(use_so4=None, use_o2=None, use_ph='lab')

def test_consolidate_w_not_all_cols():
    ''' test that consolidate works when not all
        (default) columns are present '''
    testdata = {
        'ph_lab': [4.3, 6.3, 5.4], 'ph_field': [4.4, 6.1, 5.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
    }
    df = pd.DataFrame.from_dict(testdata)

    df.hgc.make_valid()

    with pytest.raises(ValueError):
        df.hgc.consolidate(use_ph='field', use_ec='lab',)

    df.hgc.consolidate(use_ph='field', use_ec='lab', use_temp=None,
                       use_so4=None, use_o2=None)

def test_get_sum_anions_1():
    """ This testcase is based on row 11, sheet 4 of original Excel-based HGC """
    df = pd.DataFrame([[56., 16., 1.5, 0.027, 0.0, 0.0, 3.4, 0.04, 7., 4.5]], columns=('Br', 'Cl', 'doc', 'F', 'alkalinity', 'NO2', 'NO3', 'PO4', 'SO4', 'ph'))
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions()
    assert np.round(sum_anions[0], 2)  == 0.67

def test_get_sum_anions_2():
    """ This testcase is based on sheet 5, row 12 of original Excel-based HGC """
    testdata = {
        'Br': [0],
        'Cl': [19.0],
        'doc': [4.4],
        'F': [0.08],
        'alkalinity': [0.0],
        'NO2': [0.0],
        'NO3': [22.6],
        'PO4': [0.04],
        'SO4': [16.0],
        'ph': [4.3]
    }
    df = pd.DataFrame.from_dict(testdata)
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions()
    assert np.round(sum_anions[0], 2)  == 1.28

def test_get_sum_anions_3(test_data_bas_vdg):
    """ Test based on Bas vd Grift bug report """
    df = test_data_bas_vdg
    df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None, use_so4=None, use_o2=None)

    sum_anions = df.hgc.get_sum_anions()
    np.testing.assert_almost_equal(sum_anions.values,
                                   np.array([0.77472968, 1.7837688, 3.3159489,
                                             ]))

    sum_cations = df.hgc.get_sum_cations()
    np.testing.assert_almost_equal(sum_cations.values,
                                   np.array([2.1690812, 2.0341514, 15.9185133]))

def test_get_sum_cations():
    df = pd.DataFrame([[4.5, 9.0, 0.4, 1.0, 1.1, 0.1, 0.02, 1.29, 99.0, 3.0, 0.3, 3.2, 0.6, 0.6, 10.4, 7.0, 15.0]], columns=('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn'))
    df.hgc.make_valid()
    sum_cations = df.hgc.get_sum_cations()
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
        'alkalinity': [0.0],
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

def test_get_stuyfzand_water_type(test_data_bas_vdg):
    """ test based on bas van de grift his test data """
    # abbrevation
    df = test_data_bas_vdg
    df.hgc.consolidate(use_ph='lab', use_ec='lab',
                       use_temp=None, use_so4=None, use_o2=None)
    assert df.hgc.get_stuyfzand_water_type().to_list() == ['g1CaHCO3o', 'F*NaClo' , 'B1NaCl']


testdata = {
     'ph_lab': [7.5, 6.1, 7.6], 'ph_field': [4.4, 6.1, 7.7],
     'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
     'temp': [10, 10, 10],
     'alkalinity':  [110, 7, 121],
    #  'HCO3':  [110, 7, 121],
     'O2':  [11, 0, 0],
     'Na': [2,40,310],
     'K':[0.4, 2.1, 2.0],
     'Ca':[40,3,47],
     'Fe': [0.10, 2.33, 0.4],
     'Mn': [0.02, 0.06, 0.13],
     'NH4': [1.29, 0.08, 0.34],
    #  'Amm': [1.29, 0.08, 0.34],
     'SiO2': [0.2, 15.4, 13.3],
     'SO4': [7,19,35],
     'NO3': [3.4,0.1,0],
     'Cl': [10,50,310]
}

df = pd.DataFrame.from_dict(testdata)
df.hgc.make_valid()
df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None, use_so4=None, use_o2=None)
df.hgc.get_stuyfzand_water_type()
[_.total('N') for _ in df.hgc.get_phreeqpython_solutions()]



def test_get_bex():
    """ Sheet 5 - col EC in HGC Excel """
    df = pd.DataFrame([[15., 1.1, 1.6, 19.]], columns=('Na', 'K', 'Mg', 'Cl'))
    df.hgc.make_valid()
    bex = df.hgc.get_bex()
    assert np.round(bex[0], 2)  == 0.24
