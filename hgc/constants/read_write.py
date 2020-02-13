''' Import csv files that contain information on the constants required by HGC.
    This will be transformed to a
    pickle file with the same information in a dict of named tuples '''
# import pickle
import cloudpickle as pickle
from collections import namedtuple
from pathlib import Path
from pyparsing import Word, Optional, OneOrMore, Group
import numpy as np

import pandas as pd

PATH = Path.cwd() / 'hgc' / 'constants'
PICKLE_PATH_FILE = PATH / 'constants.pickle'

def _formulaParser(formula, calculate_or_not, atoms):
    ''' parses the chemical formula if calculate_or_not
        equals `calculate`, otherwise, do nothing. Use
        the molecular weight from atoms dict. '''

    if (calculate_or_not != 'calculate') or (formula in ['N_tot_k', 'PO4_ortho', 'SO4_ic', 'alkalinity']):
        return calculate_or_not

    # define some strings to use later, when describing valid lists
    # of characters for chemical symbols and numbers
    caps = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowers = caps.lower()
    digits = "0123456789"
    brackets = "[]{}()"

    if any([_ in formula for _ in brackets]):
        raise Exception('Not implemented with brackets in formula string')

    # Version 1
    # Define grammar for a chemical formula
    # - an element is a Word, beginning with one of the characters in caps,
    #   followed by zero or more characters in lowers
    # - an integer is a Word composed of digits
    # - an elementRef is an element, optionally followed by an integer - if
    #   the integer is omitted, assume the value "1" as a default; these are
    #   enclosed in a Group to make it easier to walk the list of parsed
    #   chemical symbols, each with its associated number of atoms per
    #   molecule
    # - a chemicalFormula is just one or more elementRef's
    # Version 3 - Compute partial molecular weight per element, simplifying
    # summing
    # No need to redefine grammar, just define parse action function, and
    # attach to elementRef

    # Auto-convert integers, and add results names
    def convertIntegers(tokens):
        return int(tokens[0])

    element = Word( caps, lowers )
    integer = Word( digits ).setParseAction( convertIntegers )
    elementRef = Group( element("symbol") + Optional( integer, default=1 )("qty") )

    chemicalFormula = OneOrMore( elementRef )

    def computeElementWeight(tokens):
        element = tokens[0]
        element["weight"] = atoms[element.symbol] * element.qty

    elementRef.setParseAction(computeElementWeight)

    formulaData = chemicalFormula.parseString(formula)

    # compute molecular weight
    mw = sum( [ element.weight for element in formulaData ] )

    return mw

def df_to_dict_of_tuples(df, tuple_name='Row'):
    ''' changes dataframe to dictionary of tuples '''
    Row = namedtuple(tuple_name, df.columns)
    tuples_dict = {}
    for row in df.itertuples():
        tuple_ = Row(*row[1:])
        tuples_dict[tuple_.feature] = tuple_
    return tuples_dict


def convert_csv_to_tuples():
    ''' Convert the definitions in CSV files to one dict of named tuples and
        write that to constants.py
    '''
    default_read_csv_args = dict(na_values=[None, 'None'], comment='#')
    atoms = pd.read_csv(PATH / 'atoms.csv', **default_read_csv_args)
    ions = pd.read_csv(PATH / 'ions_and_organic_compounds.csv', **default_read_csv_args)
    properties = pd.read_csv(PATH / 'other_than_concentrations.csv', **default_read_csv_args)

    # convert nan to None
    atoms = atoms.where((pd.notnull(atoms)), None)
    ions = ions.where((pd.notnull(ions)), None)
    properties = properties.where((pd.notnull(properties)), None)

    rename_columns = {'molar_weight': 'mw', 'predominant_oxidized_state': 'oxidized', 'predominant_reduced_state': 'reduced'}

    atoms = atoms.rename(columns=rename_columns)
    ions = ions.rename(columns=rename_columns)
    properties = properties.rename(columns=rename_columns)

    # remove leading and trailing white spaces
    # atoms.loc[:, ['feature', 'name', 'unit']] = atoms.loc[:, ['feature', 'name', 'unit']].applymap(lambda x: x.strip())
    # ions.loc[:, ['feature', 'name', 'unit']] = ions.loc[:, ['feature', 'name', 'unit']].applymap(lambda x: x.strip())
    # properties.loc[:, ['feature', 'name', 'unit', 'example']] = properties.loc[:, ['feature', 'name', 'unit', 'example']].applymap(lambda x: x.strip())

    # create a dict with atoms as key and mw as value to be used to parse the molecular formula in ions['feature']
    atoms_dict = atoms.set_index(['feature'])['mw'].to_dict()
    ions['mw'] = ions.apply(lambda x: _formulaParser(x['feature'], x['mw'], atoms_dict), axis=1)

    atoms_dict = df_to_dict_of_tuples(atoms, tuple_name='Atom')
    ions_dict = df_to_dict_of_tuples(ions, tuple_name='Ion')
    properties_dict = df_to_dict_of_tuples(properties, tuple_name='Properties')

    return atoms_dict, ions_dict, properties_dict

def csv_to_pickle():
    atoms, ions, properties = convert_csv_to_tuples()
    with open(PICKLE_PATH_FILE, 'wb') as file_out:
        pickle.dump((atoms, ions, properties), file_out)

def load_pickle_as_namedtuples():
    try:
        with open(PICKLE_PATH_FILE, 'rb') as file_in:
            atoms, ions, properties = pickle.load(file_in)
    except FileNotFoundError:
        try:
            atoms, ions, properties = convert_csv_to_tuples()
        except FileNotFoundError:
            raise FileNotFoundError('Required CSV with constant definition cannot be found')

    return atoms, ions, properties


