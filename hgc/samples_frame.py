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


        self.is_valid = self._check_validity(pandas_obj)
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
        return True


    def _replace_negative_concentrations(self):
        """
        Replace any negative concentrations with 0.
        """
        # Get all columns that represent chemical compounds
        # Replace negatives with 0
        raise NotImplementedError


    def _remove_invalid_strings(self):
        """ Remove any strings in HGC-columns that are not '<' or '>' """
        raise NotImplementedError
    

    def validate(self):
        """ 
        Run some tests to validate the object obj (a
        Pandas dataframe).
        """
        # Conduct conversions here. If they fail, raise error (e.g. when not a single valid column is present)
        self._replace_negative_concentrations()
        self._remove_invalid_strings()
        self.is_valid = True


    def replace_detection_lim(self, rule="half"):
        """ 
        Substitute detection limits according to one of the available
        rules. Cells that contain for example '<0.3' or '> 0.3' will be replaced
        with 0.15 and 0.45 respectively (in case of rule "half"). 

        Args:
            rule (str): Can be any of "half", ... Rule "half" replaces cells with detection limit for half of the value. 
        """
        # Search for any '>' and '<', replace
        raise NotImplementedError

    
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





