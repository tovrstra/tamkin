%chk=gaussian.chk
%nproc=1
%mem=500MB
# HF/3-21G opt(modredundant,tight) int=ultrafine scf(tight) maxdisk=12GB NoSymm

Who cares about the title?

0 1
  C        15.0000001126       15.0000000000       14.2351033511
  C        14.9999998874       15.0000000000       15.7648966489
  H        16.0416717620       15.0000000000       13.8490027805
  H        13.9583282380       15.0000000000       16.1509972195
  H        15.5208355692       14.0978859230       16.1509975512
  H        15.5208355692       15.9021140770       16.1509975512
  H        14.4791644308       14.0978859230       13.8490024488
  H        14.4791644308       15.9021140770       13.8490024488

D 5 2 1 7 S 30 2.0 

