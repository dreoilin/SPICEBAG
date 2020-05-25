from turmeric import main

#r = main('netlists/FifthOrderLowpass.net', outfile='tmp')
r = main('netlists/OP/diodemulti.net', outfile='tmp')

print(r['op'])