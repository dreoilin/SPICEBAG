from turmeric import main

#r = main('netlists/FifthOrderLowpass.net', outfile='tmp')
r = main('netlists/AC/diodemulti.net', outfile='tmp')

print(r['op'])