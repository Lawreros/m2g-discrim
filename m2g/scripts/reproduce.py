import numpy as np 
from graspy.utils import pass_to_ranks
from graspy.utils import import_edgelist
from hyppo.discrim import DiscrimOneSample
import networkx as nx
from scipy import stats

diff = False
func = True

dset_d = ['SWU4','HNU1','NKIENH','XHCUMS','BNU3']
atlas_d = ['AAL_space-MNI152NLin6_res-2x2x2', 'Desikan_space-MNI152NLin6_res-2x2x2', 'Hammersmith_space-MNI152NLin6_res-2x2x2',
'Talairach_space-MNI152NLin6_res-2x2x2', 'Yeo-17_space-MNI152NLin6_res-2x2x2', 'Yeo-17-liberal_space-MNI152NLin6_res-2x2x2.nii.gz',
'Yeo-7_space-MNI152NLin6_res-2x2x2.nii.gz', 'Yeo-7-liberal_space-MNI152NLin6_res-2x2x2']

if diff:
    # Load diffusion files from single directory as numpy arrays
    file_list=[]
    for i in range(1,6):
        file_list.append(f"/reproduce/{i}/sub-0025629/ses-1/connectomes/{atlas[1]}/sub-0025629_ses-1_dwi_{atlas[1]}_connectome.csv")

    list_of_arrays = import_edgelist(file_list, delimiter=" ")

    # Pass each to rank
    #graphs = np.array([pass_to_ranks(graph) for graph in list_of_arrays])

    # Convert non-ptr into 1D vector
    fixed=np.zeros((len(list_of_arrays),6671))
    for idx, i in enumerate(list_of_arrays):
        count = 0
        for j in range(0,i.shape[1]):
            for k in range(0,j):
                count += 1
                fixed[idx][count] = i[j][k]

    # Go through the spearman correlation values for each combination
    for i in range(len(fixed)):
        for j in range(0,i):
            print(stats.spearmanr(fixed[i], fixed[j])[0])


    # Convert ptr into 1D vector
    #fixed=np.zeros((len(graphs),2416))
    #for idx, i in enumerate(graphs):
    #    count = 0
    #    for j in range(0,i.shape[1]):
    #        for k in range(0,j):
    #            count += 1
    #            fixed[idx][count] = i[j][k]

    print(count)

    # Go through the spearman correlation values for each combination
    #for i in range(len(fixed)):
    #    for j in range(0,i):
    #        print(stats.spearmanr(fixed[i], fixed[j])[0])



###---------------------------Functional Reproducibility Metric-----------------------------###


dset_f = ['SWU4','BNU3','XHCUMS','UPSM_1']
atlas_f = ['_mask_AAL_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..AAL_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Desikan_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Desikan_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Hammersmith_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Hammersmith_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Talairach_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Talairach_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Yeo-17_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Yeo-17_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Yeo-17-liberal_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Yeo-17-liberal_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Yeo-7_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Yeo-7_space-MNI152NLin6_res-2x2x2.nii.gz',
'_mask_Yeo-7-liberal_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Yeo-7-liberal_space-MNI152NLin6_res-2x2x2.nii.gz']

if func:

    file_list=[]
    file_list.append(f"/reproduce/func-test/SWU4/1/functional_edgelists/_mask_Desikan_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Desikan_space-MNI152NLin6_res-2x2x2.nii.gz/sub-0025629_ses-1_scan_rest-None_measure-correlation.csv")
    file_list.append(f"/reproduce/func-test/SWU4/2/functional_edgelists/_mask_Desikan_space-MNI152NLin6_res-2x2x2_mask_file_..m2g_atlases..atlases..label..Human..Desikan_space-MNI152NLin6_res-2x2x2.nii.gz/sub-0025629_ses-1_scan_rest-None_measure-correlation.csv")


    list_of_arrays = import_edgelist(file_list, delimiter=" ")

    # Pass each to rank
    #graphs = np.array([pass_to_ranks(graph) for graph in list_of_arrays])
    #list_of_arrays = graphs

    # Convert non-ptr into 1D vector
    fixed=np.zeros((len(list_of_arrays),2416))
    for idx, i in enumerate(list_of_arrays):
        count = 0
        for j in range(0,i.shape[1]):
            for k in range(0,j):
                count += 1
                fixed[idx][count] = i[j][k]

    # Go through the spearman correlation values for each combination
    for i in range(len(fixed)):
        for j in range(0,i):
            a,b = stats.spearmanr(fixed[i], fixed[j])
            print(f"{a}\t{b}")



print('oof')