Modelling of robotic mail sorting center
========================================
### [Example 1](examples/random_direction_on_small.py) 
generates random marking for a map 3x3 and choses best. Result, where `+` is input, `-` is output:
```
BEST: 10.04 seconds per mail
|+|→| |←|+|
 ↑   ↓   ↑
| |←| |←| |
 ↓   ↓   ↑
|-|→| |→|-|
```

### [Example 2](examples/ant_on_small.py)
simple ant brain, same map. Result:
```
...
40 1829
41 1751
42 1771
43 1843
44 1728
45 1762
46 1873
47 1735
48 1811
49 1873
50 1733
average: 16.866250632484398 seconds per mail
```
