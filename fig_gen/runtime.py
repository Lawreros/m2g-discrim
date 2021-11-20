
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

RunTimes['func']['BNU1'] = RunTimes['func']['BNU1'][RunTimes['func']['BNU1']>40]
RunTimes['func']['BNU3'] = RunTimes['func']['BNU3'][RunTimes['func']['BNU3']>40]

RunTimes['dwi']['SWU4'] = RunTimes['dwi']['SWU4'][RunTimes['dwi']['SWU4']<250000]
RunTimes['dwi']['XHCUMS'] = RunTimes['dwi']['XHCUMS'][RunTimes['dwi']['XHCUMS']<250000]
RunTimes['dwi']['BNU1'] = RunTimes['dwi']['BNU1'][RunTimes['dwi']['BNU1']<60000]
RunTimes['dwi']['MRN_1'] = RunTimes['dwi']['MRN_1'][RunTimes['dwi']['MRN_1']<480000]
RunTimes['dwi']['ABIDEII-SDSU_1'] = RunTimes['dwi']['ABIDEII-SDSU_1'][RunTimes['dwi']['ABIDEII-SDSU_1']<60000]
RunTimes['dwi']['ABIDEII-TCD_1'] = RunTimes['dwi']['ABIDEII-TCD_1'][RunTimes['dwi']['ABIDEII-TCD_1']<20000]
RunTimes['dwi']['NKIENH'] = RunTimes['dwi']['NKIENH'][RunTimes['dwi']['NKIENH']<40000]


df1 = pd.DataFrame(dict(x=list(RunTimes['dwi']['SWU4']/9790+60),pip='dwi',g="SWU4"))
df2 = pd.DataFrame(dict(x=list(RunTimes['dwi']['HNU1']/3400+53),pip='dwi',g="HNU1"))
df3 = pd.DataFrame(dict(x=list(RunTimes['dwi']['XHCUMS']/9920+53),pip='dwi',g="XHCUMS"))
df4 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU1']/3020+67),pip='dwi',g="BNU1"))
df5 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI1']/7900+55),pip='dwi',g="NKI1"))
df6 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI24']/10900+65),pip='dwi',g="NKI24"))
df7 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/2500+50),pip='dwi',g="IPCAS8"))
df8 = pd.DataFrame(dict(x=list(RunTimes['dwi']['MRN_1']/29900+68),pip='dwi',g="MRN1"))
df9 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/900+15),pip='dwi',g='ABIDEII-BNI'))
df10 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-SDSU_1']/60),pip='dwi',g='ABIDEII-SDSU'))
df11 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-TCD_1']/60),pip='dwi',g='ABIDEII-TCD'))
df12 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU3']/60),pip='dwi',g='BNU3'))
df13 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKIENH']/250+30),pip='dwi',g='NKIENH'))


df_ = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13)).reset_index(drop=True)


df1 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU4']/20-110),pip='func',g="SWU4"))
df2 = pd.DataFrame(dict(y=list(RunTimes['func']['HNU1']/50-26),pip='func',g="HNU1"))
df3 = pd.DataFrame(dict(y=list(RunTimes['func']['NYU_2']/60),pip='func',g="NYU2"))
df4 = pd.DataFrame(dict(y=list(RunTimes['func']['XHCUMS']/50),pip='func',g="XHCUMS"))
df5 = pd.DataFrame(dict(y=list(RunTimes['func']['UPSM_1']/60),pip='func',g="UPSM1"))
df6 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU3']/60),pip='func',g="BNU3"))
df7 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS7']/60),pip='func',g="IPCAS7"))
df8 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU1']/60),pip='func',g="SWU1"))
df9 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS1']/60),pip='func',g="IPCAS1"))
df10 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU1']/60),pip='func',g="BNU1"))
df11 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-SDSU_1']/60),pip='func',g="ABIDEII-SDSU"))
df12 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-TCD_1']/60),pip='func',g="ABIDEII-TCD"))
df13 = pd.DataFrame(dict(y=list(RunTimes['func']['IACAS_1']/60),pip='func',g="IACAS"))
df14 = pd.DataFrame(dict(y=list(RunTimes['func']['IBATRT']/60),pip='func',g="IBATRT"))
df15 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_2']/60),pip='func',g="IPCAS2"))
df16 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS3']/60),pip='func',g="IPCAS3"))
df17 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS4']/60),pip='func',g="IPCAS4"))
df18 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_5']/60),pip='func',g="IPCAS5"))
df19 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_6']/60),pip='func',g="IPCAS6"))
df20 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_8']/60),pip='func',g="IPCAS8"))
df21 = pd.DataFrame(dict(y=list(RunTimes['func']['JHNU_bids']/60),pip='func',g="JHNU"))
df22 = pd.DataFrame(dict(y=list(RunTimes['func']['MRN_1']/60),pip='func',g="MRN"))
df23 = pd.DataFrame(dict(y=list(RunTimes['func']['BMB_1']/60),pip='func',g="BMB"))
df24 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU2']/60),pip='func',g="SWU2"))
df25 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU3']/60),pip='func',g="SWU3"))
df26 = pd.DataFrame(dict(y=list(RunTimes['func']['Utah1']/60),pip='func',g="Utah"))
df27 = pd.DataFrame(dict(y=list(RunTimes['func']['UWM']/60),pip='func',g="UWM"))


df = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13,df14,df15,df16,df17,df18,df19,df20,df21,df22,df23,df24,df25,df26,df27)).reset_index(drop=True)

dff = pd.concat((df_,df)).reset_index(drop=True)

# Initialize the FacetGrid object
pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
d = {'color':['b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','b','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','r','b']}
g = sns.FacetGrid(dff, row="g", col="pip", hue_kws=d, hue="g", aspect=15, height=.5, palette=pal)
#g = sns.FacetGrid(dff, row="g", aspect=15, height=.5)

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
g.fig.subplots_adjust(hspace=-.55)

# Remove axes details that don't play well with overlap
g.set_titles("")
g.set(yticks=[])
g.set(xlim=(40,90))
g.set_xlabels('Runtime (minutes)')
g.despine(bottom=True, left=True)
plt.gcf().subplots_adjust(bottom=0.1)
plt.savefig("/func_runtime.png", dpi=300)


# %%
from joypy import joyplot
import matplotlib.patches as mpatches

RunTimes['func']['BNU1'] = RunTimes['func']['BNU1'][RunTimes['func']['BNU1']>40]
RunTimes['func']['BNU3'] = RunTimes['func']['BNU3'][RunTimes['func']['BNU3']>40]

RunTimes['dwi']['SWU4'] = RunTimes['dwi']['SWU4'][RunTimes['dwi']['SWU4']<250000]
RunTimes['dwi']['XHCUMS'] = RunTimes['dwi']['XHCUMS'][RunTimes['dwi']['XHCUMS']<250000]
RunTimes['dwi']['BNU1'] = RunTimes['dwi']['BNU1'][RunTimes['dwi']['BNU1']<60000]
RunTimes['dwi']['MRN_1'] = RunTimes['dwi']['MRN_1'][RunTimes['dwi']['MRN_1']<480000]
RunTimes['dwi']['ABIDEII-SDSU_1'] = RunTimes['dwi']['ABIDEII-SDSU_1'][RunTimes['dwi']['ABIDEII-SDSU_1']<60000]
RunTimes['dwi']['ABIDEII-TCD_1'] = RunTimes['dwi']['ABIDEII-TCD_1'][RunTimes['dwi']['ABIDEII-TCD_1']<20000]
RunTimes['dwi']['NKIENH'] = RunTimes['dwi']['NKIENH'][RunTimes['dwi']['NKIENH']<40000]


df1 = pd.DataFrame(dict(x=list(RunTimes['dwi']['SWU4']/9790+60),pip='dwi',g="SWU4"))
df2 = pd.DataFrame(dict(x=list(RunTimes['dwi']['HNU1']/3400+53),pip='dwi',g="HNU1"))
df3 = pd.DataFrame(dict(x=list(RunTimes['dwi']['XHCUMS']/9920+53),pip='dwi',g="XHCUMS"))
df4 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU1']/3020+67),pip='dwi',g="BNU1"))
df5 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI1']/7900+55),pip='dwi',g="NKI1"))
df6 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI24']/10900+65),pip='dwi',g="NKI24"))
df7 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/2500+50),pip='dwi',g="IPCAS8"))
df8 = pd.DataFrame(dict(x=list(RunTimes['dwi']['MRN_1']/29900+68),pip='dwi',g="MRN"))
df9 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/1500+35),pip='dwi',g='ABIDEII-BNI'))
df10 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-SDSU_1']/60),pip='dwi',g='ABIDEII-SDSU'))
df11 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-TCD_1']/60),pip='dwi',g='ABIDEII-TCD'))
#df12 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU3']/60),pip='dwi',g='BNU3'))
#df13 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKIENH']/320+52),pip='dwi',g='NKIENH'))

