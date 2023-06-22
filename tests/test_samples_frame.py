import logging
from hgc.samples_frame import SamplesFrame
from hgc.constants.constants import mw
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

@pytest.fixture(name='test_data_bas_vdg_consolidated')
def fixture_test_bas_vdg_consolidated(test_data_bas_vdg):
    df = test_data_bas_vdg.copy()
    df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None, use_so4=None, use_o2=None)
    return df

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


def test_elemental_ratios():
    """ test all the ratios are calculated correctly"""

# Cl/Br (molar ratio)
#          * Cl/Na (molar ratio)
#          * Cl/Mg (molar ratio)
#          * Ca/Sr (molar ratio)
#          * Fe/Mn (molar ratio)
#          * HCO3/Ca
    ratios = dict(cl_to_br = ['Cl', 'Br'],
                  cl_to_na = ['Cl', 'Na'],
                  ca_to_mg = ['Ca', 'Mg'],
                  ca_to_sr = ['Ca', 'Sr'],
                  fe_to_mn = ['Fe', 'Mn'],
                  )
    for ratio, (numerator, denominator) in ratios.items():
        dict_df = {
            'ph': np.array(6 * [7]),
            numerator:np.array([1, 2, 3, 1, 2, 3]) * mw(numerator),
            denominator:np.array([1, 1, 1, 2, 2, 2]) * mw(denominator)}
        # dict_df = {k: mw(k)*conc for k, conc in dict_df.items()}
        df = pd.DataFrame.from_dict(dict_df)
        df.hgc.get_ratios()
        np.testing.assert_array_almost_equal(df[ratio].values, np.array([1, 2, 3, 0.5, 1, 1.5]))

def test_alkalinity_ratios():

    dict_df = {
        'alkalinity':np.array([1, 2, 3, 1, 2, 3]) * mw('HCO3'),
        'Ca':np.array([1, 1, 1, 2, 2, 2]) * mw('Ca'),
        'Mg':np.array([1, 1, 1, 2, 2, 2]) * mw('Mg'),
        'ph':np.array(6 * [7]),
    }
    df = pd.DataFrame.from_dict(dict_df)
    df.hgc.get_ratios()

    np.testing.assert_array_almost_equal(df['hco3_to_ca'].values, np.array([1, 2, 3, 0.5, 1, 1.5]))
    np.testing.assert_array_almost_equal(df['hco3_to_ca_and_mg'].values, np.array([0.5, 1, 1.5, 0.25, 0.5, .75]))
    np.testing.assert_array_almost_equal(df['hco3_to_sum_anions'].values, np.array(6 * [1]))

    dict_df['Cl'] = np.array([4, 4, 4, 8, 8, 8]) * mw('Cl')
    df = pd.DataFrame.from_dict(dict_df)
    df.hgc.get_ratios()
    np.testing.assert_array_almost_equal(df['hco3_to_ca'].values, np.array([1, 2, 3, 0.5, 1, 1.5]))
    np.testing.assert_array_almost_equal(df['hco3_to_ca_and_mg'].values, np.array([0.5, 1, 1.5, 0.25, 0.5, .75]))
    np.testing.assert_array_almost_equal(df['hco3_to_sum_anions'].values, np.array([1./5, 2./6, 3./7, 1./9, 2./10, 3./11]))


def test_get_ratios_larger_df(caplog):
    df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv', skiprows=[1], parse_dates=['date'], dayfirst=True)

    df.hgc.consolidate(use_ph='lab')
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
                                   np.array([2.285, 1.922, 11.456]),
                                   decimal=3)

    sum_cations = df.hgc.get_sum_cations(inplace=False)
    np.testing.assert_almost_equal(sum_cations.values,
                                   np.array([2.1690812, 2.0341514, 15.9185133]))

def test_get_sum_cations():
    df = pd.DataFrame([[4.5, 9.0, 0.4, 1.0, 1.1, 0.1, 0.02, 1.29, 99.0, 3.0, 0.3, 3.2, 0.6, 0.6, 10.4, 7.0, 15.0]], columns=('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn'))
    df.hgc.make_valid()
    sum_cations = df.hgc.get_sum_cations(inplace=False)
    assert np.round(sum_cations[0], 2)  == 0.66

def test_get_sum_cations_no_cations():
    df = pd.DataFrame(dict(Cl=[4, 4], Na=[0,1], ph=[10,10]))
    df.hgc.make_valid()
    sum_cations = df.hgc.get_sum_cations(inplace=False)
    assert np.round(sum_cations[0], 2)  == 0.0
    assert np.round(sum_cations[1], 2)  > 0

