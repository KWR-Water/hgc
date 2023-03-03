# <markdowncell>
# # Some test to see if the tool is behaving properly in interactive mode
# The behavior in interactive mode is not always possible (or at least nor
# easyily) to test with pytest

# <codecell>
import hgc
import pandas as pd
from pathlib import Path

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

# %%
