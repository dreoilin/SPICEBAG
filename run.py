"""
Running turmeric as a python module
"""

# You can import the turmeric module using this command
from turmeric import main


# a simulation is run as follows:
#   main(<netlist>, <ourprefix>)
#   Our netlist syntax is described in the accompanying report
results = main('netlists/AC/bw5lp.net', outprefix="tmp")

# the results of a simulation (or simulations) are formatted as
# a dictionary

print("The voltage on node 5")
#             <sim><variable>
print(results['AC']['V(5)'])

import matplotlib.pyplot as plt
import numpy as np

f = np.absolute(results['AC']['f'])
V = np.absolute(results['AC']['V(5)'])
plt.semilogx(f, V)

plt.title("Frequency response of a 5th Order LP Butterworth")
plt.ylabel("Vout")
plt.xlabel("f [Hz]")
