# from hgc import

from hgc.constants import read_write
import pandas as pd
from unittest import mock
import cloudpickle as pickle

def test_hgc_namespaceadded():
    ''' Test whether the HGC methods are added to
        dataframes that are created
    '''
    df = pd.DataFrame(dict(a=[1,2], b=[3,4]))
    df.hgc.convert_to_standard_units()

def test_creating_constants_pickle():
    ''' test the function that creates constants.py
        with named tuple from csv files '''
    read_write.csv_to_pickle()

def test_load_pickle():
    ''' test to load pickle when pickle is created '''
    read_write.csv_to_pickle()
    atoms, ions, properties = read_write.load_pickle_as_namedtuples()
    assert atoms['H'].feature == 'H'
    assert atoms['H'].name == 'Hydrogen'
    assert atoms['H'].unit == 'mg/L'
    assert atoms['H'].mw == 1.00794
    assert atoms['H'].oxidized == 1
    assert atoms['H'].reduced == 0

    assert ions['CH4'].feature == 'CH4'
    assert ions['CH4'].name == 'CH4'
    assert ions['CH4'].example == 'read'
    assert ions['CH4'].unit == 'mg/L'
    assert ions['CH4'].valence == 0
    assert ions['CH4'].mw == 16.04246
    assert ions['oPO4'].mw == 'calculate'
    assert ions['DOC'].mw == 'unknown'

    assert properties['EClab'].feature == 'EClab'
    assert properties['EClab'].name == 'EC in lab'
    assert properties['EClab'].example == 'read'
    assert properties['EClab'].unit == 'm/Sm'

def test_load_pickle_without_pickle():
    ''' test to load pickle when pickle is not found '''
    # todo: mock load_pickle with invalid file (pytest mock of unittest.mock)
    atoms, ions, properties = read_write.load_pickle_as_namedtuples()
    raise NotImplementedError('mock raising error on calling pickle.load')



