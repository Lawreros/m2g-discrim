import numpy as np
import os, ssl
import boto3
import csv
import networkx as nx
from nxviz import CircosPlot
from matplotlib import pyplot as plt
from m2g.utils.cloud_utils import get_matching_s3_objects
from m2g.utils.cloud_utils import s3_client
from graspy.utils import pass_to_ranks

from math import floor
import igraph as ig
import plotly
import plotly.offline as py
from plotly.graph_objs import *

# Find list of files
# Average ndarray rows

Connections = {}
ind_Connections={}

bucket = 'ndmg-data'
paths = ['ABIDEII-BNI_1/ABIDEII-BNI_1-m2g-dwi-04-15-20-csa-det-native/',
        'XHCUMS/XHCUMS-m2g-dwi-05-03-20-csa-det-native']

localpath = '/input'
datasets = ['BNU1','BNU3']
dsize = [100,144]
atlas = 'Desikan'



ADJMATRIX = True

#Calculate total size of scans
tot = sum(dsize)

means = OrderedDict()
var = OrderedDict()

for idx, dset in dataset:
    # get list of all files belonging to atlas:
    connectomes = os.listdir(f"{localpath}/{dset}/{atlas}")

    if idx==0:
        mean_files.append([f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "mean-ptr" in name])
        var_files.append([f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "var-ptr" in name])
    else: # itterate through list and calculate mean and variance of edgelist
        mean_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "mean-ptr" in name]
        var_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "var-ptr" in name]
    

list_of_arrays, verts = import_edgelist(files_, delimiter=" ", return_vertices=True)
if not isinstance(list_of_arrays, list):
    list_of_arrays = [list_of_arrays]

ptr_list_of_arrays = np.array([pass_to_ranks(array) for array in list_of_arrays])

stack = np.atleast_3d(list_of_arrays)
ptr_stack = np.atleast_3d(ptr_list_of_arrays)

N, _, _ = stack.shape

#Calculate mean and variance:
mean = np.mean(stack, axis=0)
var = np.var(stack, axis=0)
ptr_mean = np.mean(ptr_stack, axis=0)
ptr_var = np.var(ptr_stack, axis=0)

#Check that number of vertices and dimensions of averaged connectomes match up
if len(verts) != mean.shape[0]:
    print(f'WARNING: Number of nodes and dimension of connectome do not match for: {atlas}!')

np.savetxt(f"{output_dir}/{atlas}/verts.csv", verts, fmt='%d', delimiter=" ")

#Convert matrix to edgelists
a = sum(range(1, len(verts)))
arr = np.zeros((a,3))
z=0
for num in range(len(mean)):
    for i in range(len(mean[num])):
        if i > num:
            #print(f'{num+1} {i+1} {my_data[num][i]}')
            arr[z][0]= f'{int(verts[num])}'#f'{num+1}'
            arr[z][1]= f'{int(verts[i])}'
            arr[z][2] = mean[num][i]
            z=z+1
    




qq=0
for p in paths:
    all_files = get_matching_s3_objects(bucket,p,suffix="csv")
    for fi in all_files:
        client.download_file(bucket, fi, f"{localpath}/con_avg/{qq}.csv")
        print(f"Downloaded {qq}.csv")
        ind_Connections=np.zeros((71,71))

        #networkx.read_edgelist(f'{localpath}/con_avg/{qq}.csv', delimiter=',')
        with open(f'{localpath}/con_avg/{qq}.csv', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                edges = str(row).split("'")[1]
                a = int(edges.split(' ')[0])
                b = int(edges.split(' ')[1])
                weight = float(edges.split(' ')[2])

                #if a not in ind_Connections.keys():
                #    ind_Connections[a]={}
                #    ind_Connections[a][b] = np.zeros(0)
                #elif b not in ind_Connections[a].keys():
                #    ind_Connections[a][b] = np.zeros(0)

                #ind_Connections[a][b] = np.append(ind_Connections[a][b],[weight])

                ind_Connections[a][b] = weight


        r,c = ind_Connections.shape
        for k in range(1,r):
            for j in range(k+1,c):
                if str(k) not in Connections.keys():
                    Connections[str(k)]={}
                    Connections[str(k)][str(j)] = np.zeros(0)
                elif str(j) not in Connections[str(k)].keys():
                    Connections[str(k)][str(j)] = np.zeros(0)

                Connections[str(k)][str(j)] = np.append(Connections[str(k)][str(j)],[ind_Connections[k][j]])

        os.remove(f'{localpath}/con_avg/{qq}.csv')
        qq=qq+1



#Calculate average connections and make it into a matrix

heatmap = np.zeros((71,71))
edgeweights = list()
edge_colors = {}

if ADJMATRIX:
    for k in Connections:
        for j in Connections[k]:
            heatmap[int(k)][int(j)] = np.average(Connections[k][j])
            heatmap[int(j)][int(k)] = np.average(Connections[k][j])
else:
    for k in Connections:
        for j in Connections[k]:
            if np.average(Connections[k][j]) > 0.8:
                heatmap[int(k)][int(j)] = np.average(Connections[k][j])*4
            elif np.average(Connections[k][j]) <= 0.8 and np.average(Connections[k][j]) > 0.5:
                heatmap[int(k)][int(j)] = np.average(Connections[k][j])/2
            else:
                heatmap[int(k)][int(j)] = 0
            edgeweights.append(np.average(Connections[k][j]))


##### Heatmap Generation

#https://stackoverflow.com/questions/43290853/how-to-create-heat-map-from-irregular-xyz-data-in-pyplot
#https://matplotlib.org/3.3.3/api/_as_gen/matplotlib.pyplot.pcolormesh.html
#https://matplotlib.org/3.1.1/gallery/images_contours_and_fields/image_annotated_heatmap.html


if ADJMATRIX:
#Generate labels for figure
    atlases=list()
    for i in range(0,71):
        atlases.append(str(i))

    fig, ax = plt.subplots()
    im = ax.imshow(heatmap, cmap="gist_heat_r") #Can specify the colorscheme you wish to use
    ax.set_xticks(np.arange(len(atlases)))
    ax.set_yticks(np.arange(len(atlases)))

    ax.set_xticklabels(atlases)
    ax.set_yticklabels(atlases)

    #Label x and y-axis, adjust fontsize as necessary
    plt.setp(ax.get_xticklabels(), fontsize=6, rotation=90, ha="right", va="center", rotation_mode="anchor")
    plt.setp(ax.get_yticklabels(), fontsize=6)

    plt.colorbar(im, aspect=30)
    ax.set_title("Averaged Connections")
        
    fig.tight_layout()

    plt.show()

    plt.savefig(f'{localpath}/con_avg/heatmap.png', dpi=1000)

##### END

print('oof')