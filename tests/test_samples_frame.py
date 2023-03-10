import logging
from hgc.samples_frame import SamplesFrame
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest
from . import test_directory

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
    df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    assert df.hgc.is_valid == True

def test_invalid_changed_samples_frame():
    df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    assert df.hgc.is_valid == True
    df.loc[1, 'F'] = -1
    # this test does not fail because the self._obj in df.hgc is the orginal
    # pandas obj and is not changed in the hgc namespace
    assert df.hgc._obj.loc[1, 'F'] == -1
    assert df.hgc.is_valid == False

def test_valid_samples_frame_excel():
    df = pd.read_excel(test_directory / 'data' / 'dataset_basic.xlsx', skiprows=[1])
    assert df.hgc.is_valid == True

def test_invalid_samples_frame():
    df = pd.read_csv(test_directory / 'data' / 'dataset_invalid_columns.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    assert df.hgc.is_valid == False


def test_make_valid():
    df = pd.read_csv(test_directory / 'data' / 'dataset_invalid_columns.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df.hgc.make_valid()

    assert df.hgc.is_valid == True

def test_replace_detection_limit():
    df_original = pd.read_csv(test_directory / 'data' / 'dataset_invalid_columns.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
    df_half = df_original.copy(deep=True)
    df_on = df_original.copy(deep=True)
    df_zero = df_original.copy(deep=True)
    df_invalid = df_original.copy(deep=True)

    df_half.hgc._replace_detection_lim(rule='half')
    df_on.hgc._replace_detection_lim(rule='on')
    df_zero.hgc._replace_detection_lim(rule='zero')

    with pytest.raises(ValueError) as exc_info:
        df_invalid.hgc._replace_detection_lim(rule='invalid_option')
    assert 'Invalid rule' in str(exc_info)

    expected_changed_column = 'ec_field'
    expected_unchanged_columns = list(set(df_half.columns) - {expected_changed_column})

    df_is_not_nan_and_not_changed_half = df_half.isna() | (df_half == df_original)
    df_is_not_nan_and_not_changed_on = df_on.isna() | (df_on == df_original)
    df_is_not_nan_and_not_changed_zero = df_zero.isna() | (df_zero == df_original)

    assert all(df_is_not_nan_and_not_changed_half[expected_unchanged_columns])
    assert all(df_is_not_nan_and_not_changed_on[expected_unchanged_columns])
    assert all(df_is_not_nan_and_not_changed_zero[expected_unchanged_columns])

    assert not all(df_half[expected_changed_column] == df_original[expected_changed_column])
    assert not all(df_on[expected_changed_column] == df_original[expected_changed_column])
    assert not all(df_zero[expected_changed_column] == df_original[expected_changed_column])

    assert all(df_half.ec_field.astype(float) == [200, 350, 215, 1.5, 1.5, 525])
    assert all(df_on.ec_field.astype(float) == [200, 350, 215, 3, 3, 525])
    assert all(df_zero.ec_field.astype(float) == [200, 350, 215, 0, 0, 525])


def test_get_ratios_invalid_frame():
    df = pd.DataFrame()
    with pytest.raises(ValueError):
        df.hgc.get_ratios()


def test_get_ratios(caplog):
    df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
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

    df_ratios = df.hgc.get_ratios(inplace=False)


    assert isinstance(df_ratios, pd.core.frame.DataFrame)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        df.hgc.get_ratios()
    assert len(caplog.records) > 0

def test_consolidate():
    df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)
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

def test_consolidate_alkalinity():
    ''' test that consolidate works when not all
        (default) columns are present '''
    testdata = {
        'alkalinity': [4.3, 6.3, 5.4], 'hco3': [4.4, 6.1, 5.7],
        'ph_lab': [4.3, 6.3, 5.4], 'ph_field': [4.4, 6.1, 5.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
    }
    df = pd.DataFrame.from_dict(testdata)
    df.hgc.make_valid()

    alk = df.alkalinity
    hco3 = df.hco3
    df.hgc.consolidate(use_ph='field', use_ec='lab',use_alkalinity='alkalinity',
    use_so4=None, use_o2=None, use_temp=None)
    pd.testing.assert_series_equal(df.alkalinity, alk)
    df.hgc.consolidate(use_alkalinity='hco3', use_so4=None, use_o2=None,
    use_temp=None)
    assert all(df.alkalinity.values == hco3.values)
    assert 'hco3' not in df.columns



def test_get_sum_anions_1():
    """ This testcase is based on row 11, sheet 4 of original Excel-based HGC """
    df = pd.DataFrame([[56., 16., 1.5, 0.027, 0.0, 0.0, 3.4, 0.04, 7., 4.5]], columns=('Br', 'Cl', 'doc', 'F', 'alkalinity', 'NO2', 'NO3', 'PO4', 'SO4', 'ph'))
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions(inplace=False)
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
    sum_anions = df.hgc.get_sum_anions(inplace=False)
    assert np.round(sum_anions[0], 2)  == 1.28

def test_get_sum_anions_3(test_data_bas_vdg):
    """ Test based on Bas vd Grift bug report """
    df = test_data_bas_vdg
    df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None, use_so4=None, use_o2=None)

    sum_anions = df.hgc.get_sum_anions(inplace=False)
    np.testing.assert_almost_equal(sum_anions.values,
                                   np.array([2.285332174633880, 1.9222333673010, 11.4556385209268
                                             ]))

    sum_cations = df.hgc.get_sum_cations(inplace=False)
    np.testing.assert_almost_equal(sum_cations.values,
                                   np.array([2.1690812, 2.0341514, 15.9185133]))

def test_get_sum_cations():
    df = pd.DataFrame([[4.5, 9.0, 0.4, 1.0, 1.1, 0.1, 0.02, 1.29, 99.0, 3.0, 0.3, 3.2, 0.6, 0.6, 10.4, 7.0, 15.0]], columns=('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn'))
    df.hgc.make_valid()
    sum_cations = df.hgc.get_sum_cations(inplace=False)
    assert np.round(sum_cations[0], 2)  == 0.66

def test_get_ion_balance(test_data_bas_vdg):
    expected_value = pytest.approx([99.54, 99.62, 97.77], abs=0.01)
    assert test_data_bas_vdg.hgc.get_ion_balance(inplace=False).to_numpy() == expected_value
    test_data_bas_vdg.hgc.get_ion_balance(inplace=True)
    assert test_data_bas_vdg.ion_balance.to_numpy() == expected_value


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
    water_type = df.hgc.get_stuyfzand_water_type(inplace=False)
    assert water_type[0] == 'g*NaNO3o'
    df.hgc.get_stuyfzand_water_type()
    assert df.water_type[0] == 'g*NaNO3o'

def test_get_stuyfzand_water_type_2(test_data_bas_vdg):
    """ test based on bas van de grift his test data """
    # abbrevation
    df = test_data_bas_vdg
    df.hgc.consolidate(use_ph='lab', use_ec='lab',
                       use_temp=None, use_so4=None, use_o2=None)
    assert df.hgc.get_stuyfzand_water_type(inplace=False).to_list() == ['g1CaHCO3o', 'F*NaClo', 'B1NaCl']


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
    df.hgc.get_stuyfzand_water_type(inplace=False)



def test_get_bex():
    """ Sheet 5 - col EC in HGC Excel """
    df = pd.DataFrame([[15., 1.1, 1.6, 19.]], columns=('Na', 'K', 'Mg', 'Cl'))
    df.hgc.make_valid()
    bex = df.hgc.get_bex(inplace=False)
    assert np.round(bex[0], 2)  == 0.24

def test_inplace(test_data_bas_vdg):
    """ Test to see if the inplace argument behaves as expected: returning
    a series in inplace=False and appending the column if inplace=True"""
    test_data_bas_vdg.hgc.consolidate(use_so4=None, use_o2=None, use_ph='lab')
    def assert_column_added_inplace(column, is_added, method_name, method_kwargs):
        """ assert whether a column is added to the dataframe or not when
        a method with its arguments method_kwargs are called """
        df = test_data_bas_vdg.copy(deep=True)
        n_columns = len(df.columns)
        assert column not in df.columns
        method = getattr(df.hgc, method_name)
        df_out = method(**method_kwargs)
        if is_added:
            assert column in df.columns
            assert n_columns != len(df.columns)
            assert df_out is None
        else:
            assert column not in df.columns
            assert n_columns == len(df.columns)
            assert df_out is not None


    assert_column_added_inplace('bex', is_added=True, method_name='get_bex',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('bex', is_added=True, method_name='get_bex',
                                method_kwargs=dict())
    assert_column_added_inplace('bex', is_added=False, method_name='get_bex',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('cl_to_na', is_added=True, method_name='get_ratios',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('cl_to_na', is_added=True, method_name='get_ratios',
                                method_kwargs=dict())
    assert_column_added_inplace('cl_to_na', is_added=False, method_name='get_ratios',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('water_type', is_added=True, method_name='get_stuyfzand_water_type',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('water_type', is_added=True, method_name='get_stuyfzand_water_type',
                                method_kwargs=dict())
    assert_column_added_inplace('water_type', is_added=False, method_name='get_stuyfzand_water_type',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('dominant_anion', is_added=True, method_name='get_dominant_anions',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('dominant_anion', is_added=True, method_name='get_dominant_anions',
                                method_kwargs=dict())
    assert_column_added_inplace('dominant_anion', is_added=False, method_name='get_dominant_anions',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('sum_anions', is_added=True, method_name='get_sum_anions',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('sum_anions', is_added=True, method_name='get_sum_anions',
                                method_kwargs=dict())
    assert_column_added_inplace('sum_anions', is_added=False, method_name='get_sum_anions',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('sum_cations', is_added=True, method_name='get_sum_cations',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('sum_cations', is_added=True, method_name='get_sum_cations',
                                method_kwargs=dict())
    assert_column_added_inplace('sum_cations', is_added=False, method_name='get_sum_cations',
                                method_kwargs=dict(inplace=False))


    assert_column_added_inplace('pp_solutions', is_added=True, method_name='get_phreeqpython_solutions',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('pp_solutions', is_added=True, method_name='get_phreeqpython_solutions',
                                method_kwargs=dict())
    assert_column_added_inplace('pp_solutions', is_added=False, method_name='get_phreeqpython_solutions',
                                method_kwargs=dict(inplace=False))

    assert_column_added_inplace('si_calcite', is_added=True, method_name='get_saturation_index',
                                method_kwargs=dict(inplace=True, mineral_or_gas='calcite'))
    assert_column_added_inplace('si_calcite', is_added=True, method_name='get_saturation_index',
                                method_kwargs=dict(mineral_or_gas='calcite'))
    assert_column_added_inplace('si_calcite', is_added=False, method_name='get_saturation_index',
                                method_kwargs=dict(inplace=False, mineral_or_gas='calcite'))

    assert_column_added_inplace('sc', is_added=True, method_name='get_specific_conductance',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('sc', is_added=True, method_name='get_specific_conductance',
                                method_kwargs=dict())
    assert_column_added_inplace('sc', is_added=False, method_name='get_specific_conductance',
                                method_kwargs=dict(inplace=False))

def test_add_temp_ph_later():

    test_data = {
        'ph_lab': [7.5, 6.1, 7.6], 'ph_field': [4.4, 6.1, 7.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
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

    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_saturation_index('Calcite')
    assert 'required column' in str(exc_info)
    df['ph']=7
    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_saturation_index('Calcite')
    assert 'required column temp' in str(exc_info)
    df['temp']=10
    # assert no error is raised
    df.hgc.get_saturation_index('Calcite')



