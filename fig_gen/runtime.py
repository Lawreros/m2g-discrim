
#%%
from m2g.utils.cloud_utils import s3_client
from m2g.utils.cloud_utils import get_matching_s3_objects
import os
import re
import gzip
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


RunTimes = {}
RunTimes['func'] = {}
RunTimes['dwi'] = {}

failcount = 0

bucket = 'ndmg-results'
path = 'runlogs/4f078440-8fe0-4155-be7c-45ff34516824'
localpath = '/runtime'

all_files = get_matching_s3_objects(bucket, path, suffix="0.gz")
client = s3_client(service="s3")


qq = 0
for fi in all_files:
    client.download_file(bucket, fi, f"{localpath}/runlogs/{qq}.gz")
    print(f"Downloaded {qq}.gz")
    duration = None

    with gzip.open(f'{localpath}/runlogs/{qq}.gz', 'rt') as f:
        file_content = f.read()

        # find dataset, sub, and ses
        try:
            match = re.search(
                "Downloading\s*\w*\-*\w*\/sub\-\d*\/ses\-\d*", file_content)
            source = match.group()
            source = source.split(' ')[1]
            dataset = source.split('/')[0]
            sub = source.split('sub-')[1].split('/')[0]
            ses = source.split('ses-')[1]
            good = True
        except:
            print('FAILURE to retrieve dataset/sub/ses')
            good = False
            pass

        # dMRI
        a = file_content.find('Total execution time: ')
        if a > -1 and good:
            dtype = 'dwi'
            dur = file_content[a+21:a+33]
            if "day" in dur:
                dur = file_content[a+21:a+40]
                ddays = int(dur.split('day')[0])
                dur = dur.split(",")[1:]
                dhours = int(dur[0].split(':')[0])
                dminutes = int(dur[0].split(':')[1])
                dseconds = float(dur[0].split(':')[2])
                duration = ((((((ddays*24)+dhours)*60)+dminutes)*60)+dseconds)
            else:
                dhours = int(dur.split(':')[0])
                dminutes = int(dur.split(':')[1])
                dseconds = float(dur.split(':')[2])

                duration = ((((dhours*60)+dminutes)*60)+dseconds)

            if dataset == "SWU4":
                print(f"{fi}")

        # fMRI
        #b = file_content.find('System time of start: ')
        #if b > -1 and good:
        #    dtype = 'func'
        #    c = file_content.find('System time of completion: ')
        #
        #    if c > -1:
        #        start = file_content[b+38:b+46]
        #        end = file_content[c+38:c+46]
        #
        #        # Convert start and end into numbers
        #        shours = int(start.split(':')[0])
        #        sminutes = int(start.split(':')[1])
        #        sseconds = int(start.split(':')[2])
        #
        #        ehours = int(end.split(':')[0])
        #        eminutes = int(end.split(':')[1])
        #        eseconds = int(end.split(':')[2])
        #
        #        duration = ((((ehours*60)+eminutes)*60)+eseconds) - \
        #            ((((shours*60)+sminutes)*60)+sseconds)
        #        print('fMRI')
        #    else:
        #        print('fMRI')
        #        print("ERROR: Log denotes failure to complete")
        b = file_content.find('Elapsed run time (minutes): ')
        if b > -1 and good:
            dtype = 'func'
            start = file_content[b+24:b+43]
            start = float(start.split(":")[1])
            duration = float(start*60)

        # failure
        d = file_content.find('m2g [-h]')
        if d > -1:
            duration = None

        if duration and duration < 800:
            print('Analysis less than 15 minutes')
            duration = None

        if not duration:
            print('FAILURE to calculate Duration')
            failcount = failcount+1

        # Store values in giant array
        if dataset not in RunTimes[dtype].keys():
            if duration and good:
                RunTimes[dtype][dataset] = np.zeros(0)
                RunTimes[dtype][dataset] = np.append(
                    RunTimes[dtype][dataset], [duration])
        else:
            if duration and good:
                RunTimes[dtype][dataset] = np.append(
                    RunTimes[dtype][dataset], [duration])

    f.close()
    os.remove(f'{localpath}/runlogs/{qq}.gz')
    qq = qq+1


#%% Plot Functional

sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

# Create the data
#rs = np.random.RandomState(1979)
#x = rs.randn(500)
#g = np.tile(list("ABCDEFGHIJ"), 50)
#df = pd.DataFrame(dict(x=x, g=g))
#m = df.g.map(ord)
#df["x"] += m

for idx, i in enumerate(RunTimes['func']):
    if idx == 0:
        df = pd.DataFrame(dict(x=list(RunTimes['func'][i]),g=i))
    else:
        dff = pd.DataFrame(dict(x=list(RunTimes['func'][i]),g=i))
        df = pd.concat((df,dff)).reset_index(drop=True)

