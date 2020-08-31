# This is necessary so you can use `import hgc` and then
# all dataframes created afterwards are extended with the
# hgc namespace
from hgc.samples_frame import SamplesFrame

name = "hgc"

# allow access to mw and units via a shortcut hgc.mw
from hgc.constants.constants import mw, units