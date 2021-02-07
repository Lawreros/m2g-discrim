import numpy as np
import os, ssl
import boto3
import csv
import networkx as nx
from matplotlib import pyplot as plt
from graspy.utils import pass_to_ranks
from graspy.utils import import_edgelist

from math import floor
import igraph as ig
from plotly import tools
import plotly.offline as py
from plotly import graph_objects as go
#from plotly.graph_objs import *

# Find list of files
# Average ndarray rows

localpath = '/discrim-data/diffusion'
datasets = ['SWU4','HNU1','NKIENH','XHCUMS','BNU1','BNU3','IPCAS8','NKI1','NKI24','MRN1']
dsize = [382,298,192,120,114,46,40,36,36,20]
atlas = 'Desikan_space-MNI152NLin6_res-2x2x2'

#Calculate total size of scans
tot = sum(dsize)

for idx, dset in enumerate(datasets):
    # get list of all files belonging to atlas:
    connectomes = os.listdir(f"{localpath}/{dset}/{atlas}")

    if idx>0:
        for name in connectomes:
            if "mean-ptr" in name:
                mean_files.append(f"{localpath}/{dset}/{atlas}/{str(name)}")
            if "variance-ptr" in name:
                var_files.append(f"{localpath}/{dset}/{atlas}/{str(name)}")
        
    else: # itterate through list and calculate mean and variance of edgelist
        mean_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "mean-ptr" in name]
        var_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "variance-ptr" in name]
    

# Create the weighted averages for mean and variance
list_of_means, verts = import_edgelist(mean_files, delimiter=" ", return_vertices=True)
if not isinstance(list_of_means, list):
    list_of_means = [list_of_means]

list_of_vars, verts = import_edgelist(var_files, delimiter=" ", return_vertices=True)
if not isinstance(list_of_vars, list):
    list_of_vars = [list_of_vars]

mean_connectome = np.array([array * (dsize[idx]/tot) for idx, array in enumerate(list_of_means)])
mean_connectome = np.atleast_3d(mean_connectome)
mean_connectome = np.sum(mean_connectome, axis=0)

var_connectome = np.array([array * ((dsize[idx]/tot)*(dsize[idx]/tot)) for idx, array in enumerate(list_of_vars)])
var_connectome = np.atleast_3d(var_connectome)
var_connectome = np.sum(var_connectome, axis=0)


# Plot connectomes in one figure:
tits = tuple([f"{d} (N={dsize[idx]})" for idx, d in enumerate(datasets)])
tits += (f'Weighted Mean (N={tot})', f'Weighted Variance (N={tot})')

