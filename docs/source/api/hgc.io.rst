HGC.IO documentation (import functionality)

From experience, we know that each organization has its own different format and
data models to store water quality data. Importing data to a uniform database
that is suitable for analysis in HGC can therefore be quite cumbersome.

===================
Highlights
===================

The aim of this import module is to partly automate importing water quality data.
It takes csv and excel files. And can handle both ‘wide’ data formats (with each
parameter stored in a different column) and ‘stacked’ data formats where all data
is stored in 1 column. Features are automatically recognized using an algorithm
for named entity recognition.

===================
Steps
===================
Operating the import module typically involves 4 steps:
1. Map the features in the original file to features recognized by HGC with
“hgc.io. generate_feature_map()”. For example, “Iron”: “Fe”. Check the mapping
manually and adjust if necessary.
2. Map the units in the original file to units recognized by HGC with “hgc.io.
generate_unit_map()”. For example, “mg-NO3/L”: ”mg/L”. Check the mapping manually
and adjust if necessary.
3. Read the original file and and convert the data with “hgc.io.import_file()”
4. Convert the imported data to a dataframe in HGC wide format with “hgc.io.to_hgc()”

===================
Example: import stacked data
===================
Let’s try using an excel file with stacked data as example.

----------------------
Step 1: hgc.io. generate_feature_map()
----------------------
First map the features in the original file, to feature names recognized by HGC.
"""


import pandas as pd
import hgc

# compile a list of features by slicing the original file
lst_features = list(pd.read_excel(r'd:\hgc\testfiles\example1.xlsx', sheet_name='stacked')['Feature'])

# automatically detect features using text recognition
feature_map, feature_unmapped, df_feature_map = hgc_ner.generate_feature_map(entity_orig=lst_features)

"""
Then we need to check whether the features are correctly mapped. And whether certain 
features did not meet the minimum score. 
"""

# check if features are correctly mapped
print(feature_map)

# check for which features the algorithm was not able to find a match that met the minimum resemblance.
print(feature_unmapped)

# The dataframe can be used to check in more detail the scores how well the original features were matched to HGC features. This can be handy if you want to identify common errors and update the underlying database.
print(df_feature_map)

"""
In this case we find that the algorithm was not able to find a match for one 
of the features ('EC new sensor'). Hence, we need to adjust the mapping manually.
"""

# manually adjust the mapping by merging with a user defined dictionary (optional)
feature_map2 = {**feature_map, 'EC new sensor': 'ec_field'}

"""
----------------------
Step 2: hgc.io. generate_unit_map()
----------------------

Next, we need to make a mapping for the units, using the same approach as for the features. 
"""

lst_units = list(pd.read_excel(r'd:\hgc\testfiles\example1.xlsx', sheet_name='stacked')['Unit'])
unit_map, unit_unmapped, df_unit_map = hgc_ner.generate_unit_map(entity_orig=lst_units)
print(unit_map)

"""
----------------------
Step 3: hgc.io.import_file()
----------------------

The third step is to read the original file and and convert the data to the desired 
datamodel. This requires that we first tell python where to find the data and how to 
convert it.
"""

# Arguments defining where to find data
slice_header = [0, slice(0, 6)]  # row 0
slice_data = [slice(1, None)]  # row 1 till end of file. Use "None" instead of “:” when slicing

# Arguments how to convert the data

# map_header -->  mapping how to adjust headers name
# Note: The headers 'Value', 'Unit' and 'SampleID' are compulsory. Other headers can be any string
map_header = {**hgc_io.default_map_header(), 
              'loc.': 'LocationID', 'date': 'Datetime', 'sample': 'SampleID'}

# map_features --> see step 1
# map_units --> see step 2

# feature_units -->  mapping of the desired units for each feature
# We can inspect the default units for Cl, NO3 and ec_field
print(dict((key, hgc_io.default_feature_units()[key]) for key in ['Cl', 'NO3', 'ec_field']))

# column_dtype --> desired dtypefor columns
# we will use the default dtype
print(hgc_io.default_column_dtype())  # use default values

"""
Now the we have defined all the arguments, lets import the data
"""

df = hgc_io.import_file(file_path=r'd:\hgc\testfiles\example1.xlsx',
                    sheet_name='stacked',
                    shape='stacked',
                    slice_header= slice_header,
                    slice_data=slice_data,
                    map_header=map_header,
                    map_features=feature_map2,
                    map_units=unit_map)[0]
"""
Note that we put a '[0]' behind the function, the [1] and [2] are the data
that was dropped because duplicate or nan_value

----------------------
Step 4: hgc.io.to_hgc()
----------------------
Finally, we need to pivot the stacked data to the wide dataframe used by HGC.
The default is to use 'LocationID', 'Datetime' and 'SampleID' as index.
"""

df_hgc = hgc_io.stack_to_hgc(df)

"""
===================
Example: import wide data
===================

Next, we will import the same data, but from a ‘wide’ shaped file.

Note that it is also possible to use a dataframe instead of excel or csv as input
for hgc.io.import_file(). This requiresusing the argument “dataframe” instead of “file_name”.
An advantage of this approach is to prevent repeatedly reading the input file .
"""

df_temp = pd.read_excel(r'd:\hgc\testfiles\example1.xlsx', sheet_name='wide', header=None) # ignore headers!

# step 1: generate feature map
feature_map2, feature_unmapped2, df_feature_map2 = hgc_ner.generate_feature_map(entity_orig=list(df_temp.iloc[2, 5:]))

# step 2: generate unit map
unit_map2, unit_unmapped2, df_unit_map2 = hgc_ner.generate_unit_map(entity_orig=list(df_temp.iloc[3, 5:]))

# step 3: import file
df2 = hgc_io.import_file(dataframe=df_temp,
                          shape='wide',
                          slice_header=[3, slice(2, 5)],
                          slice_feature=[2, slice(5, None)],
                          slice_unit=[3, slice(5, None)],
                          slice_data=[slice(4, None)],
                          map_header={**hgc_io.default_map_header(), 'loc.': 'LocationID',
                                      'date': 'Datetime', 'sample': 'SampleID'},
                          map_features={**feature_map2, 'EC new sensor': 'ec_field'},
                          map_units=unit_map2)[0]

# step 4: cpnvert to wide format
df2_hgc = hgc_io.stack_to_hgc(df2)

