import statistics
import matplotlib.pyplot as plt
import numpy as np
#################
import LINALG
import time


sizes = []
time_f = []
time_np = []
dev_f = []
dev_np = []
for n in range(5, 90, 3):
    sizes.append(n)
    tmp = []
    for j in range(5):
        # create an nxn matrix
        A = np.random.rand(n*n).reshape([n,n])
        b = np.random.rand(n*1).reshape([n,1])
    
        tic = time.perf_counter()
        LU, INDX, D, C = LINALG.ludcmp(A)
        SOL = LINALG.lubksb(LU, INDX,  b)
        toc = time.perf_counter()
        tmp.append(toc-tic)
    
    time_f.append(statistics.mean(tmp))
    dev_f.append(statistics.stdev(tmp))
    tmp = []
    for j in range(5):
        tic = time.perf_counter()
        SOL = np.linalg.solve(A, b)
        toc = time.perf_counter()
        tmp.append(toc-tic)
    
    time_np.append(statistics.mean(tmp))
    dev_np.append(statistics.stdev(tmp))
    
fig = plt.figure()
ax1 = fig.add_subplot(111)

#ax1.scatter(sizes, time_f, s=10, c='b', marker="s", label='LINALG.lu')
#ax1.scatter(sizes, time_np, s=10, c='r', marker="o", label='np.linalg.solve')
ax1.errorbar(sizes, time_f, yerr=dev_f,xerr=0,linestyle='None', c='b', marker="o", label='LINALG.lu')
ax1.errorbar(sizes, time_np, yerr=dev_np,xerr=0,linestyle='None', c='r', marker="o", label='np.linalg.solve')
ax1.set_xlabel("size [n]")
ax1.set_ylabel("time [s]")
ymax = max(max(time_f), max(time_np))*1.5
ax1.set(ylim=(0, ymax))
plt.legend(loc='upper left');
plt.title("Turmeric LU vs. np.linalg.solve")
plt.show()