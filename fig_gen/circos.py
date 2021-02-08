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

# Loop through and download files
# Record values for each edge in an ndarray

# Average ndarray rows

Connections = {}
ind_Connections={}

bucket = 'ndmg-data'
paths = ['ABIDEII-BNI_1/ABIDEII-BNI_1-m2g-dwi-04-15-20-csa-det-native/',
        #'ABIDEII-SDSU_1/ABIDEII-SDSU_1-m2g-dwi-05-03-20-csa-det-native/',
        #'ABIDEII-TCD_1/ABIDEII-TCD_1-m2g-dwi-04-15-20-csa-det-native',
        #'BNU1/BNU1-2-8-20-m2g_staging-native-csa-det',
        #'BNU3/BNU3-m2g-04-05-20_dwi_csa_det_local_native',
        #'HNU1/HNU1-2-8-20-m2g_staging-native-csa-det',
        #'IPCAS_8/m2g-bet-test',
        #'MRN_1/MRN_1-m2g-dwi-05-03-20-csa-det-native',
        #'NKIENH/NKIENH-m2g-dwi-05-03-20-csa-det-native',
        #'NKI1/NKI1-2-8-20-m2g_staging-native-csa-det',
        #'NKI24/NKI24-2-8-20-m2g_staging-native-csa-det',
        #'SWU4/SWU4-2-8-20-m2g_staging-native-csa-det',
        'XHCUMS/XHCUMS-m2g-dwi-05-03-20-csa-det-native']#,
        #'Choe-DWI/Choe-8-5-20-m2g_staging-native-csa-det']

localpath = '/'

PTR = True
PLOTLY = True
ADJMATRIX = False


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



#all_files = get_matching_s3_objects(bucket, p, suffix="csv")
client = s3_client(service="s3")


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
        
        if PTR:#EXPERIMENTAL
            m = np.asmatrix(ind_Connections, dtype=float)
            ind_Connections = np.array(pass_to_ranks(m))

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
elif PLOTLY:
    for k in Connections:
        for j in Connections[k]:
            heatmap[int(k)][int(j)] = np.average(Connections[k][j])
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

if PLOTLY:
    m = np.asmatrix(heatmap,dtype=float)
    Q=nx.from_numpy_matrix(m)
    Q.remove_node(0)

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
                                    width=floor(Weights[j]*1.9)#The  width is proportional to the edge weight
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
    title="A circular graph associated to Eurovision Song Contest, 2015<br>Data source:"+\
    "<a href='http://www.eurovision.tv/page/history/by-year/contest?event=2083#Scoreboard'> [1]</a>"
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
    py.iplot(fig, filename='Eurovision-15') 

    print('done')

else:
    m = np.asmatrix(heatmap, dtype=float)
    Q = nx.from_numpy_matrix(m)
    #nx.set_edge_attributes(Q, edge_colors, 'color')

    for k in Connections:
        for j in Connections[k]:
            try:
                if int(k)<35 and int(j)<=35:
                    Q.edges[int(k),int(j)]['color']='z'
                elif int(k)>=35 and int(j)>35:
                    Q.edges[int(k),int(j)]['color']='zop'
                elif int(k) == 70-int(j):
                    Q.edges[int(k),int(j)]['color']='zoop'
                else:
                    Q.edges[int(k),int(j)]['color']='zeep'
            except:
                print(f'No edges detected between {k} and {j}')

    nx.relabel_nodes(Q, {i: "long name #" + str(i) for i in range(70)})

    Q.remove_node(0)

    c=CircosPlot(graph=Q, node_size=3,node_labels=True, edge_color="color", edge_width='weight', node_label_layout='rotation')
    q=0
    for node_color in c.node_colors:
        if q <= 35:
            c.node_colors[q] = 'green'
            q=q+1
        else:
            c.node_colors[q] = 'red'
            q=q+1



    c.draw()
    plt.savefig('/Users/ross/Documents/con_avg/test.png')

print('oof')

