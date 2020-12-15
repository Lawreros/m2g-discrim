import numpy as np
import os, ssl
import boto3
import csv
import networkx as nx
#from nxviz import CircosPlot
from matplotlib import pyplot as plt
from m2g.utils.cloud_utils import get_matching_s3_objects
from m2g.utils.cloud_utils import s3_client
from graspy.utils import pass_to_ranks

from math import floor
import igraph as ig
import plotly
import plotly.offline as py
from plotly.graph_objs import *


##-----------DIFFUSION DISCRIM--------------------##



##-----------FUNCTIONAL DISCRIM-------------------##

func_datasets=['What','Ever','Boomer']
dsizes=[2,3,400]
func_atlases=['Supa','Mario','Bros']
tot=sum(dsizes)

SWU1 = [0.3, 0.9, 0.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
SWU2 = [0.4, 1, 0.3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]


x = np.arange(35)
i = 0
q = [0]
qq = []
for idx, st in enumerate(dsizes):
    q.append(st+i)
    if idx == 0:
        qq.append(0.5*st)
    else:
        qq.append(sum(dsizes[:idx])+(0.5*st))
    i=i+st
y = np.array(q)
yticks = np.array(qq)

X,Y = np.meshgrid(x,y)

Z=np.zeros((len(y),len(x)))

Z[0] = np.array(SWU1)
Z[1] = np.array(SWU2)

fig, ax = plt.subplots()
plt.pcolormesh(X,Y,Z,cmap='PiYG')
ax.set_xticks(np.arange(0.5,len(func_atlases)+0.5,1))
ax.set_yticks(np.array(yticks))

ax.set_xticklabels(np.array(func_atlases))
ax.set_yticklabels(np.array(func_datasets))

ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
plt.setp(ax.get_xticklabels(), rotation=-30, ha="right", rotation_mode="anchor")


ax.set_aspect(aspect=0.05)

#plt.colorbar()
plt.savefig('/qwop.png')

print('stop')


