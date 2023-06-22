from hgc.constants.read_write import convert_csv_to_tuples

atoms, ions, properties = convert_csv_to_tuples()

def mw(formula):
    ''' convenience function to return the molar
        weight of a molecule with `formula` '''
    try:
        if formula == 'HCO3':
            return atoms['H'].mw + atoms['C'].mw + 3*atoms['O'].mw
        elif formula == 'CO3':
            return atoms['C'].mw + 3*atoms['O'].mw
        elif formula == 'SO4':
            return atoms['S'].mw + 4*atoms['O'].mw
        elif formula == 'SO3':
            return atoms['S'].mw + 3*atoms['O'].mw
        elif formula == 'NO3':
            return atoms['N'].mw + 3*atoms['O'].mw
        elif formula == 'NO2':
            return atoms['N'].mw + 2*atoms['O'].mw
        elif formula == 'PO4':
            return atoms['P'].mw + 4*atoms['O'].mw
        else:
            return atoms[formula].mw
    except KeyError:
        raise KeyError(f'{formula} is not an element and thus not a valid key,'
                        + ' in the atoms tabel.'
                        + f'valid keys are {list(atoms.keys())}')


def units(item):
    """ returns the unit of the column of the hgc SamplesFrame """
    try:
        return atoms[item].unit
    except KeyError:
        try:
            unit_as = ions[item].phreeq_concentration_as
            if unit_as is None:
                return ions[item].unit
            else:
                return ions[item].unit + ' ' + unit_as
        except KeyError:
            try:
                return properties[item].unit
            except KeyError:
                valid_keys = (list(atoms.keys()) + list(ions.keys()) +
                              list(properties.keys()))
                raise KeyError(f'{item} is not a valid key in the atoms,'
                               + ' ions or properties tables.'
                               + f' valid keys are {valid_keys}')

def units_wt_as(item):
    try:
        return atoms[item].unit
    except KeyError:
        try:
            return ions[item].unit
        except KeyError:
            try:
                return properties[item].unit
            except KeyError:
                return None # return a None unit if the feature is excluded in HGC
