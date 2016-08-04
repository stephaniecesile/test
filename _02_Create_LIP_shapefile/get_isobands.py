#-------------------------Written by Ashby Cooper, 2016---------------------------
#-------------------------Stage 02 - Create LIP Shapefile-------------------------

'''
Script to generate contours of the regions within the large LIP polygons (including LIP)
for all LIPs. Interval is defined in run_all script.
outputs:
    1. isobands.shp  --shapefile containing contours within regions this is later clipped
    with the LIP outlines to get contours just within LIP.

#Note: Taken from:
http://geoexamples.blogspot.com.au/2013/08/creating-vectorial-isobands-with-python.html
'''

##++++++++++++++ Import Modules ++++++++++++++++##

import os
from osgeo import gdal, gdalnumeric, ogr, osr
import numpy as np
import matplotlib.pyplot as plt



def gen_cont(x_grid, y_grid, LIP_array, levels, out):

    #Generate layer to save Contourlines in
    ogr_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(out)
    contour_layer = ogr_ds.CreateLayer('contour')
    contour_layer.CreateField(ogr.FieldDefn("ELEV", ogr.OFTReal))
    
    contours = plt.contourf(x_grid, y_grid, LIP_array, levels)


    for level in range(len(contours.collections)):
        paths = contours.collections[level].get_paths()
        for path in paths:

            feat_out = ogr.Feature( contour_layer.GetLayerDefn())
            feat_out.SetField("ELEV", contours.levels[level] )
            pol = ogr.Geometry(ogr.wkbPolygon)


            ring = None            
    
            for i in range(len(path.vertices)):
                point = path.vertices[i]
                if path.codes[i] == 1:
                    if ring != None:
                        pol.AddGeometry(ring)
                    ring = ogr.Geometry(ogr.wkbLinearRing)
    
                ring.AddPoint_2D(point[0], point[1])
    
    
            pol.AddGeometry(ring)
    
            feat_out.SetGeometry(pol)
            if contour_layer.CreateFeature(feat_out) != 0:
                print "Failed to create feature in shapefile.\n"
                exit( 1 )

    
            feat_out.Destroy()



    
    ogr_ds=None

    return
