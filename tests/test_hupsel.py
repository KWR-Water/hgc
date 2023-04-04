# -*- coding: utf-8 -*-
"""
   Test file that loads a big excel file and see if HGC's crashes or not
"""

import pandas as pd
from pathlib import Path
import hgc
from hgc.constants import constants

import os
import sys
# No need for this next line if WADI was properly installed using pip
#sys.path.append('D:\\Users\\postvi\\Documents\\github\\wadi')
#os.chdir('D:\\Users\\postvi\\Documents\\py\\test_wadi')
def test_hupsel():
    """ A test of a whole lot of samples that have been analysed manually with
    PHREEQC. The outcomes are not compared to the expected values. It only checks
     if no errors arise. """

    fpath = Path(__file__).parent / 'data'
    fname = 'analyse_bas.xls'

    df = pd.read_excel(
        io=fpath / fname,
        sheet_name='labab',
        skiprows= [0,1,3],
        usecols = ('A:L,N,O,Q,S,T,W:Y,AA:BJ'),
    )

    df = df.set_index('labcode')

    ####Mn van ug/L naar mg/L
    df.Mn = df.Mn/1000
    df.P = df.P/1000

    ####kolom namen aanpassen naar phreeqc: HCO3 naar alkalinity
    df =  df.rename(columns={"HCO3":"alkalinity",'pH':'ph','EC':'ec','P':'PO4'})

    ####NA invullen
    df['temp']=10
    values = {"ph": 7, "alkalinity": 10}
    df = df.fillna(value=values)


    df.hgc.make_valid()
    hgc_cols = df.hgc.hgc_cols
    print(hgc_cols)

    print([*constants.atoms])
    print([*constants.ions])
    print([*constants.properties])
    constants.atoms['Zn']

    df.hgc.get_sum_anions()
    df.hgc.get_sum_cations()

    df.hgc.get_dominant_anions(inplace=True)
    df.hgc.get_dominant_cations(inplace=True)
    df.hgc.get_ratios()
    df.hgc.get_stuyfzand_water_type()


    df.hgc.get_saturation_index('CO2(g)')
    df.hgc.get_saturation_index('Calcite',inplace=True)
    df.hgc.get_saturation_index('Calcite',inplace=False)
    df.hgc.get_specific_conductance()
    df.hgc.get_phreeqpython_solutions()
