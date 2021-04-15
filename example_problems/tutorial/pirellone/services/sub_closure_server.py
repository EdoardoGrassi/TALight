#!/usr/bin/env python3
# METADATA OF THIS TAL_SERVICE:
problem="pirellone"
service="sub_closure"
args_list = [
    ('m',int), 
    ('n',int),
    ('goal',str),
    ('submatrix_type',str),
    ('lang',str),
    ('ISATTY',bool),
]

from sys import stderr, exit, argv
import random
import copy
import pirellone_lib as pl
from TALinputs import TALinput
from multilanguage import Env, Lang, TALcolors
ENV =Env(problem, service, args_list)
TAc =TALcolors(ENV)
LANG=Lang(ENV, TAc, lambda fstring: eval(f"f'{fstring}'"))
TAc.print(LANG.opening_msg, "green")

# START CODING YOUR SERVICE: 


m=ENV['m'] 
n=ENV['n'] 

TAc.print(LANG.render_feedback("instance",f"Instance {m}x{n}: "), "yellow", ["bold"])
pirellone,_,sr,sc=pl.random_pirellone(m, n, solvable=True,s=True)
pl.print_pirellone(pirellone)
TAc.print(LANG.render_feedback("instance-sol","Solution of instance: "), "yellow", ["bold"])
print(" ".join(pl.solution_irredundant(pirellone,sr,sc)))
sub_n=random.randint(2, n-1)
sub_m=random.randint(2, m-1)
sub_pirellone=[[0 for j in range(0,sub_n)] for i in range(0,sub_m)]
if ENV['submatrix_type']=='consecutive':
    for i in range(0,sub_m):
        for j in range(0,sub_n):
            sub_pirellone[i][j]=pirellone[i][j]
elif ENV['submatrix_type']=='any':
    r=[]
    c=[]
    for i in range(m):
        r.append(i)
    for j in range(n):
        c.append(j)
    sub_r=random.sample(r, sub_m)
    sub_c=random.sample(c, sub_n)
    u=[]
    v=[]
    for i in sub_r:
        u.append(i)
    for j in sub_c:
        v.append(j)
    u.sort()
    v.sort()
    h=0
    k=0
    for i in u:
        for j in v:
            sub_pirellone[h][k]=pirellone[i][j]
            k+=1
        k=0
        h=+1
     
TAc.print(LANG.render_feedback("sub-matrix",f"Submatrix {sub_m}x{sub_n}"), "yellow", ["bold"])   
pl.print_pirellone(sub_pirellone)     
TAc.print(LANG.render_feedback("bub-matrix-sol",f"Solution of the submatrix {sub_m}x{sub_n} : "), "yellow", ["bold"])
solu=input()
solu=solu.split()
b,solvable=pl.check_off_lights(sub_pirellone,solu)
if b and solvable=='s':
    TAc.OK()
    TAc.print(LANG.render_feedback('correct',"This sequence turns off all lights."), "green", ["bold"])
if b==False and solvable=='s':
    TAc.NO()
    TAc.print(LANG.render_feedback('not-correct',"This sequence doesn't turn off all lights see what happens using your solution:"), "red", ["bold"])
    pl.print_pirellone(sub_pirellone)    

if b and solvable=='n':
    TAc.OK()
    TAc.print(LANG.render_feedback('no-more-lights',"You can not turn off more lights."), "green", ["bold"])
if b==False and solvable=='n':
    TAc.NO()
    TAc.print(LANG.render_feedback('do-better',"You can turn off more lights, check it: "), "red", ["bold"])
    pl.print_pirellone(sub_pirellone)  
    
exit(0)