specs=[[{'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None],
       [{'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None],
       [{'colspan': 4, 'rowspan':2}, None, None, None, {'colspan':4, 'rowspan':2}, None, None, None, None, None],
       [None, None, None, None, None, None, None, None, None, None]]

multi = tools.make_subplots(rows=4, cols=10, subplot_titles=tits, specs=specs,
                            horizontal_spacing=0.04, vertical_spacing=0.08)
locs = [(1,1), (1,3), (1,5), (1,7), (1,9),
        (2,1), (2,3), (2,5), (2,7), (2,9),
        (3,1), (3,5)]

list_of_means.append(mean_connectome)
list_of_means.append(var_connectome)

anno = []
for idx, ploty in enumerate(list_of_means):
    #ploty[0]['zmin'] = zmin
    #ploty[0]['zmax'] = zmax
    c = idx+1
    #for comp in ploty:
    if idx == 11:
        multi.append_trace(go.Heatmap(z=ploty, colorbar_x=0.82, colorbar_len=0.47, colorbar_y=0.23, colorscale="blues"), *locs[idx])
    else:
        multi.append_trace(go.Heatmap(z=ploty, coloraxis="coloraxis"), *locs[idx])
    if idx==0 or idx == 5 or idx==10:
        multi.layout['yaxis'+str(c)]['autorange'] = 'reversed'
        multi.layout['yaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['xaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['yaxis'+str(c)]['ticktext'] = ['1', '35', '70']
        multi.layout['xaxis'+str(c)]['ticktext'] = ['1', '35', '70']
        multi.layout['yaxis'+str(c)]['tickfont'] = dict(size=14, color='#28282e')
        multi.layout['xaxis'+str(c)]['tickfont'] = dict(size=14, color='#28282e')
    else:
        multi.layout['yaxis'+str(c)]['autorange'] = 'reversed'
        multi.layout['yaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['xaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['yaxis'+str(c)]['ticktext'] = ['', '', '']
        multi.layout['xaxis'+str(c)]['ticktext'] = ['', '', '']

# multi.layout.width = 1200
# multi.layout.height = 900
multi['layout'].update(title="Study Mean Connectomes")

# Set the color for the heatmaps
multi.update_layout(coloraxis = {'colorscale':'reds'})#'viridis'})

# iplot(multi)
py.plot(multi, validate=False, filename='/disctest/mean_diff_connectomes.html')









# -----------------------Functional Mean Connectome----------------------- #

localpath = '/discrim-data/functional'
datasets = ['SWU4','HNU1','NYU2','XHCUMS','UPSM1','BNU3','IPCAS7','SWU1','IPCAS1','BNU1']
dsize = [429,300,300,247,230,144,144,119,114,106]
atlas = '_mask_Desikan_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Desikan_space-MNI152NLin6_res-2x2x2.nii.gz'

#Calculate total size of scans
tot = sum(dsize)

for idx, dset in enumerate(datasets):
    # get list of all files belonging to atlas:
    connectomes = os.listdir(f"{localpath}/{dset}/{atlas}")

    if idx>0:
        for name in connectomes:
            if "mean-ptr" in name:
                mean_files.append(f"{localpath}/{dset}/{atlas}/{str(name)}")
            if "variance-ptr" in name:
                var_files.append(f"{localpath}/{dset}/{atlas}/{str(name)}")
        
    else: # itterate through list and calculate mean and variance of edgelist
        mean_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "mean-ptr" in name]
        var_files = [f"{localpath}/{dset}/{atlas}/{str(name)}" for name in connectomes if "variance-ptr" in name]
    

# Create the weighted averages for mean and variance
list_of_means, verts = import_edgelist(mean_files, delimiter=" ", return_vertices=True)
if not isinstance(list_of_means, list):
    list_of_means = [list_of_means]

list_of_vars, verts = import_edgelist(var_files, delimiter=" ", return_vertices=True)
if not isinstance(list_of_vars, list):
    list_of_vars = [list_of_vars]

mean_connectome = np.array([array * (dsize[idx]/tot) for idx, array in enumerate(list_of_means)])
mean_connectome = np.atleast_3d(mean_connectome)
mean_connectome = np.sum(mean_connectome, axis=0)

var_connectome = np.array([array * ((dsize[idx]/tot)*(dsize[idx]/tot)) for idx, array in enumerate(list_of_vars)])
var_connectome = np.atleast_3d(var_connectome)
var_connectome = np.sum(var_connectome, axis=0)


# Plot connectomes in one figure:
tits = tuple([f"{d} (N={dsize[idx]})" for idx, d in enumerate(datasets)])
tits += (f'Weighted Mean (N={tot})', f'Weighted Variance (N={tot})')

specs=[[{'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None],
       [{'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None, {'colspan': 2}, None],
       [{'colspan': 4, 'rowspan':2}, None, None, None, {'colspan':4, 'rowspan':2}, None, None, None, None, None],
       [None, None, None, None, None, None, None, None, None, None]]

multi = tools.make_subplots(rows=4, cols=10, subplot_titles=tits, specs=specs,
                            horizontal_spacing=0.04, vertical_spacing=0.08)
locs = [(1,1), (1,3), (1,5), (1,7), (1,9),
        (2,1), (2,3), (2,5), (2,7), (2,9),
        (3,1), (3,5)]

list_of_means.append(mean_connectome)
list_of_means.append(var_connectome)

anno = []
for idx, ploty in enumerate(list_of_means):
    #ploty[0]['zmin'] = zmin
    #ploty[0]['zmax'] = zmax
    c = idx+1
    #for comp in ploty:
    if idx == 11:
        multi.append_trace(go.Heatmap(z=ploty, colorbar_x=0.82, colorbar_len=0.47, colorbar_y=0.23, colorscale="blues"), *locs[idx])
    else:
        multi.append_trace(go.Heatmap(z=ploty, coloraxis="coloraxis"), *locs[idx])
    if idx==0 or idx == 5 or idx==10:
        multi.layout['yaxis'+str(c)]['autorange'] = 'reversed'
        multi.layout['yaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['xaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['yaxis'+str(c)]['ticktext'] = ['1', '35', '70']
        multi.layout['xaxis'+str(c)]['ticktext'] = ['1', '35', '70']
        multi.layout['yaxis'+str(c)]['tickfont'] = dict(size=14, color='#28282e')
        multi.layout['xaxis'+str(c)]['tickfont'] = dict(size=14, color='#28282e')
    else:
        multi.layout['yaxis'+str(c)]['autorange'] = 'reversed'
        multi.layout['yaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['xaxis'+str(c)]['tickvals'] = [0, 34, 69]
        multi.layout['yaxis'+str(c)]['ticktext'] = ['', '', '']
        multi.layout['xaxis'+str(c)]['ticktext'] = ['', '', '']

# multi.layout.width = 1200
# multi.layout.height = 900
multi['layout'].update(title="Study Mean Connectomes")

# Set the color for the heatmaps
multi.update_layout(coloraxis = {'colorscale':'reds'})#'viridis'})

# iplot(multi)
py.plot(multi, validate=False, filename='/disctest/mean_func_connectomes.html')

