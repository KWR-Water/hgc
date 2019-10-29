import hgc
from hgc.samples_frame import SamplesFrame
from hgc.constants import constants
import pandas as pd
import numpy as np
from unittest import TestCase, mock
from datetime import datetime
import pytest


def testHgcNamespaceIsAdded():
    ''' Test whether the HGC methods are added to
        dataframes that are created
    '''
    with mock.patch.object(SamplesFrame, "_validate") as mocked_validate:
        mocked_validate.return_value = True
        df = pd.DataFrame()
        df.hgc

def testMolarWeight():
    c = constants
