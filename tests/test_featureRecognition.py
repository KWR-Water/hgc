''' Contains test on feature recognition'''
import pytest
import pandas as pd
# import os
from pathlib import Path
import pickle as pckl
from hgc.feature_recognition import * 

def test_feature_map():
    # %% unit test

    # test if all HGC features are included in df_feature_alias
    # ...... @Xin/ MartinK ...........

    # test if data is correctly read
    feature_orig = list(pd.read_excel(r'.\hgc\constants\default_mapping.xlsx').iloc[2, slice(5, 999)].dropna())
    feature_map, feature_unmapped, df_feature_map = generate_feature_map(entity_orig=feature_orig)

    unit_orig = list(pd.read_excel(r'.\hgc\constants\default_mapping.xlsx').iloc[3, slice(5, 999)].dropna())
    unit_map, unit_unmapped, df_unit_map = generate_unit_map(entity_orig=unit_orig)

    assert feature_map['Acidity'] == 'ph'
    assert feature_map['ec_lab'] == 'ec_lab'
    assert unit_map['mS/m'] == 'mS/m'
    assert unit_map['μmol N/l'] == 'μmol/L N'

    # Next version: add unit test of the "score" computed by the generate_untity_map function

# %% other test data

# vitens1 = pd.read_csv(r'D:\HGC\test\vitens_lims.csv', header=None, encoding='ISO-8859-1').iloc[1, slice(11, 999)].dropna()
# vitens2 = pd.read_csv(r'D:\HGC\test\vitens_lims.csv', header=None, encoding='ISO-8859-1').iloc[2, slice(11, 999)].dropna()
# wml = pd.read_csv(r'D:\HGC\test\AQZ_Data_Combined.csv', encoding='ISO-8859-1')['PARAMETER OMSCHRIJVING'].dropna().astype('string').unique()

# feature_orig2 = list(vitens1.astype('string')) + list(vitens2.astype('string')) + list(wml)
# feature_orig2 = list(feature_orig2[500:700])  # take a subset for testing !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# feature_map2, feature_unmapped2, df_feature_map2 = generate_feature_map(entity_orig=feature_orig2)

# wml_unit = list(pd.read_csv(r'D:\HGC\test\AQZ_Data_Combined.csv', encoding='ISO-8859-1')['EENHEID'].dropna().astype('string').unique())
# vitens_unit = pd.read_csv(r'D:\HGC\test\vitens_lims.csv', header=None, encoding='ISO-8859-1').iloc[4, slice(11, 999)].dropna()

# unit_orig2 = list(set(list(vitens_unit.astype('string')) + list(wml_unit)))

# unit_map2, unit_unmapped2, df_unit_map2 = generate_unit_map(entity_orig=unit_orig2)


# %% test fuzzywuzzy function

# text = df_feature_map['Feature_orig'].values

# wordcloud = WordCloud().generate(str(text))

# plt.imshow(wordcloud)
# plt.axis("off")
# plt.show()

# f1 = "abcd efgh"
# f2 = "bacd efgh"
# f3 = "efgh abcd"
# f4 = "efgh_bacd"

# f1 = "1234 5678"
# f4 = "5678 2134"
# f1 = "hydroxidodioxidocarbonate(1−)"
# f4 = "hydroxidodioxidocarbonate 1"

# fuzz.ratio(f1, f2)
# fuzz.ratio(f1, f3)
# fuzz.ratio(f1, f4)
# fuzz.partial_ratio(f1, f2)
# fuzz.partial_ratio(f1, f3)
# fuzz.partial_ratio(f1, f4)
# fuzz.token_sort_ratio(f1, f2)
# fuzz.token_sort_ratio(f1, f3)
# fuzz.token_sort_ratio(f1, f4)

# feature_alias = [f2, f3, f4]
# feature_orig = [f1, f2]
# feature_orig2alias = []
# for orig in feature_orig:
# feature_orig2alias.append(process.extractOne(feature_orig, feature_alias, scorer=fuzz.token_sort_ratio))
