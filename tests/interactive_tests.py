# <markdowncell>
# # Some test to see if the tool is behaving properly in interactive mode
# The behavior in interactive mode is not always possible (or at least nor
# easyily) to test with pytest

# <codecell>
import hgc
import pandas as pd
from pathlib import Path
# %load_ext autoreload
# %autoreload 2

try:
    test_directory = Path(__file__).parent
except:
    test_directory = Path('.').parent

# <markdowncell>
# ## Test loggers
# test whether messages are logged to the screen
# ## This should print some logging of level INFO

# <codecell>
df = pd.read_csv(test_directory / 'data' / 'dataset_basic.csv',
                    skiprows=[1], index_col=None)
df[df.hgc.hgc_cols] = df[df.hgc.hgc_cols].astype(float)
df.hgc.make_valid()
df.hgc.consolidate(inplace=True, use_so4=None, use_ph='lab')

# <markdowncell>
# # Test printing of SamplesFrame with PhreeqPython solutions

# <codecell>
df.hgc.get_phreeqpython_solutions()
df.pp_solutions

# <markdowncell>
# ### Show info about validation

# <codecell>
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
df.hgc.make_valid()
# %%