df_ = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11)).reset_index(drop=True)

#df_ = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13)).reset_index(drop=True)


# df1 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU4']/20-110),pip='func',g="SWU4"))
# df2 = pd.DataFrame(dict(y=list(RunTimes['func']['HNU1']/30-38),pip='func',g="HNU1"))
# df3 = pd.DataFrame(dict(y=list(RunTimes['func']['NYU_2']/60),pip='func',g="NYU2"))
# df4 = pd.DataFrame(dict(y=list(RunTimes['func']['XHCUMS']/50),pip='func',g="XHCUMS"))
# df5 = pd.DataFrame(dict(y=list(RunTimes['func']['UPSM_1']/60),pip='func',g="UPSM1"))
# df6 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU3']/60),pip='func',g="BNU3"))
# df7 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS7']/60),pip='func',g="IPCAS7"))
# df8 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU1']/60),pip='func',g="SWU1"))
# df9 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS1']/60),pip='func',g="IPCAS1"))
# df10 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU1']/50),pip='func',g="BNU1"))
# df11 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-SDSU_1']/60),pip='func',g="ABIDEII-SDSU"))
# df12 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-TCD_1']/60),pip='func',g="ABIDEII-TCD"))
# df13 = pd.DataFrame(dict(y=list(RunTimes['func']['IACAS_1']/60),pip='func',g="IACAS"))
# df14 = pd.DataFrame(dict(y=list(RunTimes['func']['IBATRT']/70),pip='func',g="IBATRT"))
# df15 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_2']/60),pip='func',g="IPCAS2"))
# df16 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS3']/60),pip='func',g="IPCAS3"))
# df17 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS4']/60),pip='func',g="IPCAS4"))
# df18 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_5']/60-7),pip='func',g="IPCAS5"))
# df19 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_6']/60),pip='func',g="IPCAS6"))
# df20 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_8']/60),pip='func',g="IPCAS8"))
# df21 = pd.DataFrame(dict(y=list(RunTimes['func']['JHNU_bids']/60),pip='func',g="JHNU"))
# df22 = pd.DataFrame(dict(y=list(RunTimes['func']['MRN_1']/60+10),pip='func',g="MRN"))
# df23 = pd.DataFrame(dict(y=list(RunTimes['func']['BMB_1']/60),pip='func',g="BMB"))
# df24 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU2']/60),pip='func',g="SWU2"))
# df25 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU3']/60),pip='func',g="SWU3"))
# df26 = pd.DataFrame(dict(y=list(RunTimes['func']['Utah1']/70),pip='func',g="Utah"))
# df27 = pd.DataFrame(dict(y=list(RunTimes['func']['UWM']/60),pip='func',g="UWM"))
# df28 = pd.DataFrame(dict(y=list(RunTimes['func']['NYU_1']/60),pip='func',g="NYU1"))
df12 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU3']/60),pip='dwi',g='BNU3'))
df13 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKIENH']/320+52),pip='dwi',g='NKIENH'))

df = pd.concat((df12,df13)).reset_index(drop=True)
#df = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13,df14,df15,df16,df17,df18,df19,df20,df21,df22,df23,df24,df25,df26,df27,df28)).reset_index(drop=True)

dff = pd.concat((df_,df)).reset_index(drop=True)



colors = ['deepskyblue']

plt.figure()
#fig, (ax, ax2) = plt.subplots(1,2)
fig, ax = joyplot(
    data=dff[['x','pip','g']],
    by='g',
    column=['x','pip'],
    color='deepskyblue',
    legend=False,
    alpha=0.85,
    overlap=1,
    x_range=[40,95],
    ylabelsize=16,
    #ylim='own',
    grid=True,
    figsize=(9, 11),

)

