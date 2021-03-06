# Copyright 2014 Open Connectome Project (http://openconnecto.me)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# qa_graphs.py
# Created by Greg Kiar on 2016-05-11.
# Email: gkiar@jhu.edu

from argparse import ArgumentParser
from collections import OrderedDict
from subprocess import Popen
from scipy.stats import gaussian_kde
from m2g.utils import cloud_utils

import numpy as np
import nibabel as nb
import networkx as nx
import pickle
import sys
import os


def loadGraphs(filenames, modality="dwi", verb=False):
    """
    Given a list of files, returns a dictionary of graphs
    Required parameters:
        filenames:
            - List of filenames for graphs
    Optional parameters:
        verb:
            - Toggles verbose output statements
    """
    #  Initializes empty dictionary
    if type(filenames) is not list:
        filenames = [filenames]
    gstruct = OrderedDict()
    vlist = set()
    for idx, files in enumerate(filenames):
        if verb:
            print("Loading: " + files)
        #  Adds graphs to dictionary with key being filename
        fname = os.path.basename(files)
        try:
            gstruct[fname] = loadGraph(files, modality=modality)
            vlist |= set(gstruct[fname].nodes())
        except:
            print("{} is not in proper format. Skipping...".format(fname))
    for k, v in list(gstruct.items()):
        vtx_to_add = list(np.setdiff1d(list(vlist), list(v.nodes())))
        [gstruct[k].add_node(vtx) for vtx in vtx_to_add]
    return gstruct


def loadGraph(filename, modality="dwi", verb=False):
    if modality == "dwi":
        graph = nx.read_weighted_edgelist(filename, delimiter=" ")
    elif modality == "func":
        # read first line to int list
        with open(filename, "r") as fl:
            reader = csv.reader(fl)
            # labels
            labs = [int(x) for x in next(reader)]
        # read second line onwards to numpy array
        data = np.genfromtxt(filename, dtype=float, delimiter=",", skip_header=True)
        lab_map = dict(list(zip(list(range(0, len(labs))), labs)))
        graph = nx.from_numpy_matrix(data)
        graph = nx.relabel_nodes(graph, lab_map)
    else:
        raise ValueError("Unsupported modality.")
    return graph

def compute_metrics(fs, outdir, atlas, verb=False):
    """
    Given a set of files and a directory to put things, loads graphs and
    performs set of analyses on them, storing derivatives in a pickle format
    in the desired output location.
    Required parameters:
        fs:
            - Dictionary of lists of files in each dataset
        outdir:
            - Path to derivative save location
        atlas:
            - Name of atlas of interest as it appears in the directory titles
    Optional parameters:
        verb:
            - Toggles verbose output statements
    """

    graphs = loadGraphs(fs, verb=verb)
    #nodes = nx.number_of_nodes(graphs.values()[0])

    #  Degree sequence
    print("Computing: Degree Sequence")
    #total_deg = OrderedDict((subj, np.array(nx.degree(graphs[subj]).values()))
    #                        for subj in graphs)
    ipso_deg = OrderedDict()
    contra_deg = OrderedDict()
    for subj in graphs:  # TODO GK: remove forloop and use comprehension maybe?
        g = graphs[subj]
        N = len(g.nodes())
        LLnodes = g.nodes()[0:N/2]  # TODO GK: don't assume hemispheres
        LL = g.subgraph(LLnodes)
        LLdegs = [LL.degree()[n] for n in LLnodes]

        RRnodes = g.nodes()[N/2:N]  # TODO GK: don't assume hemispheres
        RR = g.subgraph(RRnodes)
        RRdegs = [RR.degree()[n] for n in RRnodes]

        LRnodes = g.nodes()
        ipso_list = LLdegs + RRdegs
        degs = [g.degree()[n] for n in LRnodes]
        contra_deg[subj] = [a_i - b_i for a_i, b_i in zip(degs, ipso_list)]
        ipso_deg[subj] = ipso_list
        # import pdb; pdb.set_trace()

    deg = {'total_deg': total_deg,
           'ipso_deg': ipso_deg,
           'contra_deg': contra_deg}
    write(outdir, 'degree_distribution', deg, atlas)
    show_means(total_deg)

    #  Edge Weights
    print("Computing: Edge Weight Sequence")
    temp_ew = OrderedDict((s, [graphs[s].get_edge_data(e[0], e[1])['weight']
                           for e in graphs[s].edges()]) for s in graphs)
    ew = temp_ew
    write(outdir, 'edge_weight', ew, atlas)
    show_means(temp_ew)

    #   Clustering Coefficients
    print("Computing: Clustering Coefficient Sequence")
    temp_cc = OrderedDict((subj, nx.clustering(graphs[subj]).values())
                          for subj in graphs)
    ccoefs = temp_cc
    write(outdir, 'clustering_coefficients', ccoefs, atlas)
    show_means(temp_cc)

    # Scan Statistic-1
    print("Computing: Max Local Statistic Sequence")
    temp_ss1 = scan_statistic(graphs, 1)
    ss1 = temp_ss1
    write(outdir, 'locality_statistic', ss1, atlas)
    show_means(temp_ss1)

    # Eigen Values
    print("Computing: Eigen Value Sequence")
    laplac = OrderedDict((subj, nx.normalized_laplacian_matrix(graphs[subj]))
                         for subj in graphs)
    eigs = OrderedDict((subj, np.sort(np.linalg.eigvals(laplac[subj].A))[::-1])
                       for subj in graphs)
    write(outdir, 'eigen_sequence', eigs, atlas)
    print("Subject Maxes: " + ", ".join(["%.2f" % np.max(eigs[key])
                                         for key in eigs.keys()]))

    # Betweenness Centrality
    print("Computing: Betweenness Centrality Sequence")
    nxbc = nx.algorithms.betweenness_centrality  # For PEP8 line length...
    temp_bc = OrderedDict((subj, nxbc(graphs[subj]).values())
                          for subj in graphs)
    centrality = temp_bc
    write(outdir, 'betweenness_centrality', centrality, atlas)
    show_means(temp_bc)

    # Mean connectome
    print("Computing: Mean Connectome")
    adj = OrderedDict((subj, nx.adj_matrix(graphs[subj]).todense())
                      for subj in graphs)
    mat = np.zeros(adj.values()[0].shape)
    for subj in adj:
        mat += adj[subj]
    mat = mat/len(adj.keys())
    write(outdir, 'study_mean_connectome', mat, atlas)


