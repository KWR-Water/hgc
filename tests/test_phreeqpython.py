''' Testing of the integration of phreeqpython in hgc '''
import logging

import numpy as np
import pandas as pd
import pytest
from phreeqpython import PhreeqPython, Solution

import hgc
from hgc.constants.constants import mw


@pytest.fixture(name='mineral_data')
def fixture_mineral_data():
    ''' fixture that loads the test data into a dataframe and makes it valid
        (if possible). the dataframe is returned '''
    df = pd.read_csv('./examples/data/dataset_basic.csv',
                     skiprows=[1], index_col=None)
    df[df.hgc.hgc_cols] = df[df.hgc.hgc_cols].astype(float)
    df.hgc.make_valid()
    return df


@pytest.fixture(name='consolidated_data')
def fixture_consolidated_data():
    ''' same as fixture mineral_data, but now
        including consolidate before returning
        df '''
    df = pd.read_csv('./examples/data/dataset_basic.csv',
                     skiprows=[1], index_col=None)
    df[df.hgc.hgc_cols] = df[df.hgc.hgc_cols].astype(float)
    df.hgc.make_valid()
    df.hgc.consolidate(inplace=True, use_so4=None, use_ph='lab')
    return df


@pytest.fixture(name='phreeqpython_solutions_excel')
def fixture_phreeqpython_solutions_excel():
    ''' Add the solutions of the excel file manually to test
        whether they are added correctly and to easily check
        whether all derived quantities like EC, and SI of calicite
        are correct by hgc methods '''
        #     {'temp': 10, 'Alkalinity': 0, 'O(0)': '11 ', 'C(-4)': '0 as CH4', 'pH': 4.5, 'Na': '9 charge', 'K': 0.4, 'Ca': 1, 'Mg': 1.1, 'Fe': 0.1, 'Mn': 0.02, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'},
        #     {'temp': 10, 'Alkalinity': 0, 'O(0)': '2 ', 'C(-4)': '0 as CH4', 'pH': 4.3, 'Na': '15 charge', 'K': 1.1, 'Ca': 2, 'Mg': 1.6, 'Fe': 0.29, 'Mn': 0.05, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10, 'Alkalinity': 0, 'O(0)': '1 ', 'C(-4)': '0 as CH4', 'pH': 4.4, 'Na': '19 charge', 'K': 1.8, 'Ca': 2, 'Mg': 3.0, 'Fe': 0.12, 'Mn': 0.06, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10, 'Alkalinity': 7, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 5.5, 'Na': '20 charge', 'K': 2.1, 'Ca': 3, 'Mg': 3.9, 'Fe': 2.33, 'Mn': 0.13, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10, 'Alkalinity': 13, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 5.7, 'Na': '21 charge', 'K': 2.8, 'Ca': 5, 'Mg': 5.4, 'Fe': 3.43, 'Mn': 0.03, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10, 'Alkalinity': 23, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 6.2, 'Na': '24 charge', 'K': 1.8, 'Ca': 13, 'Mg': 2.7, 'Fe': 0.7, 'Mn': 0.09, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10, 'Alkalinity': 92, 'O(0)': '0 ', 'C(-4)': '0.14 as CH4', 'pH': 7.4, 'Na': '29 charge', 'K': 1.9, 'Ca': 38, 'Mg': 2.8, 'Fe': 0.3, 'Mn': 0.13, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.1, 'Alkalinity': 146, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 7.7, 'Na': '29 charge', 'K': 2.0, 'Ca': 51, 'Mg': 3.4, 'Fe': 0.51, 'Mn': 0.13, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.2, 'Alkalinity': 151, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 7.7, 'Na': '15 charge', 'K': 1.4, 'Ca': 48, 'Mg': 3.1, 'Fe': 3.4, 'Mn': 0.18, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.5, 'Alkalinity': 156, 'O(0)': '0 ', 'C(-4)': '5 as CH4', 'pH': 7.6, 'Na': '15 charge', 'K': 1.2, 'Ca': 48, 'Mg': 2.5, 'Fe': 1.22, 'Mn': 0.13, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.7, 'Alkalinity': 169, 'O(0)': '0 ', 'C(-4)': '9.1 as CH4', 'pH': 8.1, 'Na': '24 charge', 'K': 9.5, 'Ca': 13, 'Mg': 21, 'Fe': 0.69, 'Mn': 0.04, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.8, 'Alkalinity': 398, 'O(0)': '0 ', 'C(-4)': '18.2 as CH4', 'pH': 8.5, 'Na': '155 charge', 'K': 11.5, 'Ca': 3, 'Mg': 3.1, 'Fe': 0.62, 'Mn': 0.04, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.7, 'Alkalinity': 525, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 8.2, 'Na': '190 charge', 'K': 16.8, 'Ca': 9, 'Mg': 9.5, 'Fe': 0.17, 'Mn': 0.12, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.8, 'Alkalinity': 801, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 7.7, 'Na': '445 charge', 'K': 58, 'Ca': 27, 'Mg': 19.9, 'Fe': 1.6, 'Mn': 0.12, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 10.8, 'Alkalinity': 903, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 8.5, 'Na': '910 charge', 'K': 134, 'Ca': 66, 'Mg': 71, 'Fe': 5.4, 'Mn': 0.3, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        #     {'temp': 11.0, 'Alkalinity': 2635, 'O(0)': '0 ', 'C(-4)': '0 as CH4', 'pH': 7.8, 'Na': '3380 charge', 'K': 95, 'Ca': 160, 'Mg': 390, 'Fe': 2.3, 'Mn': 0.03, 'Amm': '1.29', 'Si': '0.2 as SiO2', 'Cl': 16, 'S(6)': '7 as SO4', 'N(5)': '3.4 as NO3', 'F': 0.027, 'Mn(7)': '5.2 as KMnO4'}
        # ]
    pp = PhreeqPython()
    solution_dictionaries = [
        {'temp': 10,   'Alkalinity':    '0 as HCO3', 'O(0)': '11 ', 'C(-4)':    '0 as CH4', 'pH': 4.5, 'Na':    '9', 'K':   0.4, 'Ca':   1, 'Mg':   1.1, 'Fe': 0.10, 'Mn': 0.02, 'Amm':  1.29, 'Si':  '0.2 as SiO2', 'Cl':   16, 'S(6)':  '7 as SO4', 'N(5)':  '3.4 as NO3', 'F':  0.02700, 'Mn(7)':   '5.2 as KMnO4'},
        {'temp': 10,   'Alkalinity':    '0 as HCO3', 'O(0)':  '2 ', 'C(-4)':    '0 as CH4', 'pH': 4.3, 'Na':   '15', 'K':   1.1, 'Ca':   2, 'Mg':   1.6, 'Fe': 0.29, 'Mn': 0.05, 'Amm':  0.05, 'Si': '11.2 as SiO2', 'Cl':   19, 'S(6)': '16 as SO4', 'N(5)': '22.6 as NO3', 'F':  0.08000, 'Mn(7)':  '17.4 as KMnO4'},
        {'temp': 10,   'Alkalinity':    '0 as HCO3', 'O(0)':  '1 ', 'C(-4)':    '0 as CH4', 'pH': 4.4, 'Na':   '19', 'K':   1.8, 'Ca':   2, 'Mg':   3.0, 'Fe': 0.12, 'Mn': 0.03, 'Amm':  0.05, 'Si': '10.6 as SiO2', 'Cl':   31, 'S(6)': '18 as SO4', 'N(5)': '12.0 as NO3', 'F':  0.07000, 'Mn(7)':   '3.0 as KMnO4'},
        {'temp': 10,   'Alkalinity':    '7 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 5.5, 'Na':   '20', 'K':   2.1, 'Ca':   3, 'Mg':   3.9, 'Fe': 2.33, 'Mn': 0.06, 'Amm':  0.08, 'Si': '15.4 as SiO2', 'Cl':   34, 'S(6)': '19 as SO4', 'N(5)':  '0.1 as NO3', 'F':  0.12000, 'Mn(7)':   '5.3 as KMnO4'},
        {'temp': 10,   'Alkalinity':   '13 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 5.7, 'Na':   '21', 'K':   2.8, 'Ca':   5, 'Mg':   5.4, 'Fe': 3.43, 'Mn': 0.13, 'Amm':  0.19, 'Si': '18.6 as SiO2', 'Cl':   41, 'S(6)': '20 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00501, 'Mn(7)':   '7.3 as KMnO4'},
        {'temp': 10,   'Alkalinity':   '23 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 6.2, 'Na':   '24', 'K':   1.8, 'Ca':  13, 'Mg':   2.7, 'Fe': 0.70, 'Mn': 0.03, 'Amm':  0.23, 'Si': '15.1 as SiO2', 'Cl':   41, 'S(6)': '24 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00501, 'Mn(7)':  '13.9 as KMnO4'},
        {'temp': 10,   'Alkalinity':   '92 as HCO3', 'O(0)':  '0 ', 'C(-4)': '0.14 as CH4', 'pH': 7.4, 'Na':   '29', 'K':   1.9, 'Ca':  38, 'Mg':   2.8, 'Fe': 0.30, 'Mn': 0.09, 'Amm':  0.24, 'Si': '15.6 as SiO2', 'Cl':   44, 'S(6)': '36 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00501, 'Mn(7)':  '16.8 as KMnO4'},
        {'temp': 10,   'Alkalinity':  '121 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 7.6, 'Na':   '31', 'K':   2.0, 'Ca':  47, 'Mg':   3.3, 'Fe': 0.40, 'Mn': 0.13, 'Amm':  0.34, 'Si': '13.3 as SiO2', 'Cl':   50, 'S(6)': '35 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00501, 'Mn(7)':  '11.9 as KMnO4'},
        {'temp': 10.1, 'Alkalinity':  '146 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 7.7, 'Na':   '29', 'K':   2.0, 'Ca':  51, 'Mg':   3.4, 'Fe': 0.51, 'Mn': 0.13, 'Amm':  0.44, 'Si': '20.0 as SiO2', 'Cl':   45, 'S(6)': '22 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.01000, 'Mn(7)':   '0.0 as KMnO4'},
        {'temp': 10.2, 'Alkalinity':  '151 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 7.7, 'Na':   '15', 'K':   1.4, 'Ca':  48, 'Mg':   3.1, 'Fe': 3.40, 'Mn': 0.18, 'Amm':  0.68, 'Si': '16.0 as SiO2', 'Cl':   33, 'S(6)':  '0 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.01000, 'Mn(7)':   '0.0 as KMnO4'},
        {'temp': 10.5, 'Alkalinity':  '156 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '5 as CH4', 'pH': 7.6, 'Na':   '15', 'K':   1.2, 'Ca':  48, 'Mg':   2.5, 'Fe': 1.22, 'Mn': 0.13, 'Amm':  0.45, 'Si': '17.6 as SiO2', 'Cl':   29, 'S(6)':  '0 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.03000, 'Mn(7)':  '16.6 as KMnO4'},
        {'temp': 10.7, 'Alkalinity':  '169 as HCO3', 'O(0)':  '0 ', 'C(-4)':  '9.1 as CH4', 'pH': 8.1, 'Na':   '24', 'K':   9.5, 'Ca':  13, 'Mg':  21.0, 'Fe': 0.69, 'Mn': 0.04, 'Amm':  0.83, 'Si': '22.9 as SiO2', 'Cl':   33, 'S(6)':  '0 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.10000, 'Mn(7)':  '11.5 as KMnO4'},
        {'temp': 10.8, 'Alkalinity':  '398 as HCO3', 'O(0)':  '0 ', 'C(-4)': '18.2 as CH4', 'pH': 8.5, 'Na':  '155', 'K':  11.5, 'Ca':   3, 'Mg':   3.1, 'Fe': 0.62, 'Mn': 0.04, 'Amm':  6.19, 'Si': '17.4 as SiO2', 'Cl':   35, 'S(6)':  '0 as SO4', 'N(5)':  '0.0 as NO3', 'F':  1.50000, 'Mn(7)':  '84.9 as KMnO4'},
        {'temp': 10.7, 'Alkalinity':  '525 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 8.2, 'Na':  '190', 'K':  16.8, 'Ca':   9, 'Mg':   9.5, 'Fe': 0.17, 'Mn': 0.12, 'Amm':  8.26, 'Si': '45.0 as SiO2', 'Cl':   60, 'S(6)':  '0 as SO4', 'N(5)':  '0.0 as NO3', 'F':  1.10000, 'Mn(7)': '132.0 as KMnO4'},
        {'temp': 10.8, 'Alkalinity':  '801 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 7.7, 'Na':  '445', 'K':  58.0, 'Ca':  27, 'Mg':  19.9, 'Fe': 1.60, 'Mn': 0.12, 'Amm': 20.00, 'Si': '83.2 as SiO2', 'Cl':  390, 'S(6)':  '9 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00000, 'Mn(7)': '470.0 as KMnO4'},
        {'temp': 10.8, 'Alkalinity':  '903 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 8.5, 'Na':  '910', 'K': 134.0, 'Ca':  66, 'Mg':  71.0, 'Fe': 5.40, 'Mn': 0.30, 'Amm': 49.00, 'Si': '71.6 as SiO2', 'Cl': 1320, 'S(6)': '15 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00000, 'Mn(7)': '130.0 as KMnO4'},
        {'temp': 11.0, 'Alkalinity': '2635 as HCO3', 'O(0)':  '0 ', 'C(-4)':    '0 as CH4', 'pH': 7.8, 'Na': '3380', 'K':  95.0, 'Ca': 160, 'Mg': 390.0, 'Fe': 2.30, 'Mn': 0.03, 'Amm': 49.00, 'Si': '71.6 as SiO2', 'Cl': 5285, 'S(6)':  '4 as SO4', 'N(5)':  '0.0 as NO3', 'F':  0.00000, 'Mn(7)': '160.0 as KMnO4'},
    ]

    solutions = [None] * len(solution_dictionaries)
    for _i, sol_dict in enumerate(solution_dictionaries):
        sol_dict['units'] = 'mg/L'
        solutions[_i] = pp.add_solution(sol_dict)
    return pp, solutions


def test_data_is_valid(mineral_data):
    ''' test whether the data in the excel that contains all
        data is valid. The data is used to test all the phreeqpython
        related functionality '''
    assert mineral_data.hgc.is_valid


def test_add_not_consolidated_solution(mineral_data):
    ''' test the calculation of the saturation index (SI) of
        calcite is performed correctly '''
    df = mineral_data
    with pytest.raises(ValueError) as excinfo:
        df.hgc.get_phreeqpython_solutions()
        assert "The required column ph is missing in the dataframe.  " in excinfo


def test_phreeqpython_installed():
    '''test phreeqpython can be imported and used. test
       this by adding 1 simple solution to the PhreeqPython instance'''
    pp = PhreeqPython()
    pp.add_solution_simple({'CaCl2': 1.0, 'NaHCO3': 2.0})


def test_add_oxygen(consolidated_data, phreeqpython_solutions_excel):
    ''' Test oxygen is added and returned correctly to and from
    phreeqpython with or without. Test it in pure phreeqpython (because there
    it is not working as expected)
    - test that no O(0) added yields no O in solution
    - test that adding `O(0)` `as O2` yields wrong result
    - test that adding `O(0)` without `as O2` yields correct result
    - test that adding in the SamplesFrame O2 concentration yields correct results '''
    pp = PhreeqPython()
    test_solution_dict = {'units': 'mg/L',
                          'Cl': 8.0,
                          'Na': '2.0 charge',
                          'Alkalinity': '2.0 as HCO3',
                          'Ca': 1.0,
                          'pH': 7,
                          'temp': 11
                          }
    sol = pp.add_solution(test_solution_dict)
    assert sol.total_element('O') == 0.0

    test_solution_dict['O(0)'] = '3 as O2'
    sol1 = pp.add_solution(test_solution_dict)
    assert sol1.species['O2'] * 2 * mw('O') * 1000. != pytest.approx(3., 1.e-4)

    test_solution_dict['O(0)'] = 3
    sol1 = pp.add_solution(test_solution_dict)
    assert sol1.species['O2'] * 2 * mw('O') * 1000. == pytest.approx(3., 1.e-4)

    test_data = pd.DataFrame({'Cl': 8, 'Na': 2, 'alkalinity': 2,
                              'Ca': 1, 'O2': 3, 'ph': 7,
                              'temp': 11}, index=[0])
    test_data.hgc.make_valid()
    test_data.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)
    sols = test_data.hgc.get_phreeqpython_solutions(inplace=False)
    assert sols[0].species['O2'] * 2 * \
        mw('O') * 1000. == pytest.approx(3., 1.e-4)


def test_warning_with_hco3_column(caplog):
    """ test whether a warning is logged when using hco3 as column (and not
    alkalinity). and whether hco3 and bicarbonate columns in SamplesFrame are
    ignored in phreeq calculations"""
    test_data_no_alk = pd.DataFrame({'Cl': 8, 'Na': 2,
                                     'Ca': 1, 'O2': 3, 'ph': 7,
                                     'temp': 11}, index=[0])
    test_data_alk = pd.DataFrame({'Cl': 8, 'Na': 2, 'alkalinity': 2,
                                  'Ca': 1, 'O2': 3, 'ph': 7,
                                  'temp': 11}, index=[0])
    test_data_hco3 = pd.DataFrame({'Cl': 8, 'Na': 2, 'hco3': 2,
                                   'Ca': 1, 'O2': 3, 'ph': 7,
                                   'temp': 11}, index=[0])
    test_data_bicarb = pd.DataFrame({'Cl': 8, 'Na': 2, 'bicarbonate': 2,
                                     'Ca': 1, 'O2': 3, 'ph': 7,
                                     'temp': 11}, index=[0])
    test_data_both = pd.DataFrame({'Cl': 8, 'Na': 2, 'bicarbonate': 2,
                                   'alkalinity': 2,
                                   'Ca': 1, 'O2': 3, 'ph': 7,
                                   'temp': 11}, index=[0])
    test_data_no_alk.hgc.make_valid()
    test_data_alk.hgc.make_valid()
    test_data_hco3.hgc.make_valid()
    test_data_bicarb.hgc.make_valid()
    test_data_both.hgc.make_valid()

    test_data_no_alk.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)
    test_data_alk.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)
    test_data_hco3.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)
    test_data_bicarb.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)
    test_data_both.hgc.consolidate(
        use_so4=None, use_ph=None, use_ec=None, use_temp=None)

    with caplog.at_level(logging.WARNING):
        sol_no_alk = test_data_no_alk.hgc.get_phreeqpython_solutions(inplace=False)
    assert caplog.text == ''
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        sol_alk = test_data_alk.hgc.get_phreeqpython_solutions(inplace=False)
    assert caplog.text == ''
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        sol_hco3 = test_data_hco3.hgc.get_phreeqpython_solutions(inplace=False)
    assert 'bicarbonate (or hco3) is found, but no alkalinity' in caplog.text
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        sol_bicarb = test_data_bicarb.hgc.get_phreeqpython_solutions(inplace=False)
    assert 'bicarbonate (or hco3) is found, but no alkalinity' in caplog.text
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        sol_both = test_data_both.hgc.get_phreeqpython_solutions(inplace=False)
    assert 'bicarbonate (or hco3) and alkalinity' in caplog.text
    caplog.clear()

    assert sol_hco3.values[0].species == sol_bicarb.values[0].species
    assert sol_hco3.values[0].species == sol_no_alk.values[0].species
    assert sol_hco3.values[0].species != sol_alk.values[0].species
    assert sol_both.values[0].species == sol_alk.values[0].species





