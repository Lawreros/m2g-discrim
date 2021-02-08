import numpy as np
import os, ssl
import boto3
import csv
import networkx as nx
from nxviz import CircosPlot
from matplotlib import pyplot as plt
from m2g.utils.cloud_utils import get_matching_s3_objects
from m2g.utils.cloud_utils import s3_client
from graspy.utils import pass_to_ranks, import_edgelist

from math import floor
import igraph as ig
import plotly
import plotly.offline as py
from plotly.graph_objs import *

def dist (A,B):
    return np.linalg.norm(np.array(A)-np.array(B))

def get_idx_interv(d,D):
    k=0
    while(d>D[k]):
        k+=1
    return k-1

class InvalidInputError(Exception):
    pass

def deCasteljau(b,t): 
    N=len(b) 
    if(N<2):
        raise InvalidInputError("The  control polygon must have at least two points")
    a=np.copy(b) #shallow copy of the list of control points 
    for r in range(1,N): 
        a[:N-r,:]=(1-t)*a[:N-r,:]+t*a[1:N-r+1,:]
    return a[0,:]

def BezierCv(b, nr=5):
    t=np.linspace(0, 1, nr)
    return np.array([deCasteljau(b, t[k]) for k in range(nr)]) 



def main():
    parser = ArgumentParser(
        description="This is an end-to-end connectome estimation pipeline from M3r Images."
    )
    parser.add_argument(
        "input_dir",
        help="""The directory with the input dataset
        formatted according to the BIDS standard.
        To use data from s3, just pass `s3://<bucket>/<dataset>` as the input directory.""",
    )
    parser.add_argument(
        "output_dir",
        help="""The local directory where the output
        files should be stored.""",
    )
    parser.add_argument(
        "pipeline",
        help="""Pipeline that created the data""",
    )
    parser.add_argument(
        "--ptr",
        action="store",
        help="whether to pass to ranks",
        default=True
    )
    parser.add_argument(
        "--discrim",
        action="store",
        help="Whether or not to calculate discriminability",
        default=True
    )
    parser.add_argument(
        "--atlases",
        action="store",
        help="which atlases to use",
        nargs="+",
        default=None,
    )
    result = parser.parse_args()
    input_dir = result.input_dir
    output_dir = result.output_dir
    pipe = result.pipeline
    ptr = result.ptr
    disc = result.discrim
    atlases = result.atlases

    
    # Inputs needed:

    Connections = {}
    ind_Connections={}
    PTR = True
    PLOTLY = False
    ADJMATRIX = True

    # grab files from s3
    creds = bool(cloud_utils.get_credentials())

    buck, remo = cloud_utils.parse_path(input_dir)
    home = os.path.expanduser("~")
    input_dir = as_directory(home + "/.m2g/input", remove=True)
    if not creds:
        raise AttributeError(
            """No AWS credentials found"""
        )

    # Get S3 input data if needed
    if pipe =='func':
        if atlases is not None:
            for atlas in atlases:
                info = f"_mask_{atlas}"
                cloud_utils.s3_get_data(buck, remo, input_dir, info=info, pipe=pipe)
        else:
            info = "_mask_"
            cloud_utils.s3_get_data(buck, remo, input_dir, info=info, pipe=pipe)
    elif pipe=='dwi':
        if atlases is not None:
            for atlas in atlases:
                info = f"{atlas}"
                cloud_utils.s3_get_data(buck, remo, input_dir, info=info, pipe=pipe)
        else:
            info = ""
            cloud_utils.s3_get_data(buck, remo, input_dir, info=info, pipe=pipe)

    localpath = '/discrim-data/diffusion'
    datasets = ['SWU4','HNU1','NKIENH','XHCUMS','BNU1','BNU3','IPCAS8','NKI1','NKI24','MRN1']
    dsize = [382,298,192,120,114,46,40,36,36,20]

    atlas = 'Desikan_space-MNI152NLin6_res-2x2x2'
    #atlas = 'Hammersmith_space-MNI152NLin6_res-2x2x2/'
    #atlas = 'AAL_space-MNI152NLin6_res-2x2x2/'


    #localpath = '/discrim-data/functional'
    #datasets = ['SWU4','HNU1','NYU2','XHCUMS','UPSM1','BNU3','IPCAS7','SWU1','IPCAS1','BNU1']
    #dsize = [429,300,300,247,230,144,144,119,114,106]
    #atlas = '_mask_Desikan_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Desikan_space-MNI152NLin6_res-2x2x2.nii.gz'
    #atlas='_mask_Hammersmith_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Hammersmith_space-MNI152NLin6_res-2x2x2.nii.gz/'
    #atlas='_mask_AAL_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..AAL_space-MNI152NLin6_res-2x2x2.nii.gz/'

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

    mean_connectome = np.array([array * (dsize[idx]/tot) for idx, array in enumerate(list_of_means)])
    mean_connectome = np.atleast_3d(mean_connectome)
    mean_connectome = np.sum(mean_connectome, axis=0)

    #mean_connectome = np.array([array for idx, array in enumerate(list_of_means)])
    #meany = np.atleast_3d(mean_connectome)

    #for mean_connectome in meany:

    if 'Desikan' in atlas:
        ipsi=[]
        contra=[]
        hom=[]

        r,c = mean_connectome.shape
        for j in range(r):
            for i in range(c):
                if i>j:
                    if j+35==i:
                        hom.append(mean_connectome[j][i])
                    elif i<35 and j<35:
                        ipsi.append(mean_connectome[j][i])
                    elif i>=35 and j>=35:
                        ipsi.append(mean_connectome[j][i])
                    else:
                        contra.append(mean_connectome[j][i])
        hom=np.array(hom)
        ipsi=np.array(ipsi)
        contra=np.array(contra)

    if 'Hammer' in atlas:
        ipsi=[]
        contra=[]
        hom=[]

        r,c = mean_connectome.shape
        for j in range(r):
            for i in range(c):
                if i not in {43,48} and j not in {43,48}:
                    if i>j:
                        if (i==j+1) and (j % 2==1):
                            hom.append(mean_connectome[j][i])
                        elif i % 2 == j % 2:
                            ipsi.append(mean_connectome[j][i])
                        else:
                            contra.append(mean_connectome[j][i])
        hom=np.array(hom)
        ipsi=np.array(ipsi)
        contra=np.array(contra)

    if 'AAL' in atlas:
        ipsi=[]
        contra=[]
        hom=[]

        r,c = mean_connectome.shape
        for j in range(r):
            for i in range(c):
                if i>j:
                    if (i==j+1) and (j % 2==1):
                        hom.append(mean_connectome[j][i])
                    elif i % 2 == j % 2:
                        ipsi.append(mean_connectome[j][i])
                    else:
                        contra.append(mean_connectome[j][i])
        hom=np.array(hom)
        ipsi=np.array(ipsi)
        contra=np.array(contra)

    tot = np.sum(ipsi)+np.sum(hom)+np.sum(contra)
    print(f'Ipsi = {np.mean(ipsi)} ({np.std(ipsi)})')
    print(f'Homotopic = {np.mean(hom)} ({np.std(hom)})')
    print(f'Contralateral = {np.mean(contra)} ({np.std(contra)})')



    #Calculate average connections and make it into a matrix

    #heatmap = np.zeros((71,71))
    #edgeweights = list()
    edge_colors = {}


    if PLOTLY:
        m = np.asmatrix(mean_connectome, dtype=float)#heatmap,dtype=float)
        Q=nx.from_numpy_matrix(m)
        #Q.remove_node(0)

        nx.write_gml(Q,'avg_edges.gml')

        G=ig.Graph.Read_GML('avg_edges.gml')

        V=list(G.vs)

        labels=[v['label'] for v in V]

        G.es.attributes()# the edge attributes

        E=[e.tuple for e in G.es] #list of edges

        # Get the list of Contestant countries
        ContestantLst=[G.vs[e[1]] for e in E]
        Contestant=list(set([v['label'] for  v in ContestantLst]))

        # Get the node positions, assigned by the circular layout
        layt=G.layout('circular')

        dumb = layt.copy()

        for i in range(35,len(layt)):
            layt[i]=[2,2] #some weird bug where it only lets you replace a few values
            layt[i]=dumb[104-i]
        
        # layt is a list of 2-elements lists, representing the coordinates of nodes placed on the unit circle
        L=len(layt)

        # Define the list of edge weights
        Weights= list(map(float, G.es["weight"]))

        Dist=[0, dist([1,0], 2*[np.sqrt(2)/2]), np.sqrt(2),
            dist([1,0],  [-np.sqrt(2)/2, np.sqrt(2)/2]), 2.0]
        params=[1.2, 1.5, 1.8, 2.1]


        node_color=['rgba(0,51,181, 0.85)'  if int(v['label']) <= 35 else '#ff0000' for v in G.vs]#if v['label'] in Contestant else '#CCCCCC' for v in G.vs] 
        line_color=['#FFFFFF'  if v['label'] in Contestant else 'rgb(150,150,150)' for v in G.vs]
        edge_colors=['#000000','#e41a1c','#377eb8','#33a02c']#['#d4daff','#84a9dd', '#5588c8', '#6d8acf']


        Xn=[layt[k][0] for k in range(L)]
        Yn=[layt[k][1] for k in range(L)]

        lines=[]# the list of dicts defining   edge  Plotly attributes
        edge_info=[]# the list of points on edges where  the information is placed

        for j, e in enumerate(E):
            A=np.array(layt[e[0]])
            B=np.array(layt[e[1]])
            d=dist(A, B)
            K=get_idx_interv(d, Dist)
            b=[A, A/params[K], B/params[K], B]

            if (e[0]<35 and e[1] >=35) or (e[0]>=35 and e[1]<35):
                if abs(e[0]-e[1]) == 35:
                    color = '#000000' #black
                else:
                    color = '#33a02c' #green
            elif e[0]<=35 and e[1]<=35:
                color = '#377eb8' #blue
            else:
                color = '#e41a1c' #red
            #color=edge_colors[K]
            pts=BezierCv(b, nr=5)
            #text=V[e[0]]['label']+' to '+V[e[1]]['label']+' '+str(Weights[j])+' pts'
            mark=deCasteljau(b,0.9)
            x_point=[mark[0]]
            y_point=[mark[1]]
            edge_info.append(plotly.graph_objs.Scatter(x=x_point,#mark[0],
                                    y=y_point,#mark[1],
                                    mode='markers',
                                    marker=Marker(size=0.5, color=color),#edge_colors),
                                    )
                            )
            #edge_info.append(Scatter(x=mark[0], 
            #                         y=mark[1], 
            #                         mode='markers', 
            #                         marker=Marker( size=0.5,  color=edge_colors),
            #                         text=text, 
            #                         hoverinfo='text'
            #                         )
            #                )
            lines.append(Scatter(x=pts[:,0],
                                y=pts[:,1],
                                mode='lines',
                                line=Line(color=color, 
                                        shape='spline',
                                        width=floor(Weights[j]*1.1)#The  width is proportional to the edge weight
                                        ), 
                                hoverinfo='none' 
                            )
                        )
            
        trace2=Scatter(x=Xn,
                y=Yn,
                mode='markers',
                name='',
                marker=Marker(symbol='circle-dot',
                                size=15, 
                                color=node_color, 
                                line=Line(color=line_color, width=0.5)
                                ),
                text=labels,
                hoverinfo='text',
                )

        axis=dict(showline=False, # hide axis line, grid, ticklabels and  title
                zeroline=False,
                showgrid=False,
                showticklabels=False,
                title='' 
                )


        width=800
        height=850
        title="Circos plot"
        layout=Layout(title= title,
                    font= Font(size=12),
                    showlegend=False,
                    autosize=False,
                    width=width,
                    height=height,
                    xaxis=XAxis(axis),
                    yaxis=YAxis(axis),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',   
                    margin=Margin(l=40,
                                    r=40,
                                    b=85,
                                    t=100,
                                ),
                    hovermode='closest'
                    )

        data=Data(lines+edge_info+[trace2])
        fig=Figure(data=data, layout=layout)
        # iplot(multi)
        py.plot(fig, validate=False, filename='/disctest/circos_diff.html')
        #py.iplot(fig, filename='Eurovision-15')

        print('done')
