========================================================================================================
Import data and recognizing features
========================================================================================================

Overview
========

There are many different formats and datamodels to store water quality data.
This makes importing data to a uniform database that is suitable for analysis in HGC quite cumbersome.

The HGC.IO module partly automates importing water quality data.
It takes csv, excel files and pandas' dataframe. And can handle both ‘wide’ data formats
(with each parameter stored in a different column) and ‘stacked’ data formats (with all data
is stored in 1 column). The current version can also handle the GEF-format used in the Netherlands (BRO/ DINO).
Features and Units are automatically recognized using an algorithm for named entity recognition (HGC.NER-module).

Steps
-----

Operating the IO and NER module typically involves 5 steps:

1. Read the data and reshape to a stacked dataframe with "hgc.io.read_stacked()", "hgc.io.read_wide()" or "hgc.io.read_gef()"

2. Map the features to features accepted by HGC with “:code:`hgc.named_entity_recognition.mapping.generate_feature_map()`”. For example, “Iron” will be mapped to “Fe”.

3. Map the units to units accepted by HGC with “hgc.ner.generate_unit_map()”. For example, “mg-NO3/L” will be mapped to ”mg/L”.

4. Harmonize Features and Units with "hgc.io.harmonize()"

5. Reshape to a dataframe in HGC 'wide' format with “hgc.io.to_hgc()”

Now, let’s try some examples by importing different datamodels.

.. ipython:: python
    :okexcept:

    import os
    import hgc
    import hgc.io
    import hgc.named_entity_recognition.mapping as ner
    import hgc.constants.importdefaults
    import pandas as pd
    from pathlib import Path

Note that these example files are available in the folder .\\hgc\\examples\\data:

.. ipython:: python
    :okexcept:

    PATH = os.getcwd()
    PATH


Step 1: Read data
=================
The first step is to read the input data into a pandas dataframe where the data is "stacked":
all data is presented in one column containing all the values and another column lists the feature and the units.
The function and syntax depends on the datamodel of the input data. The current version of hgc.io can deal with
stacked-data (see Step 1A), wide-data (Step 1B) and GEF-datamodels (Step 1C).

1A stacked data: hgc.io.read_stacked()
--------------------------------------
The input file may be either a XLSX, XLS or CSV file or a dataframe (without headers!)
and with data already in stacked shape (so 1 value per row!).
Let's start by defining the arguments for reading the example file:

.. ipython:: python
    :okexcept:

    filepath = str(PATH/'examples/data/example1.xlsx')  # path to excel file
    sheet_name = 'stacked'  # name of sheet in excel file

The user has to define in which rows to find the headers and the values.
This can be eigher a list of length 1 to select a single row, or a <Slice> to select multiple rows.

.. ipython:: python
    :okexcept:

    slice_header = [0]  # header is in row 0
    slice_data = [slice(1, None)]  # values are from row 1 untill the end of file (<None> indicates last row here)

The map_header is a that dictionary defines how to rename the headers in the input file.
For stacked data, it is compulsory to define the headers 'Feature', 'Value', 'Unit' and 'SampleID', even if they are unchanged.
This may be achieved by using the same key and values. For example "{'Value':'Value', 'SampleID':'SampleID'}"

