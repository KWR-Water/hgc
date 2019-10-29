import hgc
from hgc.samples_frame import SamplesFrame
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest


def test_hgc_namespace_is_added():
    ''' Test whether the HGC methods are added to
        dataframes that are created
    '''
    with mock.patch.object(SamplesFrame, "_validate") as mocked_validate:
        mocked_validate.return_value = True
        df = pd.DataFrame()
        df.hgc

def test_validate_dataframe():
    """ Df validation """

    df = pd.read_excel('./examples/data/dataset_basic.xlsx')
    #df.validate()
