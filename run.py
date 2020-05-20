from turmeric import main

#r = main('netlists/FifthOrderLowpass.net', outfile='tmp')
r = main('netlists/diodemulti.net', outfile='tmp')

print(r['op'])