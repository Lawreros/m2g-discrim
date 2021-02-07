import numpy as np
from graspologic.datasets import load_drosophila_right
from graspologic.plot import heatmap
from graspologic.utils import binarize, symmetrize
import matplotlib.pyplot as plt

adj, labels = load_drosophila_right(return_labels=True)
adj = binarize(adj)


from graspologic.models import SBMEstimator
from graspy.utils import import_edgelist
import networkx as nx

mean_files = '/disctest/sub-0025864_ses-1_connectome.csv'

list_of_means, verts = import_edgelist(mean_files, delimiter=" ", return_vertices=True)
#list_of_means = nx.read_edgelist(mean_files, nodetype = int, data=(('weight',float),))
list_of_means = binarize(list_of_means)
verts = np.empty(70, dtype=object)
for idx, i in enumerate(verts):
    if idx < 35:
        verts[idx]='L'
    else:
        verts[idx]='R'



sbme = SBMEstimator(directed=False,loops=False)
#sbme.fit(adj, y=labels)

#list_of_means = nx.from_numpy_array(list_of_means)
sbme.fit(list_of_means, y=verts)

print("SBM \"B\" matrix:")

print(sbme.block_p_)
_ = heatmap(sbme.p_mat_,
        inner_hier_labels=labels,
        vmin=0,
        vmax=1,
        font_scale=1.5,
        title="SBM probability matrix",
        sort_nodes=True)

plt.savefig("sbm_prob_matrix.png", dpi=400)
_ = heatmap(sbme.sample()[0],
        inner_hier_labels=labels,
        font_scale=1.5,
        title="SBM sample",
        sort_nodes=True)
plt.savefig("svm_sample.png", dpi=400)


# Now do the same with the averaged adjacency matricies

# Set up labels