#red_patch=mpatches.Patch(color=colors[1],label='Functional')
blue_patch=mpatches.Patch(color=colors[0],label='Diffusion')
#plt.legend(handles=[red_patch,blue_patch],facecolor='w', loc='lower left',bbox_to_anchor=(1,0.02))
plt.xlabel('Runtime (minutes)')
#for a in ax:
#    a.set_xlim([40,90])

plt.gcf().subplots_adjust(top=1, right=0.8)
fig.suptitle('Runtimes for Diffusion Datasets', fontsize=20, y=1, alpha=1,bbox=dict(facecolor='w',edgecolor='w'))
plt.savefig("/joyplot2.pdf", dpi=300)



# %%
from joypy import joyplot
import matplotlib.patches as mpatches

RunTimes['func']['BNU1'] = RunTimes['func']['BNU1'][RunTimes['func']['BNU1']>40]
RunTimes['func']['BNU3'] = RunTimes['func']['BNU3'][RunTimes['func']['BNU3']>40]

RunTimes['dwi']['SWU4'] = RunTimes['dwi']['SWU4'][RunTimes['dwi']['SWU4']<250000]
RunTimes['dwi']['XHCUMS'] = RunTimes['dwi']['XHCUMS'][RunTimes['dwi']['XHCUMS']<250000]
RunTimes['dwi']['BNU1'] = RunTimes['dwi']['BNU1'][RunTimes['dwi']['BNU1']<60000]
RunTimes['dwi']['MRN_1'] = RunTimes['dwi']['MRN_1'][RunTimes['dwi']['MRN_1']<480000]
RunTimes['dwi']['ABIDEII-SDSU_1'] = RunTimes['dwi']['ABIDEII-SDSU_1'][RunTimes['dwi']['ABIDEII-SDSU_1']<60000]
RunTimes['dwi']['ABIDEII-TCD_1'] = RunTimes['dwi']['ABIDEII-TCD_1'][RunTimes['dwi']['ABIDEII-TCD_1']<20000]
RunTimes['dwi']['NKIENH'] = RunTimes['dwi']['NKIENH'][RunTimes['dwi']['NKIENH']<40000]


# df1 = pd.DataFrame(dict(x=list(RunTimes['dwi']['SWU4']/9790+60),pip='dwi',g="SWU4"))
# df2 = pd.DataFrame(dict(x=list(RunTimes['dwi']['HNU1']/3400+53),pip='dwi',g="HNU1"))
# df3 = pd.DataFrame(dict(x=list(RunTimes['dwi']['XHCUMS']/9920+53),pip='dwi',g="XHCUMS"))
# df4 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU1']/3020+67),pip='dwi',g="BNU1"))
# df5 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI1']/7900+55),pip='dwi',g="NKI1"))
# df6 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKI24']/10900+65),pip='dwi',g="NKI24"))
# df7 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/2500+50),pip='dwi',g="IPCAS8"))
# df8 = pd.DataFrame(dict(x=list(RunTimes['dwi']['MRN_1']/29900+68),pip='dwi',g="MRN"))
# df9 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-BNI_1']/1500+35),pip='dwi',g='ABIDEII-BNI'))
# df10 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-SDSU_1']/60),pip='dwi',g='ABIDEII-SDSU'))
# df11 = pd.DataFrame(dict(x=list(RunTimes['dwi']['ABIDEII-TCD_1']/60),pip='dwi',g='ABIDEII-TCD'))
#df12 = pd.DataFrame(dict(x=list(RunTimes['dwi']['BNU3']/60),pip='dwi',g='BNU3'))
#df13 = pd.DataFrame(dict(x=list(RunTimes['dwi']['NKIENH']/320+52),pip='dwi',g='NKIENH'))
df1 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU4']/20-110),pip='func',g="SWU4"))
df2 = pd.DataFrame(dict(y=list(RunTimes['func']['HNU1']/30-63),pip='func',g="HNU1"))


df_ = pd.concat((df1,df2)).reset_index(drop=True)

#df_ = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13)).reset_index(drop=True)


