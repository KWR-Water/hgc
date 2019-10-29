# from hgc import sample_frame
import hgc
import pandas as pd


def test_hgc_namespaceadded():
    ''' Test whether the HGC methods are added to
        dataframes that are created
    '''
    df = pd.DataFrame(dict(a=[1,2], b=[3,4]))
    df.hgc.convert_to_standard_units()
