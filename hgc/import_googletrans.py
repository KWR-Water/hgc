import pubchempy as pcp
from googletrans import Translator
# examples:
# 1,2,3-trimethylbenzeen           1,2,4-trimethylbenzeen               1,3,5-trimethylbenzeen               1,2,3,4-tetramethylbenzeen      1,2,3,5-tetramethylbenzeen      1,2,4,5-tetramethylbenzeen      2-ethyltolueen

translator = Translator()
name1 = translator.translate('1,2,3-trimethylbenzeen', src='nl', dest='en')
name2 = translator.translate('1,2,3,4-tetramethylbenzeen', src='nl', dest='en')
name1.text # here we got them in English 

idx = pcp.get_compounds(name1.text, 'name') # recognize this component by pubchempy
c = pcp.Compound.from_cid(idx[0].cid) # get cid and formularized compounds 
c.molecular_formula
c.molecular_weight
c.iupac_name
c.synonyms
