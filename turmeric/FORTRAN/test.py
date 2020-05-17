# req
import numpy as np
#################
import DC_SUBRS

# gmin test - rename to gmin cmin matrix?

gmin = 1e-12
N = 12
n_nodes = 4

print(DC_SUBRS.gmin_mat( gmin, N, n_nodes ))

# 

