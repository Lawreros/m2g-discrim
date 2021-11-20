import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


z = pd.read_csv("ipsi_aal.csv", delimiter = " ")

# Use FacetGrid to create the facet with one column
ridge_plot = sns.FacetGrid(z, row="Dataset", hue="Type", aspect=15, height=0.5)#aspect=5, height=1.25)
# Use map function to make density plot in each element of the grid.
ridge_plot.map(sns.kdeplot, "Value", clip_on=False, fill=True, alpha=0.7, lw=4, bw=.2)
ridge_plot.map(plt.axhline, y=0, lw=4, clip_on=False)
ridge_plot.savefig("Ridgeline_plot_Seaborn_first_step.png")

x = 1
if x == 3:
    #pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
    g = sns.FacetGrid(z, row="Dataset", hue="Type", aspect=15, height=.5)#, palette=pal)

    # Draw the densities in a few steps
    g.map(sns.kdeplot, "Value",
        bw_adjust=.5, clip_on=False,
        fill=True, alpha=1, linewidth=1.5)
    g.map(sns.kdeplot, "Value", clip_on=False, color="w", lw=2, bw_adjust=.5)
    g.map(plt.axhline, y=0, lw=2, clip_on=False)


    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, .2, label, fontweight="bold", color=color,
                ha="left", va="center", transform=ax.transAxes)


    g.map(label, "Dataset")

    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-.25)

    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[])
    #g.set(xlim=(20,65))
    g.despine(bottom=True, left=True)
    plt.savefig("Ridgeline_plot_Seaborn_first_step.png", dpi=300)