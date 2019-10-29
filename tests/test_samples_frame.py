# from hgc import samples_frame
import hgc
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
from hgc.samples_frame import SamplesFrame
import pytest


class testSamplesFrame(TestCase):
    """ Simple tests for SampleFrame """
    def setUp(self):
        super().setUp()
        with mock.patch.object(SamplesFrame, "_validate") as mocked_validate:
            mocked_validate.return_value = True
            df = pd.DataFrame()
        self.df = df

    def testHgcNamespaceIsAdded(self, ):
        ''' Test whether the HGC methods are added to
            dataframes that are created
        '''
            self.df.hgc

    def testUnitsAreConverted(self):
        ''' test the method that converts units '''
        self.df.hgc.convert_to_standard_units()
        raise NotImplementedError()#a

class testSamplesFrame2(TestCase):
    """docstring for testSamplesFrame."""
    def setUp(self):
        super().setUp()
        dates = [datetime(1990, _m + 1, 1) for _m in range(10)]
        self.df = pd.DataFrame(dict(date=dates,
                                    hco3=np.arange(10),
                                    fe=np.arange(10) + 10,
                                    temp=np.arange(10) + 20))