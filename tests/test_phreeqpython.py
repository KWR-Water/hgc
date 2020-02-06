import hgc
from phreeqpython import PhreeqPython, Solution
import pytest
import pandas as pd

@pytest.fixture
def mineral_data():
    df = pd.read_csv('./examples/data/dataset_basic.csv', skiprows=[1])
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

def test_add_solution(mineral_data):
    ''' test the calculation of the saturation index (SI) of
        calcite is performed correctly '''
    df = mineral_data
    df.hgc.consolidate(inplace=True, use_so4=None)
    solutions_None = df.hgc.get_phreeqpython_solutions(equilibrate_with=None)
    solutions_Na = df.hgc.get_phreeqpython_solutions(equilibrate_with='Na')
    assert len(solutions_Na.isnull())
    solutions_Cl = df.loc[solutions_Na.isnull()].hgc.get_phreeqpython_solutions(equilibrate_with='Cl')

    solutions_Cl.loc[solutions_Cl.isnull()]

def test_add_not_consolidated_solution(mineral_data):
    ''' test the calculation of the saturation index (SI) of
        calcite is performed correctly '''
    df = mineral_data
    with pytest.raises(ValueError) as excinfo:
        df.hgc.get_phreeqpython_solutions()
        assert "The required column ph is missing in the dataframe.  " in excinfo

    # raise NotImplementedError()
def test_calculate_sic(mineral_data):
    ''' test the calculation of the saturation index (SI) of
        calcite is performed correctly '''
    df = mineral_data
    sic = df.hgc.si_calcite()
    assert sic == 0.7
    # raise NotImplementedError()






