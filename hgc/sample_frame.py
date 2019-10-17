# https://github.com/ContinuumIO/cyberpandas/blob/master/cyberpandas/ip_array.py
# https://pandas.pydata.org/pandas-docs/stable/development/extending.html

import pandas as pd

@pd.api.extensions.register_dataframe_accessor("hgc")
class SamplesFrame:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        ''' run some tests to validate the object obj. obj is a
            pandas dataframe. E.g. check column names with obj.columns'''
        pass


    def convert_to_standard_units(self):
        return None
