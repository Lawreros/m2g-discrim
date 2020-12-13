#!/usr/bin/env python

"""
m2g.scripts.m2g_bids
~~~~~~~~~~~~~~~~~~~~~~

The top level m2g entrypoint module.
In this module, m2g:
1. Pulls data into the input directory from s3 if we need it.
2. Parses the input directory.
3. for each subject/session pair, runs m2g_dwi_pipeline.m2g_dwi_worker (the actual pipeline)
"""


# standard library imports
import sys
import shutil
import glob
import os
from argparse import ArgumentParser
import numpy as np
from numpy import genfromtxt

# m2g imports
from m2g.scripts.discrim import discrim_runner, avgconnectome
from m2g.utils import cloud_utils
from m2g.utils import gen_utils
from m2g.utils.gen_utils import DirectorySweeper
from m2g.utils.gen_utils import check_dependencies
from m2g.utils.gen_utils import is_bids
from m2g.utils.gen_utils import as_directory
from m2g.scripts.m2g_dwi_pipeline import m2g_dwi_worker
from m2g.functional.m2g_func import m2g_func_worker


def get_atlas(atlas_dir, vox_size):
    """Given the desired location of atlases and the type of processing, ensure we have all the atlases and parcellations.

    Parameters
    ----------
    atlas_dir : str
        Path to directory containing atlases.
    vox_size : str
        t1w input image voxel dimensions, either 2mm or 1mm

    Returns
    -------
    tuple
        filepaths corresponding to the human parcellations, the atlas, and the atlas's mask. atals_brain and lv_mask is None if not fmri.

    Raises
    ------
    ValueError
        raised if dimensionality is wrong.
    NotImplementedError
        currently raised in lieu of atlas pulling capabilities.
    """
    if vox_size == "2mm":
        dims = "2x2x2"
    elif vox_size == "1mm":
        dims = "1x1x1"
    elif vox_size == "4mm":
        dims = "4x4x4"
    else:
        raise ValueError(
            "Voxel dimensions of input t1w image not currently supported by m2g."
        )

    # grab atlases if they don't exist
    if not os.path.exists(atlas_dir):
        # TODO : re-implement this pythonically with shutil and requests in python3.
        print("atlas directory not found. Cloning ...")
        clone = "https://github.com/neurodata/neuroparc.git"
        gen_utils.run(f"git lfs clone {clone} {atlas_dir}")

    atlas = os.path.join(
        atlas_dir, "atlases/reference_brains/MNI152NLin6_res-" + dims + "_T1w.nii.gz"
    )
    atlas_mask = os.path.join(
        atlas_dir,
        "atlases/mask/MNI152NLin6_res-" + dims + "_T1w_descr-brainmask.nii.gz",
    )
    parcellations = [
        i for i in glob.glob(atlas_dir + "/atlases/label/Human/*.nii.gz") if dims in i
    ]
    parcellations = [os.path.join(atlas_dir, "label/Human/", l) for l in parcellations]

    assert all(map(os.path.exists, parcellations)), "Some parcellations do not exist."
    assert all(
        map(os.path.exists, [atlas, atlas_mask])
    ), "atlas or atlas_mask, does not exist. You may not have git-lfs -- if not, install it."
    return parcellations, atlas, atlas_mask


def get_atlas_dir():
    """
    Gets the location of m2g's atlases.
    
    Returns
    -------
    str
        atlas directory location.
    """
    if os.path.isdir("/m2g_atlases"):
        return "/m2g_atlases"  # in docker

    return os.path.expanduser("~") + "/.m2g/m2g_atlases"  # local


def main():
    """Starting point of the m2g pipeline, assuming that you are using a BIDS organized dataset
    """
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
        "--push_location",
        action="store",
        help="Name of folder on s3 to push output data to, if the folder does not exist, it will be created."
        "Format the location as `s3://<bucket>/<path>`",
        default=None,
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
    push_location = result.push_location
    atlases = result.atlases

    ##---------------------------------------------------Start Discrim Calc--------------------------------------------------------------##

    # Inputs needed:

    # input_dir = location on bucket to download from
    # push_location = where to push the discrim values and resulting connectomes
    # ptr = whether to do PTR for functional
    # atlases = which atlases to analyze (if none spceified, just get them all)
    

    # grab files from s3
    creds = bool(cloud_utils.get_credentials())

    buck, remo = cloud_utils.parse_path(input_dir)
    home = os.path.expanduser("~")
    input_dir = as_directory(home + "/.m2g/input", remove=True)
    if (not creds) and push_location:
        raise AttributeError(
            """No AWS credentials found, but "--push_location" flag called. 
            Pushing will most likely fail."""
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

    #now /root/.m2g/input/mask_.... has all these edgelists:

    latlas = os.listdir(home + '/.m2g/input')

    # Calculate discrim and average and push it
    ptr = (ptr=='True')
    disc = (disc=='True')

    for at in latlas:
        os.makedirs(f"{output_dir}/{at}", exist_ok=True)
        if disc:
            discrim = discrim_runner(input_dir, at, ptr=False)
            discrim_ptr = discrim_runner(input_dir, at, ptr=True)
        
            f = open(f"{output_dir}/Discrim_values.txt","a")
            f.write(f"{at} Discriminability is : {discrim}\n")
            f.write(f"{at} PTR Discriminability is : {discrim_ptr}\n")
            f.close()

        # Create averaged/variance connectomes and save them
        avgconnectome(input_dir, output_dir, at)

        if push_location:
            print(f"Pushing to s3 at {push_location}.")
            push_buck, push_remo = cloud_utils.parse_path(push_location)
            cloud_utils.s3_push_data(
                push_buck,
                push_remo,
                output_dir,
                atlas=at,
                creds=creds,
            )
            


if __name__ == "__main__":
    main()