#df1 = pd.DataFrame(dict(x=list(RunTimes['func']['SWU4']/60),g="SWU4"))
#df2 = pd.DataFrame(dict(x=list(RunTimes['func']['HNU1']/60),g="HNU1"))
#df3 = pd.DataFrame(dict(x=list(RunTimes['func']['NYU_2']/60),g="NYU2"))
#df4 = pd.DataFrame(dict(x=list(RunTimes['func']['XHCUMS']/60),g="XHCUMS"))
#df5 = pd.DataFrame(dict(x=list(RunTimes['func']['UPSM_1']/60),g="UPSM1"))
#df6 = pd.DataFrame(dict(x=list(RunTimes['func']['BNU3']/60),g="BNU3"))
#df7 = pd.DataFrame(dict(x=list(RunTimes['func']['IPCAS7']/60),g="IPCAS7"))
#df8 = pd.DataFrame(dict(x=list(RunTimes['func']['SWU1']/60),g="SWU1"))
#df9 = pd.DataFrame(dict(x=list(RunTimes['func']['IPCAS1']/60),g="IPCAS1"))
#df10 = pd.DataFrame(dict(x=list(RunTimes['func']['BNU1']/60),g="BNU1"))
#df = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10)).reset_index(drop=True)

# Initialize the FacetGrid object
pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
g = sns.FacetGrid(df, row="g", hue="g", aspect=15, height=.5, palette=pal)

# Draw the densities in a few steps
g.map(sns.kdeplot, "x",
      bw_adjust=.5, clip_on=False,
      fill=True, alpha=1, linewidth=1.5)
g.map(sns.kdeplot, "x", clip_on=False, color="w", lw=2, bw_adjust=.5)
g.map(plt.axhline, y=0, lw=2, clip_on=False)


# Define and use a simple function to label the plot in axes coordinates
def label(x, color, label):
    ax = plt.gca()
    ax.text(0, .2, label, fontweight="bold", color=color,
            ha="left", va="center", transform=ax.transAxes)


g.map(label, "Runtime")

# Set the subplots to overlap
g.fig.subplots_adjust(hspace=-.25)

# Remove axes details that don't play well with overlap
g.set_titles("")
g.set(yticks=[])
#g.set(xlim=(20,65))
g.despine(bottom=True, left=True)
plt.savefig("/func_runtime.png", dpi=300)

# %% Plot Diffusion

sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

# Create the data
#rs = np.random.RandomState(1979)
#x = rs.randn(500)
#g = np.tile(list("ABCDEFGHIJ"), 50)
#df = pd.DataFrame(dict(x=x, g=g))
#m = df.g.map(ord)
#df["x"] += m

for idx, i in enumerate(RunTimes['dwi']):
    if idx == 0:
        df = pd.DataFrame(dict(x=list(RunTimes['dwi'][i]),g=i))
    else:
        dff = pd.DataFrame(dict(x=list(RunTimes['dwi'][i]),g=i))
        df = pd.concat((df,dff)).reset_index(drop=True)


#df1 = pd.DataFrame(dict(x=list(RunTimes['dwi']['SWU4']/60),g="SWU4"))
#df2 = pd.DataFrame(dict(x=list(RunTimes['dwi']['HNU1']/60),g="HNU1"))
#df3 = pd.DataFrame(dict(x=list(RunTimes['dwi']['XHCUMS']/60),g="XHCUMS"))
#df4 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU1']/60),g="BNU1"))
#df5 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI1']/60),g="NKI1"))
#df6 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI24']/60),g="NKI24"))
#df7 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/60),g="IPCAS8"))
#df8 = pd.DataFrame(dict(x=list(RunTimes['dwi']['MRN_1']/60),g="MRN1"))
#df = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8)).reset_index(drop=True)

# Initialize the FacetGrid object
pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
g = sns.FacetGrid(df, row="g", hue="g", aspect=15, height=.5, palette=pal)

# Draw the densities in a few steps
g.map(sns.kdeplot, "x",
      bw_adjust=.5, clip_on=False,
      fill=True, alpha=1, linewidth=1.5)
g.map(sns.kdeplot, "x", clip_on=False, color="w", lw=2, bw_adjust=.5)
g.map(plt.axhline, y=0, lw=2, clip_on=False)


# Define and use a simple function to label the plot in axes coordinates
def label(x, color, label):
    ax = plt.gca()
    ax.text(0, .2, label, fontweight="bold", color=color,
            ha="left", va="center", transform=ax.transAxes)


g.map(label, "x")

# Set the subplots to overlap
g.fig.subplots_adjust(hspace=-.25)

# Remove axes details that don't play well with overlap
g.set_titles("")
g.set(yticks=[])
g.despine(bottom=True, left=True)
plt.savefig("/runtime.png", dpi=300)