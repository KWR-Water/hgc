"""
The SamplesFrame class is an extended Pandas DataFrame, offering additional methods
for validation of hydrochemical data, calculation of relevant ratios and classifications.
"""
import logging

import numpy as np
import pandas as pd
from phreeqpython import PhreeqPython

from hgc.constants import constants


@pd.api.extensions.register_dataframe_accessor("hgc")
class SamplesFrame(object):
    """
    DataFrame with additional hydrochemistry-specific methods.
    All HGC methods and attributes defined in this class are available
    in the namespace 'hgc' of the Dataframe.

    Examples
    --------
    To use HGC methods, we always start from a Pandas DataFrame::

        import pandas as pd
        import hgc

        # We start off with an ordinary DataFrame
        df = pd.DataFrame({'Cl': [1,2,3], 'Mg': [11,12,13]})

        # Since we imported hgc, the HGC-methods become available
        # on the DataFrame. This allows for instance to use HGC's
        # validation function
        df.hgc.is_valid
        False
        df.hgc.make_valid()
    """

    def __init__(self, pandas_obj):
        self.hgc_cols = ()
        self.is_valid, self.hgc_cols = self._check_validity(pandas_obj)
        self._obj = pandas_obj
        self._pp = PhreeqPython() # bind 1 phreeqpython instance to the dataframe
        self._valid_atoms = constants.atoms
        self._valid_ions = constants.ions
        self._valid_properties = constants.properties

    @staticmethod
    def _clean_up_phreeqpython_solutions(solutions):
        """
        This is a convenience function that removes all
        the phreeqpython solution in `solutions` from
        memory.

        Parameters
        ----------
        solutions : list
            python list containing of phreeqpython solutions

        """
        _ = [s.forget() for s in solutions]


    @staticmethod
    def _check_validity(obj):
        """
        Check if the dataframe is a valid HGC dataframe

        Notes
        -----
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
        # cast to lowercase to reduce case sensitivity
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


    def _make_input_df(self, cols_req):
        """
        Make input DataFrame for calculations. This DataFrame contains columns for each required parameter,
        which is 0 in case the parameter is not present in original HGC frame.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        df_in = pd.DataFrame(columns=cols_req)
        for col_req in cols_req:
            if col_req in self._obj:
                df_in[col_req] = self._obj[col_req]
            else:
                logging.info(f"Column {col_req} is not present in DataFrame, assuming concentration 0 for this compound for now.")

        return df_in


    def _replace_detection_lim(self, rule="half"):
        """
        Substitute detection limits according to one of the available
        rules. Cells that contain for example '<0.3' or '> 0.3' will be replaced
        with 0.15 and 0.45 respectively (in case of rule "half").

        Parameters
        ----------
        rule : str, default 'half'
            Can be any of "half" or "at"... Rule "half" replaces cells with detection limit for half of the value.
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


    def consolidate(self, use_ph='field', use_ec='lab', use_so4='ic', use_o2='field',
                    use_temp='field', merge_on_na=False, inplace=True):
        """
        Consolidate parameters measured with different methods to one single parameter.

        Parameters such as EC and pH are frequently measured both in the lab and field,
        and SO4 and PO4 are frequently measured both by IC and ICP-OES. Normally we prefer the
        field data for EC and pH, but ill calibrated sensors or tough field circumstances may
        prevent these readings to be superior to the lab measurement. This method allows for quick
        selection of the preferred measurement method for each parameter and select that for further analysis.

        For each consolidated parameter HGC adds a new column that is either filled with the lab measurements or the field
        measurements. It is also possible to fill it with the preferred method, and fill remaining NaN's with
        measurements gathered with the other possible method.

        Parameters
        ----------
        use_ph : {'lab', 'field', None}, default 'field'
            Which pH to use? Ignored if None.
        use_ec : {'lab', 'field', None}, default 'lab'
            Which EC to use?
        use_so4 : {'ic', 'field', None}, default 'ic'
            Which SO4 to use?
        use_o2 : {'lab', 'field', None}, default 'field'
            Which O2 to use?
        merge_on_na : bool, default False
            Fill NaN's from one measurement method with measurements from other method.
        inplace : bool, default True
            Modify SamplesFrame in place?


        Raises
        ------
            ValueError: if one of the `use_` parameters is set to a column that is not in the dataframe
                        *or* if one of the default parameters is not in the dataframe while it is not
                        set to None.
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
                raise ValueError(f"Column {source} not present in DataFrame. Use " +
                                 f"use_{param.lower()}=None to explicitly ignore consolidating " +
                                 f"this column.")


    def get_bex(self, watertype="G"):
        """
        Get Base Exchange Index (meq/L). By default this is the BEX without dolomite.

        Parameters
        ----------
        watertype : {'G', 'P'}, default 'G'
            Watertype (Groundwater or Precipitation)

        Returns
        -------
        pandas.Series
            Series with for each row in the original.
        """
        cols_req = ('Na', 'K', 'Mg', 'Cl')
        df = self._make_input_df(cols_req)
        df_out = pd.DataFrame()

        #TODO: calculate alphas on the fly from SMOW constants
        alpha_na = 0.556425145165362 # ratio of Na to Cl in SMOW
        alpha_k = 0.0206 # ratio of K to Cl in SMOW
        alpha_mg = 0.0667508204998738 # ratio of Mg to Cl in SMOW

        only_p_and_t = True

        if watertype == "P" and only_p_and_t:
            df_out['Na_nonmarine'] = df['Na'] - 1.7972 * alpha_na*df['Na']
            df_out['K_nonmarine'] = df['K'] - 1.7972 * alpha_k*df['Na']
            df_out['Mg_nonmarine'] = df['Mg'] - 1.7972 * alpha_mg*df['Na']
        else:
            df_out['Na_nonmarine'] = df['Na'] - alpha_na*df['Cl']
            df_out['K_nonmarine'] = df['K'] - alpha_k*df['Cl']
            df_out['Mg_nonmarine'] = df['Mg'] - alpha_mg*df['Cl']

        df_out['bex'] = df_out['Na_nonmarine']/22.99 + df_out['K_nonmarine']/39.098 + df_out['Mg_nonmarine']/12.153

        return df_out['bex']


    def get_ratios(self):
        """
        Calculate common hydrochemical ratios, will ignore any ratios
        in case their constituents are not present in the SamplesFrame.

        Notes
        -----
        HGC will attempt to calculate the following ratios:
         * Cl/Br
         * Cl/Na
         * Cl/Mg
         * Ca/Sr
         * Fe/Mn
         * HCO3/Ca
         * 2H/18O
         * SUVA: UVA254/DOC
         * HCO3/Sum of anions
         * HCO3/Sum of Ca and Mg
         * MONC
         * COD/DOC

        Returns
        -------
        pandas.DataFrame
            DataFrame with computed ratios.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        df_ratios = pd.DataFrame()

        ratios = {
            'cl_to_br': ['Cl', 'Br'],
            'cl_to_na': ['Cl', 'Na'],
            'ca_to_mg': ['Cl', 'Mg'],
            'ca_to_sr': ['Ca', 'Sr'],
            'fe_to_mn': ['Fe', 'Mn'],
            'hco3_to_ca': ['HCO3', 'Ca'],
            '2h_to_18o': ['2H', '18O'],
            'suva': ['uva254', 'doc'],
            'hco3_to_sum_anions': ['HCO3', 'sum_anions'],
            'hco3_to_ca_and_mg': ['HCO3', 'Ca', 'Mg'],
            'monc': ['cod', 'Fe', 'NO2', 'doc'],
            'cod_to_doc': ['cod', 'Fe', 'NO2', 'doc']
        }

        for ratio, constituents in ratios.items():
            has_cols = [const in self._obj.columns for const in constituents]
            if all(has_cols):
                if ratio == 'hco3_to_sum_anions':
                    df_ratios[ratio] = self._obj['HCO3'] / self.get_sum_anions_stuyfzand()
                elif ratio == 'hco3_to_ca_and_mg':
                    df_ratios[ratio] = self._obj['HCO3'] / (self._obj['Ca'] + self._obj['Mg'])
                elif ratio == 'monc':
                    df_ratios[ratio] = 4 - 1.5 * (self._obj['cod'] - 0.143 * self._obj['Fe'] - 0.348 * self._obj['NO2']) / (3.95 * self._obj['doc'])
                elif ratio == 'cod_to_doc':
                    df_ratios[ratio] = ((0.2532 * self._obj['cod'] - 0.143 * self._obj['Fe'] - 0.348 * self._obj['NO2']) / 32) / (self._obj['doc'] / 12)
                else:
                    df_ratios[ratio] = self._obj[constituents[0]] / self._obj[constituents[1]]
            else:
                missing_cols = [i for (i, v) in zip(constituents, has_cols) if not v]
                logging.info(f"Cannot calculate ratio {ratio} since columns {','.join(missing_cols)} are not present.")

        return df_ratios


    def get_stuyfzand_water_type(self):
        """
        Get Stuyfzand water type. This water type classification contains
        5 components: Salinity, Alkalinity, Dominant Cation, Dominant Anion and Base Exchange Index.
        This results in a classification such as for example 'F3CaMix+'.

        Returns
        -------
        pandas.Series
            Series with Stuyfzand water type of each row in original SamplesFrame.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        # Create input dataframe containing all required columns
        # Inherit column values from HGC frame, assume 0 if column
        # is not present
        cols_req = ('Al', 'Ba', 'Br', 'Ca', 'Cl', 'Co', 'Cu', 'doc', 'F', 'Fe', 'HCO3', 'K', 'Li', 'Mg', 'Mn', 'Na', 'Ni', 'NH4', 'NO2', 'NO3', 'Pb', 'PO4', 'ph', 'SO4', 'Sr', 'Zn')
        df_in = self._make_input_df(cols_req)
        df_out = pd.DataFrame(index=df_in.index)

        # Salinity
        df_out['swt_s'] = 'G'
        df_out.loc[df_in['Cl'] > 5, 'swt_s'] = 'g'
        df_out.loc[df_in['Cl'] > 30, 'swt_s'] = 'F'
        df_out.loc[df_in['Cl'] > 150, 'swt_s'] = 'f'
        df_out.loc[df_in['Cl'] > 300, 'swt_s'] = 'B'
        df_out.loc[df_in['Cl'] > 1000, 'swt_s'] = 'b'
        df_out.loc[df_in['Cl'] > 10000, 'swt_s'] = 'S'
        df_out.loc[df_in['Cl'] > 20000, 'swt_s'] = 'H'

        #Alkalinity
        df_out['swt_a'] = '*'
        df_out.loc[df_in['HCO3'] > 31, 'swt_a'] = '0'
        df_out.loc[df_in['HCO3'] > 61, 'swt_a'] = '1'
        df_out.loc[df_in['HCO3'] > 122, 'swt_a'] = '2'
        df_out.loc[df_in['HCO3'] > 244, 'swt_a'] = '3'
        df_out.loc[df_in['HCO3'] > 488, 'swt_a'] = '4'
        df_out.loc[df_in['HCO3'] > 976, 'swt_a'] = '5'
        df_out.loc[df_in['HCO3'] > 1953, 'swt_a'] = '6'
        df_out.loc[df_in['HCO3'] > 3905, 'swt_a'] = '7'

        #Dominant cation
        s_sum_cations = self.get_sum_cations_stuyfzand()

        is_no_domcat = (df_in['Na']/22.99 + df_in['K']/39.1 + df_in['NH4']/18.04) < (s_sum_cations/2)
        df_out.loc[is_no_domcat, 'swt_domcat'] = ""

        is_domcat_nh4 = ~is_no_domcat & (df_in['NH4']/18.04 > (df_in['Na']/22.99 + df_in['K']/39.1))
        df_out.loc[is_domcat_nh4, 'swt_domcat'] = ""

        is_domcat_na = ~is_no_domcat & ~is_domcat_nh4 & (df_in['Na']/22.99 > df_in['K']/39.1)
        df_out.loc[is_domcat_na, 'swt_domcat'] = "Na"

        is_domcat_k = ~is_no_domcat & ~is_domcat_nh4 & ~is_domcat_na
        df_out.loc[is_domcat_k, 'swt_domcat'] = "K"

        # Dominant anion
        s_sum_anions = self.get_sum_anions_stuyfzand()

        # TODO: consider renaming doman to dom_an or dom_anion
        is_doman_cl = (df_in['Cl']/35.453 > s_sum_anions/2)
        df_out.loc[is_doman_cl, 'swt_doman'] = "Cl"

        is_doman_hco3 = ~is_doman_cl & (df_in['HCO3']/61.02 > s_sum_anions/2)
        df_out.loc[is_doman_hco3, 'swt_doman'] = "HCO3"

        is_doman_so4_or_no3 = ~is_doman_cl & ~is_doman_hco3 & (2*df_in['SO4']/96.06 + df_in['NO3']/62. > s_sum_anions/2)
        is_doman_so4 = (2*df_in['SO4']/96.06 > df_in['NO3']/62.)
        df_out.loc[is_doman_so4_or_no3 & is_doman_so4, 'swt_doman'] = "SO4"
        df_out.loc[is_doman_so4_or_no3 & ~is_doman_so4, 'swt_doman'] = "NO3"

        is_mix = ~is_doman_cl & ~is_doman_hco3 & ~is_doman_so4_or_no3
        df_out.loc[is_mix, 'swt_doman'] = "Mix"

        # Base Exchange Index
        s_bex = self.get_bex()
        threshold1 = 0.5 + 0.02*df_in['Cl']/35.453
        threshold2 = -0.5-0.02*df_in['Cl']/35.453
        is_plus = (s_bex > threshold1) & (s_bex > 1.5*(s_sum_cations-s_sum_anions))
        df_out.loc[is_plus, 'swt_bex'] = '+'

        is_minus = ~is_plus & (s_bex < threshold2) & (s_bex < 1.5*(s_sum_cations-s_sum_anions))
        df_out.loc[is_minus, 'swt_bex'] = '-'

        is_neutral = ~is_plus & ~is_minus & ((s_bex > threshold2) & (s_bex < threshold1) & (s_sum_cations == s_sum_anions)) | \
                     ((s_bex > threshold2) & \
                     ((abs(s_bex + threshold1*(s_sum_cations-s_sum_anions))/abs(s_sum_cations-s_sum_anions)) > abs(1.5*(s_sum_cations-s_sum_anions))))

        df_out.loc[is_neutral, 'swt_bex'] = 'o'

        is_none = ~is_plus & ~is_minus & ~is_neutral
        df_out.loc[is_none, 'swt_bex'] = ''

        #Putting it all together
        df_out['swt'] = df_out['swt_s'].str.cat(df_out[['swt_a', 'swt_domcat', 'swt_doman', 'swt_bex']])

        return df_out['swt']


    def fillna_concentrations(self, how="phreeqc"):
        """
        Calculate missing concentrations based on the charge balance.

        Parameters
        ----------
        how : {'phreeqc', 'analytic'}, default 'phreeqc'
            Method to compute missing concentrations.
        """
        raise NotImplementedError()


    def fillna_ec(self, use_phreeqc=True):
        """
        Calculate missing Electrical Conductivity measurements using
        known anions and cations.
        """
        if use_phreeqc:
            # use get_specific_conductance method on
            # all N/A rows of EC columns
            raise NotImplementedError()
        else:
            raise NotImplementedError()


    def make_valid(self):
        """
        Try to convert the DataFrame into a valid HGC-SamplesFrame.
        """
        # Conduct conversions here. If they fail, raise error (e.g. when not a single valid column is present)
        # Important: order is important, first convert strings to double, then replace negative concentrations
        self._replace_detection_lim()
        self._cast_datatypes()
        self._replace_negative_concentrations()
        self.is_valid = True


    def get_sum_anions_stuyfzand(self):
        """
        Calculate sum of anions according to the Stuyfzand method.

        Returns
        -------
        pandas.Series
            Series with sum of cations for each row in SamplesFrame.
        """
        cols_req = ('Br', 'Cl', 'doc', 'F', 'HCO3', 'NO2', 'NO3', 'PO4', 'SO4', 'ph')
        df_in = self._make_input_df(cols_req)
        s_sum_anions = pd.Series(index=df_in.index)

        k_org = 10**(0.039*df_in['ph']**2 - 0.9*df_in['ph']-0.96) # HGC manual equation 3.5
        a_org = k_org * df_in['doc'] / (100*k_org + (10**-df_in['ph'])/10) # HGC manual equation 3.4A
        sum_ions = (df_in['Cl']/35.453 + df_in['SO4']/48.03 + df_in['HCO3']/61.02 + df_in['NO3']/62. +
                    df_in['NO2']/46.0055 + df_in['F']/18.9984 + df_in['Br']/79904 + df_in['PO4']/94.971) / (1 + 10**(df_in['ph']-7.21))

        is_add_a_org = a_org > df_in['HCO3']/61.02

        s_sum_anions.loc[is_add_a_org] = sum_ions + a_org
        s_sum_anions.loc[~is_add_a_org] = sum_ions

        return s_sum_anions


    def get_sum_cations_stuyfzand(self):
        """
        Calculate sum of cations according to the Stuyfzand method.

        Returns
        -------
        pandas.Series
            Sum of all cations for each row in original SamplesFrame.
        """
        cols_req = ('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn')
        df_in = self._make_input_df(cols_req)

        if 'Ca' == 0 and 'Mg' == 0:
            abac = 2*'H_tot'
        else:
            abac = 0

        s_sum_cations = 10**-(df_in['ph']-3) + \
                    df_in['Na']/22.99 + \
                    df_in['K']/39.1 + \
                    df_in['Ca']/20.04 + \
                    df_in['Mg']/12.156 + \
                    df_in['Fe']/(55.847/2) + \
                    df_in['Mn']/(54.938/2) + \
                    df_in['NH4']/18.04 + \
                    df_in['Al']/(26982/3) + \
                    abac + \
                    df_in['Ba']/137327 + \
                    df_in['Co']/58933 + \
                    df_in['Cu']/(63546/2) + \
                    df_in['Li']/6941 + \
                    df_in['Ni']/58693 + \
                    df_in['Pb']/207200 + \
                    df_in['Sr']/87620 + \
                    df_in['Zn']/65380

        return s_sum_cations


    def _get_phreeq_columns(self):
        """
        Returns the columns from the DataFrame that might be used
        by PhreeqPython.

        Returns
        -------
        list
            Usable PhreeqPython columns
        """
        df = self._obj

        atom_columns = set(self._valid_atoms).intersection(df.columns)
        ion_columns = set(self._valid_ions).intersection(df.columns)
        prop_columns = set(self._valid_properties).intersection(df.columns)
        phreeq_columns = list(atom_columns.union(ion_columns).union(prop_columns))

        nitrogen_cols = set(phreeq_columns).intersection({'NO2', 'NO3', 'N', 'N_tot_k'})
        phosphor_cols = set(phreeq_columns).intersection({'PO4', 'P', 'P_ortho', 'PO4_total'})

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


        return phreeq_columns

    def get_phreeqpython_solutions(self, equilibrate_with='Na', append=False):
        """
        Return a series of `phreeqpython solutions <https://github.com/Vitens/phreeqpython>`_ derived from the (row)data in the SamplesFrame.

        Parameters
        ----------
        equilibrate_with : str, default 'Na'
            Ion to add for achieving charge equilibrium in the solutions.
        append : bool, default False
            Whether the returned series is added to the DataFrame or not (default: False).

        Returns
        -------
        pandas.Series
        """
        if append is True:
            raise NotImplementedError('appending a columns to SamplesFrame is not implemented yet')

        if equilibrate_with is None:
            raise NotImplementedError('Equilibrate with None is not yet implemented')

        pp = self._pp
        df = self._obj.copy()

        # TODO: this is ugly, refactor this. Testing which columns to use should be more
        #       straigtforward and defined at one location. Not both here and in get_preeq_columns
        phreeq_cols = self._get_phreeq_columns()

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

        # return the solutions as pandas series with the same index as the source dataframe
        return pd.Series(solutions, index=self._obj.index)

    def get_saturation_index(self, mineral_or_gas, use_phreeqc=True, inplace=False, **kwargs):
        ''' adds or returns the saturation index of a mineral or the partial pressure of a gas using phreeqc.

           Parameters
           ----------
           mineral_or_gas: str
                           the name of the mineral of which the SI needs to be calculated
           use_phreeqc: bool
                        whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                        or partial pressure
           inplace: bool
                    whether to return a new dataframe with the column added or change the current dataframe itself

           Returns
           -------
                pandas.Series
                             with values of SI for each row of the input dataframe '''
        if inplace:
            raise NotImplementedError('inplace argument is not yet implemented.')
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')


        solutions = self.get_phreeqpython_solutions(**kwargs)
        saturation_index = [s.si(mineral_or_gas) if s is not None else None for s in solutions]

        self._clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        return pd.Series(saturation_index, index=self._obj.index)

    def get_specific_conductance(self, use_phreeqc=True, **kwargs):
        ''' returns the specific conductance (sc) of a water sample using phreeqc. sc is
            also known as electric conductivity (ec) or egv measurements.

            Parameters
            ----------
            use_phreeqc: bool
                        whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                        or partial pressure
            **kwargs:
                     are passed to the method `get_phreeqpython_solutions`

            Returns
            -------
            Series: with values of specific conductance for each row of the input dataframe '''
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')

        # create phreeqpython solutions
        solutions = self.get_phreeqpython_solutions(**kwargs)
        # extract sc from them
        specific_conductance = [s.sc for s in solutions]
        # clean up
        self._clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        return pd.Series(specific_conductance, index=self._obj.index)
