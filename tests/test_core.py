

from hgc.constants import read_write
import pandas as pd
from unittest import mock
import cloudpickle as pickle
import pytest
import hgc


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
    assert ions['CH4'].name == 'methane as mg CH4/L'
    assert ions['CH4'].example == 'read'
    assert ions['CH4'].unit == 'mg/L'
    assert ions['CH4'].valence == 0
    assert ions['CH4'].mw == 16.04246
    assert ions['PO4_ortho'].mw == 'calculate'
    assert ions['doc'].mw == 'unknown'

    assert properties['ec_lab'].feature == 'ec_lab'
    assert properties['ec_lab'].name == 'EC converted to 20°C in lab'
    assert properties['ec_lab'].example == 'read'
    assert properties['ec_lab'].unit == 'μS/cm'


def test_get_mw():
    """ assert correct molar weights are returned """
    assert hgc.mw('Hg') == 200.59
    assert hgc.mw('Fe') == 55.845
    with pytest.raises(KeyError):
        hgc.mw('NH4')


def test_get_units():
    """ assert correct units are returned """
    assert hgc.units('Hg') == 'μg/L'
    assert hgc.units('Fe') == 'mg/L'
    assert hgc.units('NH4') == 'mg/L'
    assert hgc.units('SO4') == 'mg/L as SO4'
    assert hgc.units('alkalinity') == 'mg/L as HCO3'
    assert hgc.units('eh_field') == 'mV'
    assert hgc.units('ph') == '-'

    with pytest.raises(KeyError):
        hgc.units('pH')
    with pytest.raises(KeyError):
        hgc.units('some other non sense')