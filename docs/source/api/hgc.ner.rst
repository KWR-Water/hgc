===================
Mapping feature
===================

The funtions generate_feature_map() and generate_unit_map() use Named Entity
Recognition (NER) techniques to match original entities to the entities used by HGC.
It is based on the fuzzywuzzy module. And uses Levenshtein Distance to calculate the differences between
original entities and HGC-compatible entities. Original entities are matched to the HGC-entity to which they
have the least distance. A match is only succesful if the score based on the Levenstein Distance remains above
a certain threshold.


For the features, a default database has been provided with the module that contains
both features and a selection of alias (synonyms). The NER function will try find which
alias provides the best match (= highest score) for each original feature.

"""

# Print first lines of default database for mapping features.
print(hgc_ner.default_feature_alias_dutch_english.head())

"""
By default, all columns are used except for 'CAS'.

It is possible to change the selection of colums through the argument 'alias_cols'
In the next example, we will attempt mapping using the CAS number.

"""

# example with mapping with CAS number
df_feature_alias = hgc_ner.generate_entity_alias(
    df=hgc_ner.entire_feature_alias_table,
    entity_col='Feature',
    alias_cols=['CAS'])

feature_map3, feature_unmapped3, df_feature_map3 =\
    hgc_ner.generate_feature_map(entity_orig=list(df_temp.iloc[1, 5:]),
                                 df_entity_alias=df_feature_alias,
                                 match_method='exact')

# check if features are correctly mapped
print(feature_map3)

"""
The results of the mapping with CAS number are very poor compared to the previous
mapping. This is logical in this case, since there are no CAS numbers in the
original file.

Note that in this case we will adjust the argument 'match_method' to 'exact'
This works faster, but features must be spelled exactly the same as in the feature list. The mapping method can be
adjusted with the argument .

It is also possible to load a user defined database with the argument
'df_entity_alias'.

===================
Mapping units
===================

For mapping units, similar functionalities are availabe as for mapping features.
Only with a differente database and alias_cols

"""

# Print first lines of default database for mapping units.
print(hgc_ner.default_unit_alias.head())


"""
WARNING: 
give pH as units '1'
same for kve, pve, etc. replace them by '1' to prevent problems with NaN errors
"""
