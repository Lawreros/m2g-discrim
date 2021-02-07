import re
import os
from collections import OrderedDict
import m2g.scripts.m2g_cloud as cm2g
import m2g.utils.cloud_utils
from m2g.utils import gen_utils
from m2g.utils.cloud_utils import get_credentials
from m2g.utils.cloud_utils import get_matching_s3_objects
from numpy import genfromtxt
from math import factorial
import numpy as np

bucket = 'ndmg-data'
paths = ['BNU1/BNU1-11-12-20-m2g-func']
localpaths = ['/BNU1'] #SWU4, BNU3

num=paths.__len__()

subj_pattern = r"(?<=sub-)(\w*)(?=/ses)"
sesh_pattern = r"(?<=ses-)(\d*)"

for qq in range(num):
    path=paths[qq]
    localpath=localpaths[qq]

    all_subfiles = get_matching_s3_objects(bucket, path + "/sub-", suffix="roi_stats.csv")

    subjs = list(set(re.findall(subj_pattern, obj)[0] for obj in all_subfiles))

    seshs = OrderedDict()
    client = m2g.utils.cloud_utils.s3_client(service="s3")

    for subj in subjs:
        prefix = f"{path}/sub-{subj}/"
        all_seshfiles = get_matching_s3_objects(bucket, prefix, "roi_stats.csv")
        seshs = list(obj for obj in all_seshfiles)

        # Load in all the files selected above for the given subject
        for csv in seshs:
            atlas = csv.split("/")[-2]
            atlas = atlas.split("_")[2]
            subsesh = f"{csv.split('/')[-10]}_{csv.split('/')[-9]}"

            os.makedirs(f"{localpath}/{atlas}", exist_ok=True)

            client.download_file(bucket, f"{csv}", f"{localpath}/{atlas}/{subsesh}_roi_stats.csv")
            print(f"Downloaded {csv}")


print('oof')