========
Tutorial
========
Practical examples


We always start by importing HGC:

.. ipython:: python

    import pandas as pd 
    import hgc

Creating a HGC-enabled DataFrame
--------------------------------
A hydrochemical groundwater analysis typically starts with a 'normal' Pandas DataFrame, in which
each row contains a groundwater quality sample, and each column represents a water quality parameter.
The DataFrame may contain concentrations of different chemical compounds, possibly exceeding the
detection limit (denoted with a '<' or '>' prefix). There may also be errors in the data, such as
negative concentrations or text placeholders.

.. ipython:: python

    testdata = {
        'Al': [2600], 'Ba': [44.0],
        'Br': [0.0], 'Ca': [2.0],
        'Cl': [19.0], 'Co': [1.2],
        'Cu': [4.0], 'doc': [4.4],
        'F': [0.08], 'Fe': [0.29],
        'HCO3': [0.0], 'K': [1.1],
        'Li': [5.0], 'Mg': [1.6],
        'Mn': ['< 0.05'], 'Na': [15.0],
        'Ni': [7.0], 'NH4': ['< 0.05'],
        'NO2': [0.0], 'NO3': [22.6],
        'Pb': [2.7], 'PO4': ['0.04'],
        'ph': [4.3], 'SO4': [16.0],
        'Sr': [50], 'Zn': [60.0]
    }
    df = pd.DataFrame.from_dict(testdata)
    df

Since the data in this DataFrame is messy, we cannot use it yet for hydrochemical calculations. HGC can check
if the data contains obvious errors: 

.. ipython:: python

    is_valid = df.hgc.is_valid
    is_valid

The DataFrame may contain any kind of columns and column names. However, HGC will only recognize a specific
set of columns with names of hydrochemical parameters.

.. ipython:: python

    from hgc.constants import constants

    print([*constants.atoms])
    print([*constants.ions])
    print([*constants.properties])

You can also retreive the details of each compound, such as the expected units, full name or molar weight:

.. ipython:: python

    constants.atoms['H']
    constants.properties['ec']

Since in this case our DataFrame contains negative concentrations, detection limits (rows with '<' or '>') and
incorrect data types (e.g. string columns that are supposed to be numeric), HGC will initially report
that the DataFrame is invalid. HGC can automatically solve inconsistencies with the 'make_valid' method.
As a result, negative concentrations are replaced by 0, concentrations exceeding the detection limit are replaced 
by 1/2 of the detection limit threshold and any string-columns cast to numeric:

.. ipython:: python

    df.hgc.make_valid()
    is_valid = df.hgc.is_valid
    is_valid
    df

    # Recognized HGC columns
    hgc_cols = df.hgc.hgc_cols
    print(hgc_cols)

Calculations
------------

Now that our DataFrame is valid, we can use all HGC methods, such as calculating the
Base Exchange Index of each row:

.. ipython:: python

    bex = df.hgc.get_bex()
    bex

We can also classify each sample into the Stuyfzand water type:

.. ipython:: python

    water_types = df.hgc.get_stuyfzand_water_type()
    water_types

Or get the sum of all anions (using the Stuyfzand method):

.. ipython:: python

    sum_anions = df.hgc.get_sum_anions_stuyfzand()
    sum_anions

It is also possible to compute common hydrochemical ratios between different compounds.
HGC calculates ratios for all columns that are available and ignores any missing columns.

.. ipython:: python

    df_ratios = df.hgc.get_ratios()
    df_ratios

A common situation is that one single parameter of a sample is measured with several methods or in
different places. Parameters such as EC and pH are frequently measured both in the lab and field, 
and SO4 and PO4 are frequently measured both by IC and ICP-OES. Normally we prefer the 
field data for EC and pH, but ill calibrated sensors or tough field circumstances may 
prevent these readings to be superior to the lab measurement. In such cases we want select from 
multiple columns the one to use for subsequent calculations, by consolidating into one single column 
containing the best measurements, possibly filling gaps with measurements from the inferior method. 
Let's consider this example:

.. ipython:: python

    testdata = {
        'ph_lab': [4.3, 6.3, 5.4], 'ph_field': [4.4, 6.1, 5.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
    }
    df = pd.DataFrame.from_dict(testdata)
    df

    df.hgc.make_valid()
    df

    df.hgc.consolidate(use_ph='field', use_ec='lab')
    df

Visualizing and exporting
-------------------------
The great thing about HGC is that your DataFrame gets hydrochemical superpowers, yet all functions
that you expect from a regular Pandas DataFrame are still available, allowing you to easily import/export 
and visualize data. 

.. ipython:: python
    
    df.std()
    df.plot()
    
.. plot:: 

    testdata = {
        'ph_lab': [4.3, 6.3, 5.4], 'ph_field': [4.4, 6.1, 5.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
    }
    df = pd.DataFrame.from_dict(testdata)
    df.plot()
