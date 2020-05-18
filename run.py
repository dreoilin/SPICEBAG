from turmeric import main

r = main('netlists/FifthOrderLowpass.net', outfile='tmp')

print(r['op'])