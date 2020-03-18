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
separate species in phreeqc (`Amm` instead of `NH<sub>4</sub><sup>+</sup>`).

