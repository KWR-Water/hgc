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

    testdata = {'alkalinity', 'Al': [2600], 'Ba': [44.0],
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

    sum_anions = df.hgc.get_sum_anions()
    sum_anions

It is also possible to compute common hydrochemical ratios between different compounds.
HGC calculates ratios for all columns that are available and ignores any missing columns.

.. ipython:: python

    df_ratios = df.hgc.get_ratios()
    df_ratios

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

.. todo::
    below code gives an error because somehow the integration with phreeqc is failing
    when building the docs. it works fine when executing the code in a local environment
    though. This needs to be fixed or some other solution needs to be found.

.. .. ipython:: python
..     :okexcept:

.. code-block:: python

    si_calcite = df.hgc.get_saturation_index('Calcite')
    si_calcite

Only saturation index (SI) of minerals can be retrieved if they are defined in the phreeqc database
used by phreeqpython.

Similar to the SI, the specific conductance (SC), also known as electric conductance (EC) or EGV,
is simply retrieved by calling:

.. .. ipython:: python
..     :okexcept:

.. code-block:: python

    df.hgc.get_specific_conductance()

Internally, these methods call the method `get_phreeqpython_solutions` to retrieve
instances of the `phreeqpython` `Solution` class. These solutions can also be available
to the user by calling

.. .. ipython:: python
..     :okexcept:

.. code-block:: python

    pp_solutions = df.hgc.get_phreeqpython_solutions()

As all elements of the returned `Series` are `phreeqpython` `Solution`'s, all its methods can be called as well.
For example, the sc can be derived by:

.. .. ipython:: python
..     :okexcept:

.. code-block:: python

    [s.sc for s in pp_solutions]

But also more involved operations are possible, for example, inspecting the speciation of the first sample in the
original `SamplesFrame` `df`:

.. .. ipython:: python
..     :okexcept:

.. code-block:: python

    pp_solutions[0].species

Note that units of these speciation calculations are in mmol/L.