from hgc.constants.read_write import load_pickle_as_namedtuples

atoms, ions, properties = load_pickle_as_namedtuples()

def mw(formula):
    ''' convenience function to return the molar
        weight of a molecule with `formula` '''
    try:
        return atoms[formula].mw
    except KeyError:
        raise KeyError(f'{formula} is not an element and thus not a valid key,'
                        + ' in the atoms tabel.' +
                        + f'valid keys are {atoms.keys()}')


def units(item):
    """ returns the unit of the column of the hgc SamplesFrame """
    try:
        unit_as = atoms[item].phreeq_concentration_as
        return atoms[item].units + unit_as
    except KeyError:
        try:
            unit_as = ions[item].phreeq_concentration_as
            return ions[item].units + unit_as
        except KeyError:
            try:
                unit_as = ions[item].phreeq_concentration_as
                return properties[item].units + unit_as
            except KeyError:
                valid_keys = (list(atoms.keys()) + list(ions.keys()) +
                              list(properties.keys()))
                raise KeyError(f'{item} is not a valid key in the atoms,'
                               + ' ions or properties tables.'
                               + f' valid keys are {valid_keys}')



