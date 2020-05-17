from turmeric import main

r = main('netlists/FifthOrderLowpass.net', verbose=3, outfile='tmp')

print(r['op'])