def test_get_sum_anions_no_anions():
    df = pd.DataFrame(dict(Cl=[0, 4], Na=[1,1], ph=[10,10]))
    df.hgc.make_valid()
    sum_anions = df.hgc.get_sum_anions(inplace=False)
    assert np.round(sum_anions[0], 2)  == 0.0
    assert np.round(sum_anions[1], 2)  > 0

def test_get_sum_an_and_cations_no_ph_raises_error():
    df = pd.DataFrame(dict(Cl=[0, 4], Na=[1,1]))
    df.hgc.make_valid()
    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_sum_anions(inplace=False)
    assert 'missing column ph' in str(exc_info).lower()

    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_sum_cations(inplace=False)
    assert 'missing column ph' in str(exc_info).lower()

def test_get_sum_cations_invalid_ph():
    df = pd.DataFrame(dict(Cl=[4, 4], Na=[1,1], ph=[0, np.nan]))
    df.hgc.make_valid()
    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_sum_anions(inplace=False)
    assert 'invalid value(s) in ph column' in str(exc_info).lower()

def test_get_ion_balance(test_data_bas_vdg_consolidated):
    expected_value = pytest.approx([-2.61, 2.82, 16.30], abs=0.01)
    assert test_data_bas_vdg_consolidated.hgc.get_ion_balance(inplace=False).to_numpy() == expected_value
    test_data_bas_vdg_consolidated.hgc.get_ion_balance(inplace=True)
    assert test_data_bas_vdg_consolidated.ion_balance.to_numpy() == expected_value


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

def test_get_stuyfzand_water_type_2(test_data_bas_vdg_consolidated):
    """ test based on bas van de grift his test data """
    # abbrevation
    df = test_data_bas_vdg_consolidated.copy()
    df['Mg'] = 0 # column required for BEX
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
    df['Mg'] = 0
    assert df.hgc.get_stuyfzand_water_type(inplace=False).to_list() == ['g1CaHCO3o', 'F*NaClo', 'B1NaCl']



def test_get_bex():
    """ Sheet 5 - col EC in HGC Excel """
    df = pd.DataFrame([[15., 1.1, 1.6, 19.]], columns=('Na', 'K', 'Mg', 'Cl'))
    df.hgc.make_valid()
    bex = df.hgc.get_bex(inplace=False)
    assert np.round(bex[0], 2)  == 0.24

def test_get_bex_while_cl_has_nan():
    """ no outcome if any of the columns has no valid value    """
    df = pd.DataFrame([[15., 1.1, 1.6, 19],
                       [15., 1.1, 1.6, np.nan]], columns=('Na', 'K', 'Mg', 'Cl'))
    df.hgc.make_valid()
    with pytest.raises(ValueError) as exc_info:
        bex = df.hgc.get_bex(inplace=False)
    assert "column(s) ['cl" in str(exc_info).lower()

def test_get_bex_without_cl_column():
    """ no outcome if any of the columns has no valid value    """
    df = pd.DataFrame([[15., 1.1, 1.6 ],
                       [15., 1.1, 1.6]], columns=('Na', 'K', 'Mg'))
    df.hgc.make_valid()
    with pytest.raises(ValueError) as exc_info:
        bex = df.hgc.get_bex(inplace=False)
    assert "column(s) ['cl" in str(exc_info).lower()

def test_inplace(test_data_bas_vdg):
    """ Test to see if the inplace argument behaves as expected: returning
    a series in inplace=False and appending the column if inplace=True"""
    test_data_bas_vdg.hgc.consolidate(use_so4=None, use_o2=None, use_ph='lab')
    test_data_bas_vdg['Mg']=0
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
            # assert n_columns == len(df.columns)  # this test does not work for bex because sum_anions is added in that case too. the test above should suffice anyway, so drop this test
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

    assert_column_added_inplace('dominant_cation', is_added=True, method_name='get_dominant_cations',
                                method_kwargs=dict(inplace=True))
    assert_column_added_inplace('dominant_cation', is_added=True, method_name='get_dominant_cations',
                                method_kwargs=dict())
    assert_column_added_inplace('dominant_cation', is_added=False, method_name='get_dominant_cations',
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
    assert 'missing column ph' in str(exc_info).lower()
    df['ph']=7
    with pytest.raises(ValueError) as exc_info:
        df.hgc.get_saturation_index('Calcite')
    assert 'required column temp' in str(exc_info)
    df['temp']=10
    # assert no error is raised
    df.hgc.get_saturation_index('Calcite')




