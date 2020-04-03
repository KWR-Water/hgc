

from hgc.constants import read_write
import pandas as pd
from unittest import mock
import cloudpickle as pickle
import pytest


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
    assert ions['PO4_ortho'].mw == 'calculate'
    assert ions['doc'].mw == 'unknown'

    assert properties['ec_lab'].feature == 'ec_lab'
    assert properties['ec_lab'].name == 'EC in lab'
    assert properties['ec_lab'].example == 'read'
    assert properties['ec_lab'].unit == 'm/Sm'



