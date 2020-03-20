===============
Getting Started
===============
HGC (HydroGeoChemistry) is a Python package for correction, validation and analysis of ground water quality samples.

Main features:
 - Handle common erros and peculiarities in hydrochemical data, such as negative concentrations, detection limits and non-numerical placeholders
 - Calculate common ratios, such as for example MONC, SUVA and HCO3 to the sum of all anions
 - Classify groundwater samples according to the Stuyfzand water types
 - Calculate missing concentrations through the ion balance, with PhreeqPython

Install
-------
HGC requires Python 3.6 or later.

To get HGC, use the following command::

    pip install hgc

Philosophy
----------
HGC is an extension of the Pandas DataFrame, giving your DataFrame hydrochemistry superpowers. You can thus
mix HGC with your regular Pandas/Numpy workflows.

A DataFrame does not need to conform to a specific format to work with HGC, however it is required that:
 - Each row in the DataFrame represents a groundwater quality sample
 - Each column represents a groundwater quality parameter

HGC checks if column names in the DataFrame match with chemical parameters that it recognizes. Such columns
should be in the units that HGC expects. In addition to 'HGC-enabled' columns, the DataFrame can contain
an arbitrary number of non-hydrochemistry columns (such as XY-locations, comments, or other
measured quantities), HGC simply ignores those columns.

Conventions
-----------
The naming conventions of the column names is that they are all in lower case with
an underscore between separate words. E.g. the EC measured in the lab is indicated with
`ec_lab`. The only exception to this is the notation of chemical structures and atoms; there standard capitalization
is used. E.g. the column name for total total nitrogen is `N_total` and for ortho-phosphate `PO4_ortho`.
