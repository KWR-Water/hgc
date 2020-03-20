# <codecell>
import pandas as pd
import hgc
# <markdowncell>
# # PHREEQC integration with HGC
# ## Basics
# Create some test data

# <codecell>

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
#df.hgc.make_valid()
#df.hgc.consolidate(use_ph='lab', use_ec='lab', use_temp=None,
                       use_so4=None, use_o2=None)

# <markdowncell>
# With this DataFrame, we can do some PHREEQC calculations. For example,
# we can calculate the saturation index of different minerals like Calcite:

# <codecell>

    #df.hgc.get_phreeqpython_solutions()
    # si_calcite = df.hgc.get_saturation_index('Calcite')
    #si_calcite



# %%
