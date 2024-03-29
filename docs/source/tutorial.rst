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

.. note::
    Please refer to the excellent `WaDI package <https://wadi.readthedocs.io/en/latest/>`_
    to get your excel or csv file
    with measurements in a format
    `that HGC understands <https://wadi.readthedocs.io/en/latest/user_guide/creating_hgc_dataframes.html>`_.
    In this tutorial, we create our own `DataFrame` for clarity.

.. ipython:: python

    testdata = {'alkalinity': [0.0], 'Al': [2600], 'Ba': [44.0],
                'Br': [0.0], 'Ca': [2.0], 'Cl': [19.0],
                'Co': [1.2], 'Cu': [4.0], 'doc': [4.4],
                'F': [0.08], 'Fe': [0.29], 'K': [1.1],
                'Li': [5.0], 'Mg': [1.6], 'Mn': ['< 0.05'],
                'Na': [15.0], 'Ni': [7.0], 'NH4': ['< 0.05'],
                'NO2': [0.0], 'NO3': [22.6], 'Pb': [2.7],
                'PO4': ['0.04'], 'ph': [4.3], 'SO4': [16.0],
                'Sr': [50], 'Zn': [60.0] }
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

For your convenience, all units for all allowed (columns with) atoms, ions and properties are enlisted here :ref:`here <Units>`.

Since in this case our DataFrame contains negative concentrations, detection limits (rows with '<' or '>') and
incorrect data types (e.g. string columns that are supposed to be numeric), HGC will initially report
that the DataFrame is invalid. HGC can automatically solve inconsistencies with the 'make_valid' method.
As a result, negative concentrations are replaced by 0; concentrations below detection limit are replaced
by half the limit; concentrations above the upper detection limit are replaced by 1.5 times that limit.

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
Base Exchange Index of each row; this is added as column to `df`:

.. ipython:: python

    df.hgc.get_bex()
    df.bex

We can also classify each sample into the Stuyfzand water type:

.. ipython:: python

    df.hgc.get_stuyfzand_water_type()
    df.water_type


Or get the sum of all anions (using the Stuyfzand method):

.. ipython:: python

    df.hgc.get_sum_anions()
    df.sum_anions

It is also possible to compute common hydrochemical ratios between different compounds.
HGC calculates ratios for all columns that are available and ignores any missing columns.

.. ipython:: python

    df.hgc.get_ratios()
    df.cl_to_na

For all these above mentioned *get* functions, the columns are added to the dataframe. Most
of the times this is convenient, but there are also cases where you don't want to add them
to the DataFrame but only want to return the result. In that case, one could use the `inplace`
argument; `this works the same as native pandas methods that have this argument
<https://www.geeksforgeeks.org/what-does-inplace-mean-in-pandas/>`_
With `inplace=True` (the default), the columns are added to the DataFrame (as shown
in the examples above). With `inplace=False` the columns are not added to the database
but returned as a pandas `Series` or `DataFrame`. E.g., for the Stuyfzand water type (a `Series`)
or `ratios` (a `DataFrame`):

.. ipython:: python

    water_type = df.hgc.get_stuyfzand_water_type(inplace=False)
    water_type
    ratios = df.hgc.get_ratios(inplace=False)
    ratios


Consolidation
=============
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

    df.hgc.consolidate(use_ph='field', use_ec='lab', use_temp=None,
                       use_so4=None, use_o2=None)
    df

.. warning::
    Note that omitting ``use_so4=None`` in the function call, would let the function
    fall back to the default which is ``ic``. Because the column ``so4_ic`` is not in the dataframe
    this will return an error. The same holds for ``use_temp`` and ``use_o2``.

.. ipython:: python
    :okexcept:

    df.hgc.consolidate(use_ph='field', use_ec='lab', use_temp=None,)


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


Coupling to PHREEQC
-------------------
Another great superpower of HGC is that it allows easy geochemistry *directly on your dataframe*!
It currently has coupling with the popular geochemistry software
`PHREEQC <https://www.usgs.gov/software/phreeqc-version-3>`_ via its python
wrappers as implemented by the `phreeqpython package <https://github.com/Vitens/phreeqpython>`_.

