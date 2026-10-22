#  Inverting spectrum to get a radial profile

Following Wen et al (in prep) we here tighten the inversion by assuming a rotation curve, for
example based on the Universal Rotation Curve (URC) relationship.


## Simulation

Using `hi_profile.py` we can forward model as follows

      ./hi_profile.py

which create a number of tables usefule to check the inversion:

1.  hi_profile_rv.tab - rotation curve
2.  hi_profile_sv.tab - spectrum
3.  hi_profile_sv0.tab - one sided spectrum
4.  hi_profile_rdv.tab - radius_density_velocity table

Now the same script can be used for the inversion

      ./hi_profile.py --rvfile  hi_profile_rv.tab  --invert  --reg 0.1

or using a single sided spectrum

      ./hi_profile.py  --rvfile  hi_profile_rv.tab  --svfile  hi_profile_sv0.tab --reg 0.1
