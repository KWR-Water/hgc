''' In here the extension of the pandas DataFrame is defined. It adds methods
    for validation, calculation of properties. Extending the dataframe is based on:
    # https://github.com/ContinuumIO/cyberpandas/blob/master/cyberpandas/ip_array.py
    # https://pandas.pydata.org/pandas-docs/stable/development/extending.html
'''

import pandas as pd

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
        self.is_valid = False
        self.hgc_cols = ()
        self.is_valid, self.hgc_cols = self._check_validity(pandas_obj)
        self._obj = pandas_obj


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
        PARAMS = ('mg',)

        hgc_cols = [item for item in PARAMS if item in obj.columns]
        neg_conc_cols = []
        invalid_str_cols = []
        
        for col in hgc_cols:
            if obj[col].dtype in ('object', 'str'):
                if not all(obj[col].str.isnumeric()):
                    invalid_str_cols.append(col)
            else:
                if any(obj[col] < 0):
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


    def consolidate(self, use_ph='field', use_ec='lab', use_so4='ic', use_o2='field', merge_on_na=False):
        """ 
        Consolidate parameters measured with different methods to one single parameter 

        Kwargs:
            use_ph (str): Which pH to use? Can be 'field' or 'lab', default 'field'
            use_ec (str): Which EC to use? Can be 'field' or 'lab', default 'lab'
            use_so4 (str): Which SO4 to use? Default 'ic'
            use_o2 (str): Which O2 to use? Can be 'field' or 'lab', default 'field'
            merge_on_na (str): Fill NaN's from one measurement method with measurements from other method
        """
        if not self.is_valid:
            raise ValueError("Method can only be used on validated HGC frames, use 'make_valid' to validate")
        
        param_mapping = {
            'ph': use_ph,
            'ec': use_ec,
            'so4': use_so4,
            'o2': use_o2
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
            if (source in self._obj.columns):
                self._obj[param] = np.NaN
                self._obj[param].fillna(self._obj[source], inplace=True)

                if merge_on_na:
                    raise NotImplementedError
                
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