def test_add_solution(consolidated_data, phreeqpython_solutions_excel):
    ''' Assert phreeqpython solutions are returned as series with correct
       compounds'''
    df = consolidated_data
    # pp = phreeqpython_solutions_excel[0]
    solutions_direct = phreeqpython_solutions_excel[1]

    solutions_hgc = df.hgc.get_phreeqpython_solutions(inplace=False)
    assert all([isinstance(s, Solution) for s in solutions_hgc])

    for _i, sol in enumerate(solutions_hgc):
        sol_pp = solutions_direct[_i]
        assert sol.species_molalities == sol_pp.species_molalities, f'species molalities are not equal for solution #{_i}'
        # assert sol.species_molalities == pytest.approx(sol_pp.species_molalities, abs=1.e-4, rel=1e-1), f'species molalities are not equal for solution #{_i}'


def test_solution_auto_equilibrate(consolidated_data):
    """ assert that solutions are equilibrated with Na or Cl depending
        on what their concentrations are """
    df = consolidated_data
    df = df.iloc[:3, :]
    # make sure that equilibrating with Na will fail because
    # it will needs a concentration below 0 to match the
    # charge in balance
    df.loc[0, 'Fe'] = 2*df.loc[0, 'Na']
    sol = df.hgc.get_phreeqpython_solutions(equilibrate_with='auto', inplace=False)
    Na_in_sol = [s.total_element('Na') * mw('Na') for s in sol]
    Cl_in_sol = [s.total_element('Cl') * mw('Cl') for s in sol]
    # first one equilibrates with Cl
    np.testing.assert_allclose(
        Na_in_sol[:1], df.loc[:0, 'Na'].values, rtol=1.e-1)
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(Na_in_sol[1:],
                                   df.loc[1:, 'Na'].values,
                                   rtol=1.e-1)
    # others one equilibrates with Na
    np.testing.assert_allclose(
        Cl_in_sol[1:], df.loc[1:, 'Cl'].values, rtol=1.e-1)


