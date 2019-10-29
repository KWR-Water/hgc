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
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        ''' run some tests to validate the object obj. obj is a
            pandas dataframe. E.g. check column names with obj.columns'''
        raise NotImplementedError('There is not method implemented for validation yet')


    def convert_to_standard_units(self):
        return None
