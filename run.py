from turmeric import main

#r = main('netlists/FifthOrderLowpass.net', outfile='tmp')
r = main('netlists/AC/Butterworth5thOrderLP.net', outfile='tmp')

print(r['op'])