.. ipython:: python
    :okexcept:

    map_header = {**hgc.io.default_map_header(),  # default headers
        'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}  # headers that need to be adjusted.

Now ready to read the data:

.. ipython:: python
    :okexcept:

    dfA_read = hgc.io.read_stacked(file_path=filepath, sheet_name=sheet_name,
        slice_header=slice_header, slice_data=slice_data, map_header=map_header)

Check the new dataframe

.. ipython:: python
    :okexcept:

    df1a.head(5)

1B wide data: hgc.io.read_wide()
--------------------------------
It is also possible to read and reshape 'wide data', where all Features are in a separate column (so many values per row).
The function takes XLSX, XLS, CSV and dataframes (without headers!)
Let's look at the following example:

.. ipython:: python
    :okexcept:

    filepath = str(PATH/'examples/data/example1.xlsx')
    sheet_name = 'wide'
    map_header = {**hgc.io.default_map_header(),  # default headers
        'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}  # same as step 1A

We also need to define both the rows AND columns where to find the headers, features and units.

.. ipython:: python
    :okexcept:

    slice_header = [3, slice(2, 5)],  # the header is in row 3, from column 2 to 5
    slice_feature = [2, slice(5, None)],  # the feature names are in row 2, from column 5 untill the last column (<None> indicates last column here)
    slice_unit = [3, slice(5, None)],  # the units are in row 3, same columns as the features
    slice_data = [slice(4, 10)],  # the values are from row 4 untill the end of the file

For the wide format, the Feature, Unit and Value columns are automatically created and named correctly.
Others columns may be mapped.

.. ipython:: python
    :okexcept:

    map_header = {**hgc.io.default_map_header(),  # default headers
        'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}  # headers that need to be adjusted.

Now ready to read the wide data:

.. ipython:: python
    :okexcept:

    dfB_read = hgc.io.read_wide(file_path=filepath, sheet_name=sheet_name,
        slice_header=slice_header, slice_feature=slice_feature, slice_unit=slice_unit, slice_data=slice_data,
        map_header=map_header, )

Check the new dataframe

.. ipython:: python
    :okexcept:

    dfB_read.head(5)

1C Geophysical Exchange Files (GEF): hgc.io.read_gef()
------------------------------------------------------
We are currently constructing a function to read GEF files of the Dutch BRO (www.dinoloket.nl)

Example, how to import a single file

.. ipython:: python
    :okexcept:

    dfC_read = hgc.io.read_gef(file_path=PATCH/'examples/data/.........txt', format='NL_BRO2019')

By using the argument "folder_path" instead of "file_path",
the function automatically reads all GEF files in the folder, including subfolders.

.. ipython:: python
    :okexcept:

    dfC_read = hgc.io.read_gef(folder=str(PATH), format='NL_BRO2019')


Feature and unit in same column?
--------------------------------
Sometimes, the feature name and concentration are in the same column in stacked data
(or in the same row in wide data). In that case we recommend to first split the features
and units into separate columns using standard python functionalities. For example:

.. ipython:: python
    :okexcept:

    MyData = pd.DataFrame.from_dict({'Feature_Unit': ['mg NO3/L', 'mg SO4/L', 'mg PO4/L', 'mg O2/L'], 'value': [1., 2, 4.5, 5]})
    MyData['Feature'] = MyData['Feature_Unit'].str.split(' ',1).str[1].str.split('/').str[0]
    MyData['Unit'] = MyData['Feature_Unit'].str.split(' ').str[0] + '/' + MyData['Feature_Unit'].str.split('/').str[-1]

Note that it is NOT a problem to recognize UNITS when they include HGC-compatible macro-ions or atoms.
Thus, 'mg NO3/L', 'mg SO4/L', 'mg PO4/L', 'mg O2/L' can be used as input for hgc.ner.generate_unit_map() in step 3.
However, 'mg benzene/L', 'mg nitrate/L' will yield mistakes.


Step 2: Map Features
====================

:code:`hgc.named_entity_recognition.mapping.generate_feature_map()`
------------------------------
Next, we need to map the original features in the input file to new features that are recognizable by HGC.
The new feature names may include feature names that are outside the scope of HGC (e.g. micro-organisms or organic micro pollutants).

For this example, we will continue with the stacked data (step 1A).
We need to compile a list of features by slicing the "Features" column

.. ipython:: python
    :okexcept:

    lst_features = list(dfA_read['Feature'])  # must be a 'List'

In this example, we will use the default values to automatically detect the features.
That means we only need to define the "entity_org" argument with a list of original features.

.. ipython:: python
    :okexcept:

    feature_map, feature_unmapped, df_feature_map = hgc.named_entity_recognition.mapping.generate_feature_map(entity_orig=lst_features)

.. warning::

   it is recommended to manually check the mapped features before proceeding to the next step.

.. ipython:: python
    :okexcept:

    feature_map  # dictionary

We can also check for which original features the algorithm was NOT able to find a new feature.
In this case we find that the algorithm was not able to find a match for one
of the features ('EC new sensor').

.. ipython:: python
    :okexcept:

    feature_unmapped  # list

Hence, we need to update the dictionary manually.

.. ipython:: python
    :okexcept:

    feature_map = {**feature_map, 'EC new sensor': 'ec_field'}

The dataframe provides more details on what method was used to map the features, and why mapping certain features was usuccesfull:

.. ipython:: python
    :okexcept:

    df_feature_map

Default database with features and alias (alias_entity)
-------------------------------------------------------
The basis for several techniques to recognize features (see next paragraph) is a database table
with features and thier alias (synonyms). The database has different columns, that each
represents a different nomenclator. E.g.: "IUPAC" contains IUPAC names, "HGC" contains the
limited set of Features defined by HGC, and "SIKBomschrijving" the description given to features
in the datamodel of Dutch water laboratories.

.. ipython:: python
    :okexcept:

    hgc.constants.importdefaults.read_feature_mapping_table()

It is possible to specify what columns to use when applying :code:`hgc.named_entity_recognition.mapping.generate_feature_map()` through the
"alias_entity" argument. The following would ensure that only the "Feature" defined by the default
database and the "SIKBomschrijving" are used.

.. ipython:: python
    :okexcept:

    alias_entity={**dict_alias_features['Feature'], **dict_alias_features['SIKBomschrijving']}
    print(alias_entity)

of course, it is also possbile to enter a user defined alias-feature dictionary.

Tip: It is also possible to match using CAS-numbers. In that case you need to specify a different
alias_entity table and use the 'exact' method as match_method:

.. ipython:: python
    :okexcept:

    alias_entity={**dict_alias_features['CAS']}
    print(alias_entity)

dict_alias_features['Feature']


Recognizing features (match_method)
----------------------------------
The match_methode argument defines what Named Entity Recognition (NER) techniques to use.
There are various built in options, which the user may specify as a list. Methods are
executed according to the order of the list. For example:
['exact', 'ascii', 'Levenshtein', 'pubchempy', 'pubchempy_stripbrackets']

1. 'exact'
  With the 'exact' method, the script checks whether the original features matches exactly
  with one of the aliases in the alias_entity database.

2. 'ascii'
  The 'ascii' method is the same as the exact method, but after removal of non-ascii symbols and
  changing upper to lower case for both the original features and the features/ alias in the database.
  For example: '2,5-Xylidine' --> '2,5 xylidine'

3. 'Levenshtein'
  Is a Named Entity Recognition (NER) that uses Levenshtein Distance (fuzzywuzzy module) to calculate the
  differences between original entities and names in the alias_entity database. Original entities are
  matched to the HGC-entity to which they have the least distance, represented as a score. A better match
  results in a higher score. A match is only succesful if the score based on the Levenstein Distance
  remains above a certain score threshold. This threshold is at least 100% (for short names)
  and at least 85% (for longer names).

  Note that Levenshtein performs the matching after both original and new features are converted to ascii.
  The 'exact', 'ascii' and 'Levenshtein' method all use the aforementioned alias_entity table.

4. 'pubchempy'
  Features are translated (see source_language argument) and then matched with the chemical components
  and its synonyms in the pubchem database. Uses the get_compound function of the pubchempy module.
  This method thus ignores the user defined alias_entity database. returns the IUPAC name.

5. 'pubchempy_stripbrackets'
  Same as 'pubchempy', but after remove tekst between brackets.

Foreign languages (source_language)
----------------------------------
The user has the option to translate the original features to English before matching with
GoogleTrans by specifying the source_language (default = 'NL'). This argument only works
for the match_method 'google_translate'

other arguments
---------------

Check the documentation to find out the other options.


Step 3: Map Units
=================

hgc.ner.generate_unit_map()
---------------------------
The units need to be mapped in a similar fashion as the features. We will again use the default
arguments and check the resulting mapping:

.. ipython:: python
    :okexcept:

    lst_units = list(dfA_read['Unit'])  # must be a 'List'
    unit_map, unit_unmapped, df_unit_map = hgc.ner.generate_unit_map(unit_orig=lst_units)
    unit_map  # check results

For generating units, similar arguments can be specified as with generate_feature_map(). However, the match_method
'pubchempy' and 'pubchempy_stripbrackets' do not work. Hence, source language is also ignored.

.. warning::

   Replace the unit for pH, kve, pve by '1' to prevent problems with NaN errors

mg/L versus mg-N/L
~~~~~~~~~~~~~~~~~~
The script can recognize atoms in "concentrations as". It distuingishes between
"mg/L", "mg-N/L" (e.g. NO3, NH4), "mg-P/L" (e.g. PO4), "mg-S/L" (e.g. SO4), "mg-Si/L" (e.g. SiO2).

Step 4: Harmonize data
======================

hgc.io.harmonize()
-------------------
Now that we have defined the datamodel, we can harmonize the features and units to the defaults
used by HGC:
- map features
- map units
- correct values for change of units
    + mg/L to g/L -> factor 1000;
    + mg-N/L to mg/L for NO3 -> factor 62/14
    + mol/L to mg/L for NO3 -> factor 62 (molweight)
- specify datatype (string, value, datetime)
- drop rows without value or duplicates

The "<" sign is kept when the symbol is at position 1. Values with other symbols are treated
as NAN data.

Input data for this function must be as follows:
- separate columns for sampleID, Feature, Unit and Value.
- index must contain incrementing numbers 0,1,2,3,etc.

.. ipython:: python
    :okexcept:

    df_harmonized, dct_harmonized = hgc.io.harmonize(df_read=dfA_read,
        feature_map=feature_map, unit_map=unit_map)

The dataframe contains the harmonized data.
The dictionary contains rows that are dropped because they contain NAN or duplicate values

feature_units (argument)
------------------------
The function can only corrected values for the right units, when both the original and desired
units are known. The desired units are defined in the feature_unit map.

.. ipython:: python
    :okexcept:

    hgc.constants.importdefaults.dict_features_units()

The dictionary needs to be adjusted when adding new features.

.. warning::

   Units and values are NOT corrected for Features identified through the 'pubchempy' method.

column_dtype (argument)
-----------------------
Specify what datatype to use for each column. Default:

.. ipython:: python
    :okexcept:

    hgc.io.default_column_dtype()

Step 5: Convert to wide table
=============================

hgc.io.to_hgc()
---------------
Finally, we need to pivot the stacked data to the wide shaped table used by HGC.

.. ipython:: python
    :okexcept:

    df_hgc = hgc.io.stack_to_hgc(df_harmonized=df_harmonized)

index (argument)
----------------
The default is to use 'LocationID', 'Datetime' and 'SampleID' as index.

Combine step 1-5 with import_file()
===================================
HGC.io.import_file() is a convenience function that combines step 1 -5.


.. ipython:: python
    :okexcept:

    map_header = {**hgc.io.default_map_header(),
                  'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}

    df_harmonize, df_hgc, dct = hgc.io.import_file(file_path=str(PATH/'examples/data/example1.xlsx'),
                                                    sheet='stacked',
                                                    map_header=map_header2,
                                                    function='read_stacked',
                                                    stack_to_hgc=True)

The column '_Logging_' flags issues with harmonizing the Units and Values.
Upon inspection, we will see that there are flags raised:
- For "Reactive Yellow 3", the original units XXX are unknow and new features were
  not matched to new units because the feature was not predefined but found through
  the pubchempy matching method.
- "EC new sensor" is not recognized at all as feature.

.. ipython:: python
    :okexcept:

    df1[['Feature', '_Logging_']]

We can however facilitated recognition of "EC new sensor" as "ec_field", by adding
a dictionary with the original and new feature to the default arguments already
used by the :code:`hgc.named_entity_recognition.mapping.generate_feature_map()`  function:

.. ipython:: python
    :okexcept:

    import inspect

    def get_default_args(func):
        """Get the default arguments of a function as dictionary."""
        sig = inspect.signature(func)
        dct = {k: v.default for k, v in sig.parameters.items()
               if v.default is not inspect.Parameter.empty}
        return dct

    alias_entity2 = {**get_default_args(hgc.named_entity_recognition.mapping.generate_feature_map)['alias_entity'],  # get default values
                    'EC new sensor': 'ec_field'},  # User defined mapping of <original unit>: <new units>

Let's repeat the calculation, and check out the logging:

.. ipython:: python
    :okexcept:

    df_harmonize, df_hgc, dct = hgc.io.import_file(file_path=str(PATH/'examples/data/example1.xlsx'),
                                                   sheet='stacked',
                                                   map_header=map_header2,
                                                   alias_entity = alias_entity2
                                                   function='read_stack',
                                                   stack_to_hgc=True)
    df1[['Feature', '_Logging_']]

Note that it is also possible to enter the arguments for this function as a dictionary.
This can be handy when processing multiple files. Also, the dictionary may be stored
and reused when importing a similar file in the future.

.. ipython:: python
    :okexcept:

    dctA =
