# GBT-EDGE-HI

HI survey of EDGE galaxies.   Started with AGBT15B_287, where 100+ galaxies were
observed in a modified PositionSwitch using ON-OFF-ON and a corresponding getsigref
procedure


## Example

Make sure your data is in the `$SDFITS_DATA` directory.
If you use $DYSH_DATA, they
can also be located in the `$DYSH_DATA/sdfits` directory



```
f1=dysh_data('AGBT15B_287_19')
sdf1 = GBTFITSLoad(f1)
sdf1.filename
```

but for now the following
is a bug/feature (see https://github.com/GreenBankObservatory/dysh/issues/740)

```
unset DYSH_DATA
export SDFITS_DATA=/home/teuben/GBT/dysh_data/sdfits
dysh
  f2=dysh_data('AGBT15B_287_19')
  sdf2=GBTOffline('AGBT15B_287_19')
  sdf2.filename

  f1=dysh_data('AGBT15B_287_19', dysh_data='/home/teuben/GBT/dysh_data/')

```
