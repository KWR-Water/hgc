import hgc
from phreeqpython import PhreeqPython, Solution
import pytest
import pandas as pd

@pytest.fixture
def mineral_data():
    df = pd.read_excel('./examples/data/dataset_minerals.xlsx', skiprows=[1])
    df.hgc.make_valid()
    return df

def test_data_is_valid(mineral_data):
    ''' test whether the data in the excel that contains all
        data is valid. The data is used to test all the phreeqpython
        related functionality '''
    assert mineral_data.hgc.is_valid == True

def test_phreeqpython_installed():
    '''test phreeqpython can be imported and used. test
       this by adding 1 simple solution to the PhreeqPython instance'''
    pp = PhreeqPython()
    solution = pp.add_solution_simple({'CaCl2':1.0,'NaHCO3':2.0})

def test_calculate_sic(mineral_data):
    ''' test the calculation of the saturation index (SI) of
        calcite is performed correctly '''
    df = mineral_data
    sic = df.hgc.sic
    # assert sic == 0.7
    # raise NotImplementedError()






