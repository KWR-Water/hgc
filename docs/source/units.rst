.. _Units:

========
Units
========
An overview of the used units of all columns in a SamplesFrame.

Atoms
---------

.. ipython:: python

    import pandas as pd
    from hgc.constants import constants
    {a: constants.units(a) for a in constants.atoms}

Ions
---------

.. ipython:: python

    import pandas as pd
    from hgc.constants import constants
    {a: constants.units(a) for a in constants.ions}

Other properties
-----------------

.. ipython:: python

    import pandas as pd
    from hgc.constants import constants
    {a: constants.units(a) for a in constants.properties}