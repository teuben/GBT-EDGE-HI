#! /usr/bin/env dysh
#
#  See bug https://github.com/GreenBankObservatory/dysh/issues/702
#
#  until this works, use:    ipython --profile=dysh test1.py

print("test dysh for GBT_EDGE_HI")

f1=dysh_data('AGBT15B_287_19')
sdf1 = GBTFITSLoad(f1)
print("SDF1:",sdf1.filename)

# silly?
# print(sdf1.get_summary())

sdf1.summary()
