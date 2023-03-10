===
FAQ
===
Frequently Asked Questions

Where are total P and total N?
------------------------------
These are stored as the columns `P` and `N` respectively.

Which redox state is used for the phreeqc simulations?
------------------------------------------------------
It uses the default values as used by phreeqc itself, that is, `Fe(2)`, `As(3)` and `Mn(2)`.

Why does ammonium not contribute in the redox-equilibrium?
----------------------------------------------------------
This is by design as its kinetics are generally too slow. It is added as a
separate species in phreeqc (`Amm` instead of NH\ :sub:`4`\ \ :sup:`+`\ ).

How do I report alkalinity and/or bicarbonate (HCO\ :sub:`3`\ \ :sup:`-`\ )?
----------------------------------------------------------------------------
It is assumed everywhere that the HCO\ :sub:`3`\ \ :sup:`-`\  concentration
equals the alkalinity.

Why is my pH, temperature or other column not added to the SamplesFrame and/or recognized by HGC?
--------------------------------------------------------------------------------------------------
A common mistake is that the temperature is added with

.. code-block:: python

    df.temp = 10

But this is an invalid way of adding columns to a DataFrame and therefore, it is not recognized as a column
Instead, use

.. code-block:: python

    df['temp'] = 10