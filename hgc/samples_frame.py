''' In here the extension of the pandas DataFrame is defined. It adds methods
    for validation, calculation of properties. Extending the dataframe is based on:
    # https://github.com/ContinuumIO/cyberpandas/blob/master/cyberpandas/ip_array.py
    # https://pandas.pydata.org/pandas-docs/stable/development/extending.html
'''
import logging

import numpy as np
import pandas as pd
from phreeqpython import PhreeqPython

from hgc.constants import constants



@pd.api.extensions.register_dataframe_accessor("hgc")
class SamplesFrame(object):
    ''' This class defines the extensions to a pandas dataframe
        that are specific for this package. The extension is effectuated
        by calling the class decorator `@pd.api.extensions.register_dataframe_accessor("hgc")`
        All methods and attributes defined in this class `SamplesFrame` is available
        in the namespace `hgc` of the Dataframe.

        Example

        ```
          import pandas as pd
          import hgc

          # define dataframe
          df = pd.DataFrame({'a': [1,2,3], 'b': [11,12,13]})
          # because hgc is also imported above, the namespace
          # `hgc` came available to the dataframe. This allows
          # to call the following method
          df.hgc.validate()
    '''
    def __init__(self, pandas_obj):
        self.hgc_cols = ()
        self.is_valid, self.hgc_cols = self._check_validity(pandas_obj)
        self._obj = pandas_obj
        # bind 1 phreeqpython instance to the dataframe
        self._pp = PhreeqPython()
        self._valid_atoms = constants.atoms
        self._valid_ions = constants.ions
        self._valid_properties = constants.properties

    @staticmethod
    def clean_up_phreeqpython_solutions(solutions):
        ''' This is a convenience function that removes all
            the phreeqpython solution in `solutions` from
            memory.
        '''
        _ = [s.forget() for s in solutions]


    @staticmethod
    def _check_validity(obj):
        """
        Check if the dataframe is a valid HGC dataframe

        Returns:


        Notes:
            Checks are:
            1. Are there any columns names in the recognized parameter set?
            2. Are there no strings in the recognized columns (except '<' and '>')?
            3. Are there negative concentrations in the recognized columns?

        """
        logging.info("Checking validity of DataFrame for HGC...")
        # Define allowed columns that contain concentration values
        allowed_concentration_columns = (list(constants.atoms.keys()) +
                                         list(constants.ions.keys()))
        # Define allowed columns of the hgc SamplesFrame
        allowed_hgc_columns = (list(constants.atoms.keys()) +
                               list(constants.ions.keys()) +
                               list(constants.properties.keys()))
        # # cast to lower case to reduce case sensitivity
        # allowed_concentration_columns = map(str.lower, allowed_concentration_columns)
        # allowed_hgc_columns = map(str.lower, allowed_hgc_columns)

        hgc_cols = [item for item in allowed_hgc_columns if item in obj.columns]
        neg_conc_cols = []
        invalid_str_cols = []

        # Check the columns for (in)valid values
        for col in hgc_cols:
            # check for only numeric values
            if obj[col].dtype in ('object', 'str'):
                if not all(obj[col].str.isnumeric()):
                    invalid_str_cols.append(col)
            # check for non-negative concentrations
            elif (col in allowed_concentration_columns) and (any(obj[col] < 0)):
                neg_conc_cols.append(col)

        is_valid = ((len(hgc_cols) > 0) and (len(neg_conc_cols) == 0) and (len(invalid_str_cols) == 0))

        logging.info(f"DataFrame contains {len(hgc_cols)} HGC-columns")
        if len(hgc_cols) > 0:
            logging.info(f"Recognized HGC columns are: {','.join(hgc_cols)}")

        logging.info(f"DataFrame contains {len(neg_conc_cols)} HGC-columns with negative concentrations")
        if len(neg_conc_cols) > 0:
            logging.info(f"Columns with negative concentrations are: {','.join(neg_conc_cols)}")

        logging.info(f"DataFrame contains {len(invalid_str_cols)} HGC-columns with invalid values")
        if len(invalid_str_cols) > 0:
            logging.info(f"Columns with invalid strings are: {','.join(invalid_str_cols)}. Only '<' and '>' and numeric values are allowed.")

        if is_valid:
            logging.info("DataFrame is valid")
        else:
            logging.info("DataFrame is not HGC valid. Use the 'make_valid' method to automatically resolve issues")

        return is_valid, hgc_cols


    def _replace_detection_lim(self, rule="half"):
        """
        Substitute detection limits according to one of the available
        rules. Cells that contain for example '<0.3' or '> 0.3' will be replaced
        with 0.15 and 0.45 respectively (in case of rule "half").

        Args:
            rule (str): Can be any of "half" or "at"... Rule "half" replaces cells with detection limit for half of the value.
                        Rule "at" replaces detection limit cells with the exact value of the detection limit.
        """
        for col in self.hgc_cols:
            if self._obj[col].dtype in ('object', 'str'):
                is_below_dl = self._obj[col].str.contains(pat=r'^[<]\s*\d').fillna(False)
                is_above_dl = self._obj[col].str.contains(pat=r'^[>]\s*\d').fillna(False)

                if rule == 'half':
                    self._obj.loc[is_below_dl, col] = self._obj.loc[is_below_dl, col].str.extract(r'(\d+)').astype(np.float64) / 2
                    self._obj.loc[is_above_dl, col] = self._obj.loc[is_above_dl, col].str.extract(r'(\d+)').astype(np.float64) + \
                                     (self._obj.loc[is_above_dl, col].str.extract(r'(\d+)').astype(np.float64) / 2)
                elif rule == 'on':
                    self._obj[col] = self._obj.loc[col].str.extract(r'(\d+)').astype(np.float64)


    def _replace_negative_concentrations(self):
        """
        Replace any negative concentrations with 0.
        """
        # Get all columns that represent chemical compounds
        # Replace negatives with 0
        for col in self.hgc_cols:
            self._obj.loc[self._obj[col] < 0, col] = 0


    def _cast_datatypes(self):
        """
        Convert all HGC-columns to their correct data type.
        """
        for col in self.hgc_cols:
            if self._obj[col].dtype in ('object', 'str'):
                self._obj[col] = pd.to_numeric(self._obj[col], errors='coerce')


    def consolidate(self, use_ph='field', use_ec='lab', use_so4='ic', use_o2='field', use_temp='field', merge_on_na=False,
                    inplace=True):
        """
        Consolidate parameters measured with different methods to one single parameter

        Kwargs:
            use_ph (str): Which pH to use? Can be 'field' or 'lab' or None; not consolidated when None is chosen. Default 'field'
            use_ec (str): Which EC to use? Similar to `use_ph`. Default 'lab'
            use_so4 (str): Which SO4 to use?  Similar to `use_ph`. Default 'ic'
            use_o2 (str): Which O2 to use? Similar to `use_ph`. Default 'field'
            merge_on_na (str): Fill NaN's from one measurement method with measurements from other method
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        if inplace is False:
            raise NotImplementedError('inplace=False is not (yet) implemented. It will become the default though')

        param_mapping = {
            'ph': use_ph,
            'ec': use_ec,
            'SO4': use_so4,
            'O2': use_o2,
            'temp': use_temp
        }

        for param, method in param_mapping.items():
            if not method:
                # user did not specify source, ignore
                continue

            if not isinstance(method, str):
                ValueError(f"Invalid method {method} for parameter {param}. Arg should be a string.")

            if param in self._obj.columns:
                logging.info(f"Parameter {param} already present in DataFrame, ignoring. Remove column manually to enable consolidation.")
                continue

            source = f"{param}_{method}"
            if source in self._obj.columns:
                source_val = self._obj[source]
                if any(np.isnan(source_val)):
                    raise ValueError('Nan value for column {source}')

                self._obj[param] = np.NaN
                self._obj[param].fillna(source_val, inplace=True)


                if merge_on_na:
                    raise NotImplementedError('merge_on_na is True is not implemented (yet).')

                # Drop source columns
                suffixes = ('_field', '_lab', '_ic')
                cols = [param + suffix for suffix in suffixes]
                self._obj.drop(columns=cols, errors='ignore')

            else:
                raise ValueError(f"Column {str(source)} not present in DataFrame")


    def get_ratios(self):
        """
        Calculate all common ratios. Return as separate dataframe.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        df_ratios = pd.DataFrame()

        ratios = {
            'cl_to_br': ['cl', 'br'],
            'cl_to_na': ['cl', 'na'],
            'ca_to_mg': ['cl', 'mg'],
            'ca_to_sr': ['ca', 'sr'],
            'fe_to_mn': ['fe', 'mn'],
            'hco3_to_ca': ['hco3', 'ca'],
            '2h_to_18o': ['2h', '18o'],
            'suva': ['uva254', 'doc'],
            'hco3_to_sum_anions': ['hco3', 'anions'],
            'hco3_to_ca_and_mg': ['hco3', 'ca', 'mg'],
            'monc': ['cod', 'fe', 'no2', 'doc'],
            'cod_to_doc': ['cod', 'fe', 'no2', 'doc']
        }

        for ratio, constituents in ratios.items():
            has_cols = [const in self._obj.columns for const in constituents]
            if all(has_cols):
                if len(constituents) == 2:
                    df_ratios[ratio] = self._obj[constituents[0]] / self._obj[constituents[1]]
                elif ratio == 'hco3_to_ca_and_mg':
                    df_ratios[ratio] = self._obj['hco3'] / (self._obj['ca'] + self._obj['mg'])
                elif ratio == 'monc':
                    df_ratios[ratio] = 4 - 1.5 * (self._obj['cod'] - 0.143 * self._obj['fe'] - 0.348 * self._obj['no2']) / (3.95 * self._obj['doc'])
                elif ratio == 'cod_to_doc':
                    df_ratios[ratio] = ((0.2532 * self._obj['cod'] - 0.143 * self._obj['fe'] - 0.348 * self._obj['no2']) / 32) / (self._obj['doc'] / 12)
            else:
                missing_cols = [i for (i, v) in zip(constituents, has_cols) if not v]
                logging.info(f"Cannot calculate ratio {ratio} since columns {','.join(missing_cols)} are not present.")

        return df_ratios


    def fillna_concentrations(self, how="phreeqc"):
        """
        Calculate missing concentrations based on the charge balance.

        Args:
            how (str): any of "phreeqc" or "analytic"
        """
        raise NotImplementedError


    def fillna_ec(self):
        """
        Calculate missing Electrical Conductivity measurements using
        known anions and cations.
        """
        raise NotImplementedError


    def make_valid(self):
        """
        Run some tests to validate the object obj (a
        Pandas dataframe).
        """
        # Conduct conversions here. If they fail, raise error (e.g. when not a single valid column is present)
        # Important: order is important, first convert strings to double, then replace negative concentrations
        self._replace_detection_lim()
        self._cast_datatypes()
        self._replace_negative_concentrations()
        self.is_valid = True

    def get_phreeq_columns(self):
        ''' returns the columns from the dataframe that might be used
            by phreeq python '''
        df = self._obj

        atom_columns = set(self._valid_atoms).intersection(df.columns)
        ion_columns = set(self._valid_ions).intersection(df.columns)
        prop_columns = set(self._valid_properties).intersection(df.columns)
        phreeq_columns = list(atom_columns.union(ion_columns).union(prop_columns))

        # check whether ph and temp are in the list
        if 'ph' not in phreeq_columns:
            raise ValueError('The required column ph is missing in the dataframe. ' +
                             'Add a column ph manually or consolidate ph_lab or ph_field ' +
                             'to ph by running the method DataFrame.hgc.consolidate().')
        if 'temp' not in phreeq_columns:
            raise ValueError('The required column temp is missing in the dataframe. ' +
                             'Add a column temp manually or consolidate temp_lab or temp_field ' +
                             'to temp by running the method DataFrame.hgc.consolidate().')
        if 'doc' in phreeq_columns:
            logging.info('DOC column found in samples frame while using phreeqc as backend; influence of DOC on any value calculated using phreeqc is ignored.')


        return phreeq_columns

    def get_phreeqpython_solutions(self, equilibrate_with='Na', append=False):
        ''' return a series of phreeqpython solutions derived from the (row)data in the SamplesFrame.

            Args:
                equilibrate_with (str): the ion with which to add to achieve charge equilibrium in the solutions (default: 'Na')
                append (bool): whether the returned series is added to the DataFrame or not (default: False)
             '''
        if append is True:
            raise NotImplementedError('appending a columns to SamplesFrame is not implemented yet')

        if equilibrate_with is None:
            raise ValueError('Invalid value for equilibrate_with')

        pp = self._pp
        df = self._obj.copy()

        phreeq_cols = self.get_phreeq_columns()
        nitrogen_cols = set(phreeq_cols).intersection({'NO2', 'NO3', 'N', 'N_tot_k'})
        phosphor_cols = set(phreeq_cols).intersection({'PO4', 'P', 'P_ortho', 'PO4_total'})

        if len(nitrogen_cols) > 1:
            # check if nitrogen is defined in more than one column (per sample)
            duplicate_nitrogen = df[nitrogen_cols].apply(lambda x: sum(x > 0) > 1, axis=1)

            if sum(duplicate_nitrogen) > 0:
                logging.info('Some rows have more than one column defining N. ' +
                             'Choose N over NO2 over NO3')

            for index, row in df.loc[duplicate_nitrogen].iterrows():
                for col in ['N', 'NO2', 'NO3']:
                    if col in nitrogen_cols:
                        if row[col] > 0:
                            df.loc[index, list(nitrogen_cols-{col})] = 0.
                            break

        if len(phosphor_cols) > 1:
            # check if phosphor is defined in more than one column (per sample)
            duplicate_phosphor = df[phosphor_cols].apply(lambda x: sum(x > 0) > 1, axis=1)

            if sum(duplicate_phosphor) > 0:
                logging.info('Some rows have more than one column defining P. Choose P over PO4')

            for index, row in df.loc[duplicate_phosphor].iterrows():
                for col in ['P', 'PO4']:
                    if col in phosphor_cols:
                        if row[col] > 0:
                            df.loc[index, list(phosphor_cols-{col})] = 0.
                            break

        solutions = pd.Series(index=df.index, dtype='object')
        for index, row in df[phreeq_cols].iterrows():
            _sol = {'units': 'mg/l'}
            for col in row.index:

                try:
                    atom = self._valid_atoms[col]
                    phreeq_name = atom.feature
                    phreeq_as = ''
                    phreeq_unit = atom.unit
                    value = row[col]
                except KeyError:
                    try:
                        ion = self._valid_ions[col]
                        phreeq_name = ion.phreeq_name
                        phreeq_as = ion.phreeq_concentration_as
                        phreeq_unit = ion.unit
                        if phreeq_as is None:
                            phreeq_as = ''
                        value = row[col]
                    except KeyError:
                        property_ = self._valid_properties[col]
                        phreeq_name = property_.phreeq_name
                        phreeq_as = ''
                        phreeq_unit = ''
                        value = row[col]

                if (value > 0) and (phreeq_name is not None):
                    # Phreeq_name is None indicates that the atom/ion/property
                    # is not a valid property for a phreeqc simulation and the key
                    # should therefore not be added to the phreeqpython solutions
                    phreeq_name = phreeq_name.strip()
                    phreeq_unit = phreeq_unit.strip()
                    phreeq_as = phreeq_as.strip()
                    _sol[phreeq_name] = f"{value} {phreeq_unit} {phreeq_as}"

            try:
                # append the keyword charge to the compound that is used to charge balance
                _sol[equilibrate_with] = _sol[equilibrate_with] + ' charge'
            except KeyError:
                logging.info(f'{equilibrate_with} not found in solution while it is selected to balance charge with. Starts initial guess with 20 mg/L to balance charge.')
                _sol[equilibrate_with] = '20. mg/L charge'

            try:
                solutions[index] = pp.add_solution(_sol)
            except Exception as error:
                logging.info(error)
                raise ValueError(f'Something went wrong with the phreeqc calculation with index {index} from the DataFrame. PHREEQC returned: {error}')


        return solutions

    def get_saturation_index(self, mineral_or_gas, use_phreeqc=True, inplace=False, **kwargs):
        ''' adds or returns the saturation index of a mineral or the partial pressure of a gas using phreeqc.

           Args:
                mineral_or_gas (str): the name of the mineral of which the SI needs to be calculated or
               use_phreeqc (bool): whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                                   or partial pressure
               inplace (bool): whether to return a new dataframe with the column added or change the current dataframe itself

           Returns:
                Series: with values of si for each row of the input dataframe '''
        if inplace:
            raise NotImplementedError('inplace argument is not yet implemented.')
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')


        solutions = self.get_phreeqpython_solutions(**kwargs)
        saturation_index = [s.si(mineral_or_gas) if s is not None else None for s in solutions]

        self.clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        return pd.Series(saturation_index, index=self._obj.index)

    def get_specific_conductance(self, use_phreeqc=True, **kwargs):
        ''' returns the specific conductance (sc) of a water sample using phreeqc. sc is
            also known as electric conductivity (ec) or egv measurements.

           Args:
               use_phreeqc (bool): whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                                   or partial pressure

           Returns:
                Series: with values of specific conductance for each row of the input dataframe '''
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')

        # create phreeqpython solutions
        solutions = self.get_phreeqpython_solutions(**kwargs)
        # extract sc from them
        specific_conductance = [s.sc for s in solutions]
        # clean up
        self.clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        return pd.Series(specific_conductance, index=self._obj.index)
