#-------------------------Written by Ashby Cooper, 2016---------------------------
#-------------------------Stage 02 - Create LIP Shapefile-------------------------

'''
Script to generate statistics for the LIP and surrounding seafloor polygon.
Outputs are:
    1. LIP_histograms/      --histogram plot for LIP, LIP+surrounds and surrounds
    2. modal depth of surrounding seafloor is returned to main script to calculate
    LIP height of contours.
'''

##++++++++++++++ Import Modules ++++++++++++++++##

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
import matplotlib.colors
matplotlib.rc('xtick', labelsize=9)
matplotlib.rc('ytick', labelsize=9)


def get_stats(large_array, LIP_array, output_histo_file, LIP_name):
    
    print ''
    print '...............................................................'
    print '....Now using Python to produce histograms for the data........'
    print '...............................................................'
    print ''
    print 'Getting values from historgram............'

    histoLIP=np.histogram(LIP_array, bins=80, range=[-8000,0])
   
    #########------------------------User Input Optional --------------------------######

    #find the mode for the LIP from the histogram information
    index_minLIP=histoLIP[0].argmax()
    value1=histoLIP[1][index_minLIP]
    maxdepth=int(value1/100)*100

    histolarge_no_mod=np.histogram(large_array, bins=80, range=[-8000,0])

    #strip all values from large array that are above the modal depth of the LIP
    large_array[large_array>int(maxdepth)]=np.nan

    histolarge=np.histogram(large_array, bins=80, range=[-8000,0])
    
    #find the mode for the large polygon from the histogram information
    #this can be changed to the mean etc... see the numpy documentation for further details.
    index_minlarge=histolarge[0].argmax()
    value1=histolarge[1][index_minlarge]

    #the mode funtionality returns the most frequently occuring value
    #we want a rough estimate that corresponds with the bin size of the histograms
    #the below will get the value of the left side of the bin that the modal value is in.
    mindepth=int(value1/100)*100

    #########----------------------------------------------------------------------######

    print ''
    print 'Finished calculating statistics.............'
    print ''
    print 'LIP Modal Depth=            ', maxdepth
    print 'Surrounding Sea-Floor Depth=', mindepth
    print 'Outputting Histogram plot........'

    #if the histogram already exists exit script
    if os.path.exists(output_histo_file):
        print 'Done with stat_calc.py.........'
        print ''
        return mindepth


    #-------Plotting the histogram data for the lIP, large polygon and modified large polygon -----------
    #note: Matplotlib has its own histogram plotting functionality
    #this should not affect the histogram

    titlename='Histogram output for '+LIP_name
    
    #plot the three plots on the same figure side by side
    f, (ax1, ax2, ax3) = plt.subplots(1, 3, sharey=True)

    f.text(0.5, 0.95, titlename, ha='center',fontsize=10)
    f.text(0.5, 0.03, 'Frequency', ha='center',fontsize=9)
    f.text(0.03, 0.5, 'Depth (m)', va='center', rotation='vertical',fontsize=9)

    ax1.set_title('LIP Histogram', fontsize=9)
    ax2.set_title('LIP + Surrounds Histogram', fontsize=9)
    ax3.set_title('Surrounds Histogram', fontsize=9)
    
    ax1.set_ylim([-8000,0])
    ax2.set_ylim([-8000,0])
    ax3.set_ylim([-8000,0])

    for tick in ax1.get_xticklabels():
        tick.set_rotation(60)

    for tick in ax2.get_xticklabels():
        tick.set_rotation(60)

    for tick in ax3.get_xticklabels():
        tick.set_rotation(60)


    hist1, bins1 = histoLIP
    hist2, bins2 = histolarge_no_mod
    hist3, bins3 = histolarge


    bin_centers1 = (bins1[:-1] + bins1[1:]) / 2
    bin_centers2 = (bins2[:-1] + bins2[1:]) / 2
    bin_centers3 = (bins3[:-1] + bins3[1:]) / 2
    
    patches1=ax1.barh(bin_centers1, hist1, align='center', height=100, alpha=0.9)
    patches2=ax2.barh(bin_centers2, hist2, align='center', height=100, alpha=0.9)
    patches3=ax3.barh(bin_centers3, hist3, align='center', height=100, alpha=0.9)

    
    #-------- Lets highlight the modal bin in red and add a blue to dark blue colour gradient to the histogram bins.

    #the colour map
    cm = plt.cm.get_cmap('Blues_r')
 
    #get the colour for the bin
    col1 = bin_centers1 - min(bin_centers1)
    col2 = bin_centers2 - min(bin_centers2)
    col3 = bin_centers3 - min(bin_centers3)
    col1 /= max(col1)
    col2 /= max(col2)
    col3 /= max(col3)

    #set counter
    count=-1
    #iterate through the histogram bins and the colour map and set colour
    for c, p in zip(col1, patches1):
        count=count+1
        if count == index_minLIP:
            plt.setp(p, 'facecolor', 'r')
        else:
            plt.setp(p, 'facecolor', cm(c))

    count=-1
    for c, p in zip(col2, patches2):
        count=count+1
        if count == index_minLIP or count == index_minlarge:
            plt.setp(p, 'facecolor', 'r')
        else:
            plt.setp(p, 'facecolor', cm(c))

    count=-1
    for c, p in zip(col3, patches3):
        count=count+1
        if count == index_minlarge:
            plt.setp(p, 'facecolor', 'r')
        else:
            plt.setp(p, 'facecolor', cm(c))


            
    #save the output image
    f.savefig(output_histo_file, dpi=480)

    plt.close()

    print 'Done with stat_calc.py.........'
    print ''
    return mindepth