def test_solution_equilibrate_with(consolidated_data):
    ''' Assert phreeqpython solutions are returned as series'''
    df = consolidated_data

    solutions_default = df.hgc.get_phreeqpython_solutions(inplace=False)
    solutions_Na = df.hgc.get_phreeqpython_solutions(equilibrate_with='Na', inplace=False)
    solutions_Cl = df.hgc.get_phreeqpython_solutions(equilibrate_with='Cl', inplace=False)
    solutions_none = df.hgc.get_phreeqpython_solutions(equilibrate_with=None, inplace=False)
    solutions_auto = df.hgc.get_phreeqpython_solutions(equilibrate_with='auto', inplace=False)

    # get the list of Na-concentrations in the phreeqpython-solutions (from mmol/L to
    # mg/L)
    Na_in_sol_default = [s.total_element('Na') * mw('Na')
                         for s in solutions_default]
    Na_in_sol_Na = [s.total_element('Na') * mw('Na') for s in solutions_Na]
    Na_in_sol_Cl = [s.total_element('Na') * mw('Na') for s in solutions_Cl]
    Na_in_sol_none = [s.total_element('Na') * mw('Na') for s in solutions_none]
    Na_in_sol_auto = [s.total_element('Na') * mw('Na') for s in solutions_auto]

    # get the list of Fe-concentrations in the phreeqpython-solutions (from mmol/L to
    # mg/L)
    Fe_in_sol_default = [s.total_element('Fe') * mw('Fe')
                         for s in solutions_default]
    Fe_in_sol_none = [s.total_element('Fe') * mw('Fe')
                      for s in solutions_none]
    Fe_in_sol_auto = [s.total_element('Fe') * mw('Fe')
                      for s in solutions_auto]

    # test that default equilibrate with is None by returning the same array
    np.testing.assert_array_equal(Na_in_sol_default, Na_in_sol_none)
    # assert that indeed Na-concentration is altered by comparing it
    # to the Na concentration when Cl is used for equilibration
    assert all(np.not_equal(Na_in_sol_Cl, Na_in_sol_Na))
    # assert that auto equals with Na for this case
    assert all(np.not_equal(Na_in_sol_none, Na_in_sol_Na))
    # assert Na-concentration is not altered by using equilibrate with
    # Cl. Na concentration should be the same as in the original dataframe
    # to some extent of accuracy (this is generally not closer than 10% in my experience).
    np.testing.assert_allclose(Na_in_sol_Cl, df.Na.values, rtol=1.e-1)
    np.testing.assert_allclose(Na_in_sol_none, df.Na.values, rtol=1.e-1)
    # same assertion but now for Fe
    np.testing.assert_allclose(Fe_in_sol_default, df.Fe.values, rtol=1.e-1)
    np.testing.assert_allclose(Fe_in_sol_none, df.Fe.values, rtol=1.e-1)
    np.testing.assert_allclose(Fe_in_sol_auto, df.Fe.values, rtol=1.e-1)