def show_means(data):
    print("Subject Means: " + ", ".join(["%.2f" % np.mean(data[key])
                                         for key in data.keys()]))


def scan_statistic(mygs, i):
    """
    Computes scan statistic-i on a set of graphs
    Required Parameters:
        mygs:
            - Dictionary of graphs
        i:
            - which scan statistic to compute
    """
    ss = OrderedDict()
    for key in mygs.keys():
        g = mygs[key]
        tmp = np.array(())
        for n in g.nodes():
            sg = nx.ego_graph(g, n, radius=i)
            tmp = np.append(tmp, np.sum([sg.get_edge_data(e[0], e[1])['weight']
                            for e in sg.edges()]))
        ss[key] = tmp
    return ss


def density(data, nbins=500, rng=None):
    """
    Computes density for metrics which return vectors
    Required parameters:
        data:
            - Dictionary of the vectors of data
    """
    density = OrderedDict()
    xs = OrderedDict()
    for subj in data:
        hist = np.histogram(data[subj], nbins)
        hist = np.max(hist[0])
        dens = gaussian_kde(data[subj])
        if rng is not None:
            xs[subj] = np.linspace(rng[0], rng[1], nbins)
        else:
            xs[subj] = np.linspace(0, np.max(data[subj]), nbins)
        density[subj] = dens.evaluate(xs[subj])*np.max(data[subj]*hist)
    return {"xs": xs, "pdfs": density}


def write(outdir, metric, data, atlas):
    """
    Write computed derivative to disk in a pickle file
    Required parameters:
        outdir:
            - Path to derivative save location
        metric:
            - The value that was calculated
        data:
            - The results of this calculation
        atlas:
            - Name of atlas of interest as it appears in the directory titles
    """
    with open(outdir + '/' + atlas + '_' + metric + '.pkl', 'wb') as of:
        pickle.dump({metric: data}, of)


def main():
    """
    Argument parser and directory crawler. Takes organization and atlas
    information and produces a dictionary of file lists based on datasets
    of interest and then passes it off for processing.
    Required parameters:
        atlas:
            - Name of atlas of interest as it appears in the directory titles
        basepath:
            - Basepath for which data can be found directly inwards from
        outdir:
            - Path to derivative save location
    Optional parameters:
        fmt:
            - Determines file organization; whether graphs are stored as
              .../atlas/dataset/graphs or .../dataset/atlas/graphs. If the
              latter, use the flag.
        verb:
            - Toggles verbose output statements
    """

    parser = ArgumentParser(description="Computes Graph Metrics")
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
        "atlases",
        action="store",
        help="which atlases to use",
        nargs="+",
        default=None,
    )

    parser.add_argument("-v", "--verb", action="store_true", help="")
    result = parser.parse_args()

    #  Sets up directory to crawl based on the system organization you're
    #  working on. Which organizations are pretty clear by the code, methinks..
    indir = result.input_dir
    outdir = result.output_dir
    atlas = result.atlases
    pipe = result.pipeline



    if "s3://" in indir:
        # grab files from s3
        creds = bool(cloud_utils.get_credentials())

        buck, remo = cloud_utils.parse_path(input_dir)
        home = os.path.expanduser("~")
        input_dir = as_directory(home + "/.m2g/input", remove=True)

        if (not creds) and push_location:
            raise AttributeError(
                """No AWS credentials found."""
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
    

    #fs = dict()
    #for root, dirs, files in os.walkdir(f"{indir}/{dset}"):
    #    if 

    #fs = [indir + "/" + for root, dirs, files in os.walk(indir)
    #    for fl in files
    #    if fl.endeswith(".csv")]

    fs = ['/disctest/BNU1/Desikan/sub-0025864_ses-1_connectome.csv','/disctest/BNU1/Desikan/sub-0025864_ses-2_connectome.csv']

    os.makedirs(outdir, exist_ok=True)
    #  The fun begins and now we load our graphs and process them.
    compute_metrics(fs, outdir, atlas)


if __name__ == "__main__":
    main()