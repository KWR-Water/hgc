"""
The `SamplesFrame` class is an extended Pandas DataFrame, offering additional methods
for validation of hydrochemical data, calculation of relevant ratios and classifications.

.. # an alias used in different doc strings in this file
.. |HCO3| replace:: HCO\ :sub:`3`\ :sup:`-`

"""
import logging

import numpy as np
import pandas as pd
from phreeqpython import PhreeqPython

from hgc.constants import constants
from hgc.constants.constants import mw


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

    def _check_validity(self, verbose=True):
        """
        Check if the dataframe is a valid HGC dataframe

        Notes
        -----
        Checks are:
            1. Are there any columns names in the recognized parameter set?
            2. Are there no strings in the recognized columns (except '<' and '>')?
            3. Are there negative concentrations in the recognized columns?

        """
        obj = self._obj
        if verbose:
            logging.info("Checking validity of DataFrame for HGC...")
        # Define allowed columns that contain concentration values
        allowed_concentration_columns = (list(constants.atoms.keys()) +
                                         list(constants.ions.keys()))

        hgc_cols = self.hgc_cols
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

        if verbose:
            logging.info(f"DataFrame contains {len(hgc_cols)} HGC-columns")
            if len(hgc_cols) > 0:
                logging.info(f"Recognized HGC columns are: {','.join(hgc_cols)}")

            if unused_columns := list(set(obj.columns) - set(hgc_cols)):
                logging.info(f'These columns of the dataframe are not used by HGC: {unused_columns}')

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

        return is_valid

    @property
    def allowed_hgc_columns(self):
        """  Returns allowed columns of the hgc `SamplesFrame`"""
        return (list(constants.atoms.keys()) +
                               list(constants.ions.keys()) +
                               list(constants.properties.keys()))
    @property
    def hgc_cols(self):
        """ Return the columns that are used by hgc """
        return [item for item in self.allowed_hgc_columns if item in self._obj.columns]


    @property
    def is_valid(self):
        """ returns a boolean indicating that the columns used by hgc have
        valid values """
        is_valid = self._check_validity(verbose=False)
        return is_valid

    def _make_input_df(self, cols_req):
        """
        Make input DataFrame for calculations. This DataFrame contains columns for each required parameter,
        which is 0 in case the parameter is not present in original HGC frame. It also
        replaces all NaN with 0.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        df_in = pd.DataFrame(columns=cols_req)
        for col_req in cols_req:
            if col_req in self._obj:
                df_in[col_req] = self._obj[col_req]
            else:
                logging.info(f"Column {col_req} is not present in DataFrame, assuming concentration 0 for this compound for now.")
        df_in = df_in.fillna(0.0)

        return df_in


    def _replace_detection_lim(self, rule="half"):
        """
        Substitute detection limits according to one of the available
        rules. Cells that contain for example '<0.3' or '> 0.3' will be replaced
        with 0.15 and 0.45 respectively (in case of rule "half").

        Parameters
        ----------
        rule : {'half', 'on', 'zero'}, default 'half'
            Rule "half" replaces cells *below* detection limit with half of the value of the detection limit;
                   and replaces cells *above* upper detection limit with 1.5 of that detection limit's value.
            Rule "at" replaces detection limit cells with the exact value of the detection limit.
            Rule "zero" replaces below detection limit cells with zero; values above the detection limit set at detection limit.
        """
        rule = str(rule)
        for col in self.hgc_cols:
            if self._obj[col].dtype in ('object', 'str'):
                is_below_dl = self._obj[col].str.contains(pat=r'^[<]\s*\d').fillna(False)
                is_above_dl = self._obj[col].str.contains(pat=r'^[>]\s*\d').fillna(False)
                lower_detection_limit = self._obj.loc[is_below_dl, col].str.extract(r'(\d+)').astype(np.float64).values
                upper_detection_limit = self._obj.loc[is_below_dl, col].str.extract(r'(\d+)').astype(np.float64).values

                if rule.lower() == 'half':
                    logging.info("Replace values below detection limit with (detection limit) / 2.")
                    self._obj.loc[is_below_dl, col] = lower_detection_limit / 2
                    logging.info("Replace values above detection limit with 1.5 * (detection limit).")
                    self._obj.loc[is_above_dl, col] = 1.5 * upper_detection_limit
                elif rule.lower() == 'on':
                    logging.info("Replace values above and below detection limit with detection limit.")
                    self._obj.loc[is_below_dl, col] = lower_detection_limit
                    self._obj.loc[is_above_dl, col] = upper_detection_limit
                elif str(rule).lower() in ['zero', '0']:
                    logging.info("Replace values below detection limit with zero, above detection limit with (upper) detection limit.")
                    self._obj.loc[is_below_dl, col] = 0
                    self._obj.loc[is_above_dl, col] = upper_detection_limit
                else:
                    raise ValueError("Invalid rule. Allowed rules are half, on and zero.")

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
                    use_temp='field', use_alkalinity='alkalinity',
                    merge_on_na=False, inplace=True):
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
        use_alkalinity: str, default 'alkalinity'
            name of the column to use for alkalinity
        merge_on_na : bool, default False
            Fill NaN's from one measurement method with measurements from other method.
        inplace : bool, default True
            Modify `SamplesFrame` in place. inplace=False is not implemented (yet)


        Raises
        ------
            ValueError: if one of the `use_` parameters is set to a column that is not in the dataframe
                        *or* if one of the default parameters is not in the dataframe while it is not
                        set to None.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        if inplace is False:
            raise NotImplementedError('inplace=False is not (yet) implemented.')

        param_mapping = {
            'ph': use_ph,
            'ec': use_ec,
            'SO4': use_so4,
            'O2': use_o2,
            'temp': use_temp,
        }
        if not (use_alkalinity in ['alkalinity', None]):
            try:
                self._obj['alkalinity'] = self._obj[use_alkalinity]
                self._obj.drop(columns=[use_alkalinity], inplace=True)
            except KeyError:
                raise ValueError(f"Invalid value for argument 'use_alkalinity': " +
                                f"{use_alkalinity}. It is not a column name of " +
                                f"the dataframe")


        for param, method in param_mapping.items():
            if not method:
                # user did not specify source, ignore
                continue

            if not isinstance(method, str):
                raise ValueError(f"Invalid method {method} for parameter {param}. Arg should be a string.")

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
                self._obj.drop(columns=cols, inplace=True, errors='ignore')

            else:
                raise ValueError(f"Column {source} not present in DataFrame. Use " +
                                 f"use_{param.lower()}=None to explicitly ignore consolidating " +
                                 f"this column.")


    def get_bex(self, watertype="G", inplace=True):
        """
        Get Base Exchange Index (meq/L). By default this is the BEX without dolomite.

        Parameters
        ----------
        watertype : {'G', 'P'}, default 'G'
            Watertype (Groundwater or Precipitation)
        inplace: bool, optional, default True
                whether the saturation index should be added to the `pd.DataFrame` (inplace=True)
                as column `si_<mineral_name>` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` or `pd.Series` with base exchange index for each row in SamplesFrame
            if `inplace=False`.
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

        if inplace:
            self._obj['bex'] = df_out['bex']
        else:
            return df_out['bex']


    def get_ratios(self, inplace=True):
        """
        Calculate common hydrochemical ratios, will ignore any ratios
        in case their constituents are not present in the `SamplesFrame`.

        Notes
        -----

        It is assumed that only |HCO3| contributes to
        the alkalinity.

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

        Parameters
        ----------
        inplace: bool, optional, default True
                whether the saturation index should be added to the `pd.DataFrame` (inplace=True)
                as column `<numerator>_to_<denominator>` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.DataFrame or None
            Returns None if `inplace=True` and `pd.DataFrame` with the different ratios as column, for each row in
            `SamplesFrame` if `inplace=False`.
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
            'hco3_to_ca': ['alkalinity', 'Ca'],
            '2h_to_18o': ['2H', '18O'],
            'suva': ['uva254', 'doc'],
            'hco3_to_sum_anions': ['alkalinity', 'sum_anions'],
            'hco3_to_ca_and_mg': ['alkalinity', 'Ca', 'Mg'],
            'monc': ['cod', 'Fe', 'NO2', 'doc'],
            'cod_to_doc': ['cod', 'Fe', 'NO2', 'doc']
        }

        for ratio, constituents in ratios.items():
            has_cols = [const in self._obj.columns for const in constituents]
            if all(has_cols):
                if ratio == 'hco3_to_sum_anions':
                    df_ratios[ratio] = self._obj['alkalinity'] / self.get_sum_anions(inplace=False)
                elif ratio == 'hco3_to_ca_and_mg':
                    df_ratios[ratio] = self._obj['alkalinity'] / (self._obj['Ca'] + self._obj['Mg'])
                elif ratio == 'monc':
                    df_ratios[ratio] = 4 - 1.5 * (self._obj['cod'] - 0.143 * self._obj['Fe'] - 0.348 * self._obj['NO2']) / (3.95 * self._obj['doc'])
                elif ratio == 'cod_to_doc':
                    df_ratios[ratio] = ((0.2532 * self._obj['cod'] - 0.143 * self._obj['Fe'] - 0.348 * self._obj['NO2']) / 32) / (self._obj['doc'] / 12)
                else:
                    df_ratios[ratio] = self._obj[constituents[0]] / self._obj[constituents[1]]
            else:
                missing_cols = [i for (i, v) in zip(constituents, has_cols) if not v]
                logging.info(f"Cannot calculate ratio {ratio} since columns {','.join(missing_cols)} are not present.")

        if inplace:
            logging.info(f'Added columns {list(df_ratios.columns)}')
            self._obj[df_ratios.columns] = df_ratios
        else:
            return df_ratios


    def get_stuyfzand_water_type(self, inplace=True):
        """
        Get Stuyfzand water type. This water type classification contains
        5 components: Salinity, Alkalinity, Dominant Cation, Dominant Anion and Base Exchange Index.
        This results in a classification such as for example 'F3CaMix+'.

        It is assumed that only |HCO3| contributes to
        the alkalinity.

        Parameters
        ----------
        inplace: bool, optional, default True
                whether the saturation index should be added to the `pd.DataFrame` (inplace=True)
                as column `<numerator>_to_<denominator>` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series
            Series with Stuyfzand water type of each row in original `SamplesFrame`.
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")

        # Create input dataframe containing all required columns
        # Inherit column values from HGC frame, assume 0 if column
        # is not present
        cols_req = ('Al', 'Ba', 'Br', 'Ca', 'Cl', 'Co', 'Cu', 'doc', 'F', 'Fe', 'alkalinity', 'K', 'Li', 'Mg', 'Mn', 'Na', 'Ni', 'NH4', 'NO2', 'NO3', 'Pb', 'PO4', 'ph', 'SO4', 'Sr', 'Zn')
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
        df_out.loc[df_in['alkalinity'] > 31, 'swt_a'] = '0'
        df_out.loc[df_in['alkalinity'] > 61, 'swt_a'] = '1'
        df_out.loc[df_in['alkalinity'] > 122, 'swt_a'] = '2'
        df_out.loc[df_in['alkalinity'] > 244, 'swt_a'] = '3'
        df_out.loc[df_in['alkalinity'] > 488, 'swt_a'] = '4'
        df_out.loc[df_in['alkalinity'] > 976, 'swt_a'] = '5'
        df_out.loc[df_in['alkalinity'] > 1953, 'swt_a'] = '6'
        df_out.loc[df_in['alkalinity'] > 3905, 'swt_a'] = '7'

        #Dominant cation
        s_sum_cations = self.get_sum_cations(inplace=False)

        df_out['swt_domcat'] = self._get_dominant_anions_of_df(df_in)

        # Dominant anion
        s_sum_anions = self.get_sum_anions(inplace=False)
        cl_mmol = df_in.Cl/mw('Cl')
        hco3_mmol = df_in.alkalinity/(mw('H') + mw('C') + 3*mw('O'))
        no3_mmol = df_in.NO3/(mw('N') + 3*mw('O'))
        so4_mmol = df_in.SO4/(mw('S') + 4*mw('O'))

        # TODO: consider renaming doman to dom_an or dom_anion
        is_doman_cl = (cl_mmol > s_sum_anions/2)
        df_out.loc[is_doman_cl, 'swt_doman'] = "Cl"

        is_doman_hco3 = ~is_doman_cl & (hco3_mmol > s_sum_anions/2)
        df_out.loc[is_doman_hco3, 'swt_doman'] = "HCO3"

        is_doman_so4_or_no3 = ~is_doman_cl & ~is_doman_hco3 & (2*so4_mmol + no3_mmol > s_sum_anions/2)
        is_doman_so4 = (2*so4_mmol > no3_mmol)
        df_out.loc[is_doman_so4_or_no3 & is_doman_so4, 'swt_doman'] = "SO4"
        df_out.loc[is_doman_so4_or_no3 & ~is_doman_so4, 'swt_doman'] = "NO3"

        is_mix = ~is_doman_cl & ~is_doman_hco3 & ~is_doman_so4_or_no3
        df_out.loc[is_mix, 'swt_doman'] = "Mix"

        # Base Exchange Index
        s_bex = self.get_bex(inplace=False)
        threshold1 = 0.5 + 0.02*cl_mmol
        threshold2 = -0.5-0.02*cl_mmol
        is_plus = (s_bex > threshold1) & (s_bex > 1.5*(s_sum_cations-s_sum_anions))

        is_minus = ~is_plus & (s_bex < threshold2) & (s_bex < 1.5*(s_sum_cations-s_sum_anions))

        is_neutral = (~is_plus & ~is_minus &
                      (s_bex > threshold2) & (s_bex < threshold1) &
                      ((s_sum_cations == s_sum_anions) |
                       ((abs(s_bex + threshold1*(s_sum_cations-s_sum_anions))/abs(s_sum_cations-s_sum_anions))
                        > abs(1.5*(s_sum_cations-s_sum_anions)))
                       )
                      )

        is_none = ~is_plus & ~is_minus & ~is_neutral


        df_out.loc[is_plus, 'swt_bex'] = '+'
        df_out.loc[is_minus, 'swt_bex'] = '-'
        df_out.loc[is_neutral, 'swt_bex'] = 'o'
        df_out.loc[is_none, 'swt_bex'] = ''

        #Putting it all together
        df_out['swt'] = df_out['swt_s'].str.cat(df_out[['swt_a', 'swt_domcat', 'swt_doman', 'swt_bex']])

        if inplace:
            logging.info(f'Added the column water_type.')
            self._obj['water_type'] = df_out['swt']
        else:
            return df_out['swt']

    def _get_dominant_anions_of_df(self, df_in):
        """  calculates the dominant anions of the dataframe df_in """
        s_sum_cations = self.get_sum_cations(inplace=False)

        cols_req = ('ph', 'Na', 'K', 'Ca', 'Mg', 'Fe', 'Mn', 'NH4', 'Al', 'Ba', 'Co', 'Cu', 'Li', 'Ni', 'Pb', 'Sr', 'Zn')
        df_in = df_in.hgc._make_input_df(cols_req)

        na_mmol = df_in.Na/mw('Na')
        k_mmol = df_in.K/mw('K')
        nh4_mmol = df_in.NH4/(mw('N')+4*mw('H'))
        ca_mmol = df_in.Ca/mw('Ca')
        mg_mmol = df_in.Mg/mw('Mg')
        fe_mmol = df_in.Fe/mw('Fe')
        mn_mmol = df_in.Mn/mw('Mn')
        h_mmol = (10**-df_in.ph) / 1000  # ph -> mol/L -> mmol/L
        al_mmol = 1000. * df_in.Al/mw('Al')  # ug/L ->mg/L -> mmol/L

        # - Na, K, NH4
        # select rows that do not have Na, K or NH4 as dominant cation
        is_no_domcat_na_nh4_k = (na_mmol + k_mmol + nh4_mmol) < (s_sum_cations/2)

        is_domcat_nh4 = ~is_no_domcat_na_nh4_k & (nh4_mmol > (na_mmol + k_mmol))

        is_domcat_na = ~is_no_domcat_na_nh4_k & ~is_domcat_nh4 & (na_mmol > k_mmol)

        is_domcat_k = ~is_no_domcat_na_nh4_k & ~is_domcat_nh4 & ~is_domcat_na

        # abbreviation
        is_domcat_na_nh4_k = is_domcat_na | is_domcat_nh4 | is_domcat_k

        # - Ca, Mg
        is_domcat_ca_mg = (
            # not na or nh4 or k dominant
            ~is_domcat_na_nh4_k & (
                # should be any of Ca or Mg available
                ((ca_mmol > 0) | (mg_mmol > 0)) |
                # should be more of Ca or Mg then sum of H, Fe, Al, Mn
                # (compensated for charge)
                (2*ca_mmol+2*mg_mmol < h_mmol+3*al_mmol+2*fe_mmol+2*mn_mmol)))

        is_domcat_ca = is_domcat_ca_mg & (ca_mmol >= mg_mmol)
        is_domcat_mg = is_domcat_ca_mg & (ca_mmol < mg_mmol)

        # - H, Al, Fe, Mn
        # IF(IF(h_mmol+3*IF(al_mmol)>2*(fe_mol+mn_mol),IF(h_mmol>3*al_mmol,"H","Al"),IF(fe_mol>mn_mol,"Fe","Mn")))
        is_domcat_fe_mn_al_h = (
            # not na, nh4, k, ca or Mg dominant
            ~is_domcat_na_nh4_k & ~is_domcat_ca & ~is_domcat_mg & (
                # should be any of Fe, Mn, Al or H available
                (fe_mmol > 0) | (mn_mmol > 0) | (h_mmol > 0) | (al_mmol > 0)  # |
                # # should be more of Ca or Mg then sum of H, Fe, Al, Mn
                # # (compensated for charge)
                # (2*ca_mmol+2*mg_mmol < h_mmol+3*al_mmol+2*fe_mmol+2*mn_mmol)
            )
        )

        is_domcat_h_al=is_domcat_fe_mn_al_h & ((h_mmol + 3*al_mmol) > (2*fe_mmol + 2*mn_mmol))
        is_domcat_h = is_domcat_h_al & (h_mmol > al_mmol)
        is_domcat_al = is_domcat_h_al & (al_mmol > h_mmol)

        is_domcat_fe_mn = is_domcat_fe_mn_al_h & ~is_domcat_h_al
        is_domcat_fe = is_domcat_fe_mn & (fe_mmol > mn_mmol)
        is_domcat_mn = is_domcat_fe_mn & (mn_mmol > fe_mmol)

        sr_out = pd.Series(index=df_in.index, dtype='object')
        sr_out[:] = ""
        sr_out[is_domcat_nh4] = "NH4"
        sr_out[is_domcat_na] = "Na"
        sr_out[is_domcat_k] = "K"
        sr_out[is_domcat_ca] = 'Ca'
        sr_out[is_domcat_mg] = 'Mg'
        sr_out[is_domcat_fe] = 'Fe'
        sr_out[is_domcat_mn] = 'Mn'
        sr_out[is_domcat_al] = 'Al'
        sr_out[is_domcat_h] = 'H'

        return sr_out


    def get_dominant_anions(self, inplace=True):
        """ Adds column or returns a series with the dominant anions.

        Parameters
        ----------
        inplace: bool, optional, default True
                whether the saturation index should be added to the `pd.DataFrame` (inplace=True)
                as column `<numerator>_to_<denominator>` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` and `pd.Series` with dominant anions for each row in `SamplesFrame`
            if `inplace=False`.
        """
        if inplace:
            self._obj['dominant_anion'] = self._get_dominant_anions_of_df(self._obj)
        else:
            return self._get_dominant_anions_of_df(self._obj)

    def fillna_concentrations(self, how="phreeqc"):
        """
        Calculate missing concentrations based on the charge balance.

        Parameters
        ----------
        how : {'phreeqc', 'analytic'}, default 'phreeqc'
            Method to compute missing concentrations.
        """
        raise NotImplementedError()

    def get_ion_balance(self, inplace=True):
        """
        Calculate the balance between anion and kations and add it as a percentage [%]
        to the column 'ion_balance' to the SamplesFrame

        Parameters:
        -----------
        inplace: bool, optional, default True
                whether the ion balance should be added to the `SamplesFrame` (inplace=True)
                as column `ion_balance` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` or `pd.Series` with ion balance for each row in `SamplesFrame`
            if `inplace=False`.
        """
        anions = abs(self.get_sum_anions(inplace=False))
        cations = abs(self.get_sum_cations(inplace=False))
        ion_balance = 100 * (cations - anions) / (cations + anions)
        if inplace:
            logging.info("Charge balance of ions is added to the column ion_balance to the DataFrame")
            self._obj['ion_balance'] = ion_balance
        else:
            return ion_balance


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
        Try to convert the DataFrame into a valid HGC-`SamplesFrame`.
        """
        # Conduct conversions here. If they fail, raise error (e.g. when not a single valid column is present)
        # Important: order is important, first convert strings to double, then replace negative concentrations
        self._replace_detection_lim()
        self._cast_datatypes()
        self._replace_negative_concentrations()
        self._check_validity(verbose=True)


    def get_sum_anions(self, inplace=True):
        """
        Calculate sum of anions according to the Stuyfzand method.

        It is assumed that only |HCO3| contributes to
        the alkalinity.

        Parameters
        ----------
        inplace: bool, optional, default True
                whether the sum of anions should be added to the `pd.DataFrame` (inplace=True)
                as column `sum_anions` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` or `pd.Series` with sum of anions for each row in `SamplesFrame`
            if `inplace=False`.
        """
        cols_req = ('Br', 'Cl', 'doc', 'F', 'alkalinity', 'NO2', 'NO3', 'PO4', 'SO4', 'ph')
        df_in = self._make_input_df(cols_req)
        s_sum_anions = pd.Series(index=df_in.index,dtype='float64')

        k_org = 10**(0.039*df_in['ph']**2 - 0.9*df_in['ph']-0.96) # HGC manual equation 3.5
        a_org = k_org * df_in['doc'] / (100*k_org + (10**-df_in['ph'])/10) # HGC manual equation 3.4A
        sum_ions = (df_in['Cl']/35.453 + df_in['SO4']/48.03 +
                    df_in['alkalinity']/61.02 + df_in['NO3']/62. +
                    df_in['NO2']/46.0055 + df_in['F']/18.9984 +
                    df_in['Br']/79904 +
                    (df_in['PO4']/94.971) / (1 + 10**(df_in['ph']-7.21))
                   )

        is_add_a_org = (a_org > df_in['alkalinity']/61.02)

        s_sum_anions.loc[is_add_a_org] = sum_ions + a_org
        s_sum_anions.loc[~is_add_a_org] = sum_ions

        if inplace:
            self._obj['sum_anions'] = s_sum_anions
        else:
            return s_sum_anions

    def get_sum_cations(self, inplace=True):
        """
        Calculate sum of cations according to the Stuyfzand method.

        Parameters
        ----------
        inplace: bool, optional, default True
                whether the sum of cations should be added to the `pd.DataFrame` (inplace=True)
                as column `sum_cations` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` or `pd.Series` with sum of cations for each row in `SamplesFrame`
            if `inplace=False`.
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

        if inplace:
            self._obj['sum_cations'] = s_sum_cations
        else:
            return s_sum_cations


    def select_phreeq_columns(self):
        """
        Returns the columns from the DataFrame that might be used
        by PhreeqPython.

        Returns
        -------
        list
            Usable PhreeqPython columns
        """
        df = self._obj

        bicarbonate_in_columns = any([('hco' in _c.lower()) or
                                      ('bicarbona' in _c.lower())
                                      for _c in df.columns])
        alkalinity_in_columns = any(['alkalinity' in _c.lower()
                                     for _c in df.columns])
        if bicarbonate_in_columns:
            if alkalinity_in_columns:
                logging.warning('Warning: both bicarbonate (or hco3) and alkalinity are ' +
                'defined as columns. Note that only alkalinity column is used')
            else:
                logging.warning('Warning: bicarbonate (or hco3) is found, but no alkalinity ' +
                'is defined as columns. Note that only alkalinity column are used')


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

    def get_phreeqpython_solutions(self, equilibrate_with='none', inplace=True):
        """
        Return a series of `phreeqpython solutions <https://github.com/Vitens/phreeqpython>`_ derived from the (row)data in the `SamplesFrame`.

        Parameters
        ----------
        equilibrate_with : str, default 'none'
            Ion to add for achieving charge equilibrium in the solutions.
        inplace : bool, default True
            Whether the result is returned as a `pd.Series` or is added to the `pd.DataFrame`
            as column `pp_solutions`.

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` and `pd.Series` with `PhreeqPython.Solution` instances for every row in
            `SamplesFrame` if `inplace=False`.
        """
        # `None` is also a valid argument and is translated to the strin `'none'`
        if equilibrate_with is None:
            equilibrate_with = 'none'

        pp = self._pp
        df = self._obj.copy()

        phreeq_cols = self.select_phreeq_columns()

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

            if not (equilibrate_with.lower() in ['none', 'auto']):
                try:
                    # append the keyword charge to the compound that is used to charge balance
                    _sol[equilibrate_with] = _sol[equilibrate_with] + ' charge'
                except KeyError:
                    logging.info(f'{equilibrate_with} not found in solution while it is selected to balance charge with. Starts initial guess with 20 mg/L to balance charge.')
                    _sol[equilibrate_with] = '20. mg/L charge'
            elif equilibrate_with.lower() == 'auto':
                try:
                    # append the keyword charge to the compound that is used to charge balance
                    _sol['Na'] = _sol['Na'] + ' charge'
                except KeyError:
                    logging.info(f'Na is not found in solution while it is automatically selected to balance charge with. Starts initial guess with 20 mg/L Na to balance charge.')
                    _sol[equilibrate_with] = '20. mg/L charge'

            try:
                solutions[index] = pp.add_solution(_sol)
            except Exception as error:
                if equilibrate_with.lower() == 'auto':
                    _sol['Na'] = _sol['Na'].replace(' charge', '')
                    _sol['Cl'] = _sol['Cl'] + ' charge'
                    try:
                        logging.info(f"initializing solution with charge balancing with Na failed. Now trying to initialize solution by" +
                                     " charge balancing with Cl.")
                        solutions[index] = pp.add_solution(_sol)
                    except Exception as error:
                        logging.info(error)
                        raise ValueError(f'Something went wrong with the phreeqc calculation with index {index} from the DataFrame. PHREEQC returned: {error}. Charge balancing with either Na or Cl failed.')
                else:
                    logging.info(error)
                    raise ValueError(f'Something went wrong with the phreeqc calculation with index {index} from the DataFrame. PHREEQC returned: {error}. ' +
                                     'Possibly charge balance could (sufficiently) reached.')

        return_series = pd.Series(solutions, index=self._obj.index)
        if inplace:
            self._obj['pp_solutions'] = return_series
        else:
            # return the solutions as pandas series with the same index as the source dataframe
            return return_series

    def get_saturation_index(self, mineral_or_gas, use_phreeqc=True, inplace=True, **kwargs):
        """ adds or returns the saturation index (SI) of a mineral or the partial pressure of a gas using phreeqc. The
            column name of the result is si_<mineral_name> (if inplace=True).

           Parameters
           ----------
           mineral_or_gas: str
                           the name of the mineral of which the SI needs to be calculated
           use_phreeqc: bool
                        whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                        or partial pressure
            inplace: bool, optional, default=True
                    whether the saturation index should be added to the `pd.DataFrame` (inplace=True)
                    as column `si_<mineral_name>` or returned as a `pd.Series` (inplace=False).

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` and `pd.Series` with the saturation index of the mineral for each row in `SamplesFrame`
            if `inplace=False`.
        """
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')


        solutions = self.get_phreeqpython_solutions(inplace=False, **kwargs)
        saturation_index = [s.si(mineral_or_gas) if s is not None else None for s in solutions]

        self._clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        name_series = 'si_'+ mineral_or_gas.lower()
        return_series = pd.Series(saturation_index, index=self._obj.index,
                                  name=name_series)
        if inplace:
            logging.info(f'Added column {name_series}')
            self._obj[name_series] = return_series
        else:
            return return_series

    def get_specific_conductance(self, use_phreeqc=True, inplace=True, **kwargs):
        """ returns the specific conductance (sc) of a water sample using phreeqc. sc is
            also known as electric conductivity (ec) or egv measurements.

            Parameters
            ----------
            use_phreeqc: bool, optional
                    whether to return use phreeqc as backend or fall back on internal hgc-routines to calculate SI
                    or partial pressure
            inplace: bool, optional, default=True
                    whether the specific conductance should be added to the `pd.DataFrame` (inplace=True)
                    as column `sc` or returned as a `pd.Series` (inplace=False).
            **kwargs:
                     are passed to the method `get_phreeqpython_solutions`

        Returns
        -------
        pandas.Series or None
            Returns None if `inplace=True` and `pd.Series` with specific conductance for each row in `SamplesFrame`
            if `inplace=False`.
        """
        if not use_phreeqc:
            raise NotImplementedError('use_phreeqc=False is not yet implemented.')

        # create phreeqpython solutions
        solutions = self.get_phreeqpython_solutions(inplace=False, **kwargs)
        # extract sc from them
        specific_conductance = [s.sc for s in solutions]
        # clean up
        self._clean_up_phreeqpython_solutions(solutions)

        # return it as series with the same index as the dataframe
        series_name = 'sc'
        return_series = pd.Series(specific_conductance, index=self._obj.index,
                                  name=series_name)
        if inplace:
            self._obj[series_name] = return_series
        else:
            return return_series