# def test_calculate_ec_with_measured_values(mineral_data):
#     ''' test whether ec is calculated 10% accurately by hgc compared
#         to the measured values given in the original excel-hgc example
#         file '''
#     df = mineral_data
#     df.hgc.consolidate(use_ph='lab')
#     ec = df.hgc.get_specific_conductance()

#     # we cannot use data of the HGC excel sheet to check
#     # whether the correct values have been calculated,
#     # because Pieter has different ways of calculating it.
#     np.testing.assert_allclose(ec, df.ec.values, rtol=1.e-1)

#     # test it by calculating it seperately by phreeqpython manually.


def test_sc(consolidated_data, phreeqpython_solutions_excel):
    ''' Assert get_specific_conductance wrapper returns correct saturation indices of all test
        solutions in the fixtures '''
    df = consolidated_data
    solutions_direct = phreeqpython_solutions_excel[1]
    sc_hgc = df.hgc.get_specific_conductance(inplace=False)
    sc_pp = pd.Series([sol.sc for sol in solutions_direct], index=sc_hgc.index, name=sc_hgc.name)

    pd.testing.assert_series_equal(sc_hgc, sc_pp)


def test_si_calcite(consolidated_data, phreeqpython_solutions_excel):
    ''' Assert get_si wrapper returns correct saturation indices of all test
        solutions in the fixtures '''
    df = consolidated_data
    # pp = phreeqpython_solutions_excel[0]
    solutions_direct = phreeqpython_solutions_excel[1]

    si_calcite_hgc = df.hgc.get_saturation_index('Calcite', inplace=False)
    si_calcite_pp = pd.Series([sol.si('Calcite') for sol in solutions_direct],
                              index=si_calcite_hgc.index,
                              name=si_calcite_hgc.name)

    pd.testing.assert_series_equal(si_calcite_hgc, si_calcite_pp)


def test_for_docs():
    ''' A test to check if the code in docs is wrong or only the building fails. This can be removed. '''
    test_data = {
        'ph_lab': [4.5, 5.5, 7.6], 'ph_field': [4.4, 6.1, 7.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
        'temp': [10, 10, 10],
        'alkalinity':  [0, 7, 121],
        'O2':  [11, 0, 0],
        'Na': [9, 20, 31], 'K': [0.4, 2.1, 2.0],
        'Ca': [1, 3, 47],
        'Fe': [0.10, 2.33, 0.4],
        'Mn': [0.02, 0.06, 0.13],
        'NH4': [1.29, 0.08, 0.34],
        'SiO2': [0.2, 15.4, 13.3],
        'SO4': [7, 19, 35],
        'NO3': [3.4, 0.1, 0],
    }
    df = pd.DataFrame.from_dict(test_data)
    df.hgc.make_valid()
    df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None,
                       use_so4=None, use_o2=None)

    si_calcite = df.hgc.get_saturation_index('Calcite')