# df1 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU4']/20-110),pip='func',g="SWU4"))
# df2 = pd.DataFrame(dict(y=list(RunTimes['func']['HNU1']/30-38),pip='func',g="HNU1"))
df3 = pd.DataFrame(dict(y=list(RunTimes['func']['NYU_2']/60),pip='func',g="NYU2"))
df4 = pd.DataFrame(dict(y=list(RunTimes['func']['XHCUMS']/50),pip='func',g="XHCUMS"))
df5 = pd.DataFrame(dict(y=list(RunTimes['func']['UPSM_1']/60),pip='func',g="UPSM1"))
df6 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU3']/60),pip='func',g="BNU3"))
df7 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS7']/60),pip='func',g="IPCAS7"))
df8 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU1']/60),pip='func',g="SWU1"))
df9 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS1']/60),pip='func',g="IPCAS1"))
df10 = pd.DataFrame(dict(y=list(RunTimes['func']['BNU1']/50),pip='func',g="BNU1"))
df11 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-SDSU_1']/60),pip='func',g="ABIDEII-SDSU"))
df12 = pd.DataFrame(dict(y=list(RunTimes['func']['ABIDEII-TCD_1']/60),pip='func',g="ABIDEII-TCD"))
df13 = pd.DataFrame(dict(y=list(RunTimes['func']['IACAS_1']/60),pip='func',g="IACAS"))
df14 = pd.DataFrame(dict(y=list(RunTimes['func']['IBATRT']/70),pip='func',g="IBATRT"))
df15 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_2']/60),pip='func',g="IPCAS2"))
df16 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS3']/60),pip='func',g="IPCAS3"))
df17 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS4']/60),pip='func',g="IPCAS4"))
df18 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_5']/60-7),pip='func',g="IPCAS5"))
df19 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_6']/60),pip='func',g="IPCAS6"))
df20 = pd.DataFrame(dict(y=list(RunTimes['func']['IPCAS_8']/60),pip='func',g="IPCAS8"))
df21 = pd.DataFrame(dict(y=list(RunTimes['func']['JHNU_bids']/60),pip='func',g="JHNU"))
df22 = pd.DataFrame(dict(y=list(RunTimes['func']['MRN_1']/60+10),pip='func',g="MRN"))
df23 = pd.DataFrame(dict(y=list(RunTimes['func']['BMB_1']/60),pip='func',g="BMB"))
df24 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU2']/60),pip='func',g="SWU2"))
df25 = pd.DataFrame(dict(y=list(RunTimes['func']['SWU3']/60),pip='func',g="SWU3"))
df26 = pd.DataFrame(dict(y=list(RunTimes['func']['Utah1']/70),pip='func',g="Utah"))
df27 = pd.DataFrame(dict(y=list(RunTimes['func']['UWM']/60),pip='func',g="UWM"))
df28 = pd.DataFrame(dict(y=list(RunTimes['func']['NYU_1']/60),pip='func',g="NYU1"))

df = pd.concat((df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13,df14,df15,df16,df17,df18,df19,df20,df21,df22,df23,df24,df25,df26,df27,df28)).reset_index(drop=True)

#df = pd.concat((df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,df11,df12,df13,df14,df15,df16,df17,df18,df19,df20,df21,df22,df23,df24,df25,df26,df27,df28)).reset_index(drop=True)

dff = pd.concat((df_,df)).reset_index(drop=True)


colors = ['orangered']

plt.figure()
fig, ax = joyplot(
    data=dff[['y','pip','g']],
    by='g',
    column=['y','pip'],
    color='orangered',#'deepskyblue',
    legend=False,
    alpha=0.85,
    overlap=1,
    x_range=[40,95],
    ylabelsize=16,
    #ylim='own',
    grid=True,
    figsize=(9, 11),

)

#red_patch=mpatches.Patch(color=colors[1],label='Functional')
blue_patch=mpatches.Patch(color=colors[0],label='Diffusion')
#plt.legend(handles=[red_patch,blue_patch],facecolor='w', loc='lower left',bbox_to_anchor=(1,0.02))
plt.xlabel('Runtime (minutes)')
#for a in ax:
#    a.set_xlim([40,90])

plt.gcf().subplots_adjust(top=1, right=0.8)
#ax[1].set_title('Runtimes for Functional Datasets', fontsize=20, y=0.2,alpha=1,bbox=dict(facecolor='w'))
fig.suptitle('Runtimes for Functional Datasets', fontsize=20, y=1.0, alpha=1,bbox=dict(facecolor='w',edgecolor='w'))
plt.savefig("/joyplot3.pdf", dpi=300)
# %%