Let's extend the above DataFrame a little to make it more meaningful in the context of this coupling:

.. ipython:: python

    testdata = {
        'ph_lab': [4.5, 5.5, 7.6], 'ph_field': [4.4, 6.1, 7.7],
        'ec_lab': [304, 401, 340], 'ec_field': [290, 'error', 334.6],
        'temp': [10, 10, 10],
        'alkalinity':  [0, 7, 121],
        'O2':  [11, 0, 0],
        'Na': [9,20,31], 'K':[0.4, 2.1, 2.0],
        'Ca':[1,3,47],
        'Fe': [0.10, 2.33, 0.4],
        'Mn': [0.02, 0.06, 0.13],
        'NH4': [1.29, 0.08, 0.34],
        'SiO2': [0.2, 15.4, 13.3],
        'SO4': [7,19,35],
        'NO3': [3.4,0.1,0],
    }
    df = pd.DataFrame.from_dict(testdata)
    df.hgc.make_valid()
    df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None,
                       use_so4=None, use_o2=None)

With this DataFrame, we can do some PHREEQC calculations. For example,
we can calculate the saturation index of different minerals like Calcite:

.. ipython:: python

    df.hgc.get_saturation_index('Calcite')
    df['si_calcite'] # or df.si_calcite

The mineral name will be added as a column named `si_<mineral_name>` where `<mineral_name>` is the name of the mineral
as given to PHREEQC but all letters in *lower case* (and don't forget the underscore). The saturation index (SI) of a mineral can only be retrieved if they are defined in the phreeqc database
used by phreeqpython. If the mineral is not defined, always an SI of -999 will be returned.

This also works for the partial pressure of gasses (because in PhreeqC both minerals and gasses are defined as `PHASES`;
see below for explanation of the coupling to PhreeqC). But it looks
better if one uses the alias `partial_pressure` which returns the same values but with a different name of the column (prepending pp instead of si, since
it is the partial pressure and not the saturation index).

.. ipython:: python

    df.hgc.get_saturation_index('CO2(g)')
    df['si_co2(g)']
    df.hgc.get_partial_pressure('CO2(g)')
    df['pp_co2(g)']


Similar to the SI, the specific conductance (SC), also known as electric conductance (EC) or EGV,
is simply retrieved by calling:

.. ipython:: python

    df.hgc.get_specific_conductance()
    df.sc

Internally, these methods call the method `get_phreeqpython_solutions` to retrieve
instances of the PhreeqPython `Solution` class. `PhreeqPython <https://github.com/Vitens/phreeqpython>`_ is a
Python package that allows the use of the Geochemical modeling package PhreeqC from within Python. HGC leverages this
package to have a PhreeqC solution (or actually a PhreeqPython solution) for every row of the `SamplesFrame`. These are
available to the user by calling

.. ipython:: python
   :okexcept:

    df.hgc.get_phreeqpython_solutions()
    df.pp_solutions

Because all elements in this column are PhreeqPython `Solution`'s, PhreeqC can be used to calculate all kind of
properties of each water sample of each row in the `SamplesFrame`. In the documentation of PhreeqPython all these
are described. For example, one can derive the specific conductance or pH from the first sample:

.. ipython:: python

    df.pp_solutions[0].sc
    df.pp_solutions[0].pH

or for all the samples:

.. ipython:: python

    [s.sc for s in df.pp_solutions]

Note that these are the exact same results as above when `df.hgc.get_specific_conductance()` was called.

But also more involved operations are possible, for example, inspecting the speciation of the first sample in the
original `SamplesFrame` `df`:

.. ipython:: python

    df.pp_solutions[0].species

Note that units of these speciation calculations are in mmol/L.

One could even manipulate the solution by letting for example calcite precipitate
and see how this changes pH

.. ipython:: python

    desaturated_solutions = [s.desaturate('Calcite') for s in df.pp_solutions]

    pd.DataFrame(dict(
        original=df.ph,
        desaturated=[s.pH for s in desaturated_solutions],)
    ).round(2)


For more examples,
please visit the `examples on the Github page of PhreeqPython <https://github.com/Vitens/phreeqpython/tree/master/examples>`_.