#-------------------------Written by Ashby Cooper, 2016---------------------------
#-------------------------Stage 02 - Create LIP Shapefile-------------------------

'''
Script to calculate LIP heights form surrounding ocean floor as contours within the
LIP.
Outputs are:
   1. LIP_histograms/         --contains depth histograms for the LIP and surrounding
                              ocean floor.
   2. contour_polygons_0Ma    --shapefile with LIPs as contours


'''

##++++++++++++++ Import Modules ++++++++++++++++##

import os
import shutil
from osgeo import gdal, gdalnumeric, ogr, osr
import numpy as np
import matplotlib.pyplot as plt
from math import floor
from math import ceil



##+++++++++++++ File/Directory I/O +++++++++++++##

#read in the path text file
with open('temp_paths.txt', 'r') as f:
    temp_paths=f.read().split(' ')

path_LIP_Paleodepths=temp_paths[0]
path01=temp_paths[1]
path02=temp_paths[2]

from _02_Create_LIP_shapefile import stat_calc
from _02_Create_LIP_shapefile import get_isobands

path_histo=path02+'LIP_histograms/'
input_LIP_shp=path02+'LIP_polygons_0Ma.shp'
input_large_shp=path02+'large_polygons_0Ma.shp'
basement_raster=path02+'present_basedepth_reformat.grd'

#create directory to keep histogram plots
if not os.path.isdir(path_histo):
    os.mkdir(path_histo)



#### ------------- Re-format the basement raster file ------------ ####

if not os.path.exists(basement_raster):
    #call resamp shell script
    print 'Re-Formating the Present-Day Basement Grid:.....'
    os.chdir(path02)
    os.system('./reform.sh')    
    os.chdir(path_LIP_Paleodepths)
    print 'Done!...'
    print ''

else:
    print 'Found Re-Formated Present-Day Basement Grid!....'
    print ''


#### ------------- Open the basement raster file ------------ ####

raster_driver=gdal.GetDriverByName('GS7BG')
raster_driver.Register()

src=gdal.Open(basement_raster)
src_band = src.GetRasterBand(1)
src_array=src_band.ReadAsArray()


cols = src.RasterXSize
rows = src.RasterYSize
print 'Global Basement Raster Specifications: '
print "Cols: ",cols
print "Rows: ",rows

geotransform = src.GetGeoTransform()

originX = geotransform[0]
originY = geotransform[3]
pixelWidth = geotransform[1]
pixelHeight = geotransform[5]

print 'originX:     ', originX
print 'originY:     ', originY 
print 'pixelWidth:  ', pixelWidth
print 'pixelHeight: ', pixelHeight
print ''

x_pos = np.arange(originX, originX + cols*pixelWidth, pixelWidth)
y_pos = np.arange(originY, (originY + rows*pixelHeight), pixelHeight)
x_grid, y_grid = np.meshgrid(x_pos, y_pos)




##+++++++++ Process Data/Run Workflow ++++++++++##


#### ----------- Open the LIP and large shapefiles ---------- ####

# Create an OGR layer from LIP shapefile
LIP_shapefile_src=ogr.Open(input_LIP_shp, 1)
LIP_shapefile_layer=LIP_shapefile_src.GetLayer(0)

# Create an OGR layer from large shapefile
large_shapefile_src=ogr.Open(input_large_shp, 1)
large_shapefile_layer=large_shapefile_src.GetLayer(0)


LIP_feature=LIP_shapefile_layer.GetFeature(0)
LIP_geometry = LIP_feature.GetGeometryRef()

#create new attribute for the elevation of the surrounding seafloor
LIP_shapefile_layer.CreateField(ogr.FieldDefn("LRG_ELEV", ogr.OFTReal))
large_shapefile_layer.CreateField(ogr.FieldDefn("LRG_ELEV", ogr.OFTReal))


#### --------- Rasterize all the polygons in the layers ------ ####

#create a memory file for the LIP mask
LIP_mask_ds = gdal.GetDriverByName('MEM').Create('', cols, rows, 1, gdal.GDT_Float32)
LIP_mask_ds.SetGeoTransform(geotransform)
LIP_mask_band = LIP_mask_ds.GetRasterBand(1)

#create a memory file for the large mask
large_mask_ds = gdal.GetDriverByName('MEM').Create('', cols, rows, 1, gdal.GDT_Float32)
large_mask_ds.SetGeoTransform(geotransform)
large_mask_band = large_mask_ds.GetRasterBand(1)


# Rasterize both of the masks with 1 within the polygon and 0 elsewhere
gdal.RasterizeLayer(LIP_mask_ds, [1], LIP_shapefile_layer, burn_values=[1])
gdal.RasterizeLayer(large_mask_ds, [1], large_shapefile_layer, burn_values=[1])

#turn the mask rasters into arrays
LIP_mask_band = LIP_mask_ds.GetRasterBand(1)
LIP_mask_array=LIP_mask_band.ReadAsArray().astype(np.float32)

large_mask_band = large_mask_ds.GetRasterBand(1)
large_mask_array=large_mask_band.ReadAsArray().astype(np.float32)


#free up memory by closing memory mask files and removing temp shapefiles
LIP_mask_ds=None
large_mask_ds=None


print 'Removing LIP regions from large regions:......'
#remove the LIP region from the large mask
#add arrays together making nan outside large region, 1 inside large region (but outside LIP region) and 2 inside LIP region
temp_array=large_mask_array+LIP_mask_array


#replace all elements == 2 with 0
temp_array[temp_array == 2] = 0
new_large_mask_array=temp_array


#now generate the masked basement grids for LIP and large polygon
LIP_base_array=LIP_mask_array*src_array
large_base_array=new_large_mask_array*src_array
large_LIP_base_array=large_mask_array*src_array

#setting values of 0 to numpy nan
LIP_base_array[LIP_mask_array==0]=np.nan
large_base_array[new_large_mask_array==0]=np.nan


#### --------- Now calling a function to generate contours (isobands) ------ ####

#reading contour interval from temp file
with open('temp_cont.txt') as f:
    cont_int=int(f.read())
    
print 'Generating ',str(cont_int),'m Contours for large regions.....'
# gen_cont(x_grid, y_grid, LIP_array, levels, out)
stats = src_band.GetStatistics(True, True)


min_level=None

if min_level == None:
    min_value = stats[0]
    min_level = cont_int* floor((min_value)/cont_int)
   
max_value = stats[1]

#Due to range issues, a level is added
max_level = cont_int * (1 + ceil(max_value/cont_int))

levels = np.arange(min_level, max_level, cont_int)

if os.path.exists(path02+'isobands.shp'):
    os.remove(path02+'isobands.shp')

get_isobands.gen_cont(x_grid, y_grid, large_LIP_base_array, levels, path02+'isobands.shp')






#### -------- opening the recently created isoband shapefile as well as a new shapefile for final output contours ------ ####


output_contours=path02+'contour_polygons_0Ma.shp'

if os.path.exists(output_contours):
    os.remove(output_contours) 


iso_source=ogr.Open(path02+'isobands.shp', 1)
iso_layer=iso_source.GetLayer(0)

##create new shapefile
driver=ogr.GetDriverByName("ESRI Shapefile")
#create data source
cont_source=driver.CreateDataSource(output_contours)
#create spatial ref
srs=osr.SpatialReference()
srs.ImportFromEPSG(4326)
cont_layer=cont_source.CreateLayer("contours", srs, ogr.wkbPolygon)

##Add new fields
field_name=ogr.FieldDefn("NAME", ogr.OFTString)
field_name.SetWidth(24)
cont_layer.CreateField(field_name)
cont_layer.CreateField(ogr.FieldDefn("PLATEID", ogr.OFTInteger))
cont_layer.CreateField(ogr.FieldDefn("FROMAGE", ogr.OFTInteger))
cont_layer.CreateField(ogr.FieldDefn("TOAGE", ogr.OFTInteger))
cont_layer.CreateField(ogr.FieldDefn("LIPH", ogr.OFTReal))
cont_layer.CreateField(ogr.FieldDefn("LRG_ELEV", ogr.OFTReal))
cont_layer.CreateField(ogr.FieldDefn("CON_ELEV", ogr.OFTReal))
cont_layer.CreateField(ogr.FieldDefn("SHA_CONT", ogr.OFTReal))
cont_layer.CreateField(ogr.FieldDefn("DEP_CONT", ogr.OFTReal))


#### --------- Now looping through the individual LIPs and finding some statistics ------ ####


#iterate through every LIP in the large shapefile (contains only LIPs that we are interested in
for i in range(large_shapefile_layer.GetFeatureCount()):
    large_feature = large_shapefile_layer.GetFeature(i)
    large_geom=large_feature.GetGeometryRef()

    if not 'astrid' in large_feature.GetField("NAME"):
        continue
    
    print ''
    print '.........................................................................'
    print '................Conducting Stage 02 on LIP: ',large_feature.GetField("NAME").replace('_polygon', ''),'...............'
    print '.........................................................................'
    print ''

    #open the LIP shapefile and get the LIP feature (same index)
    LIP_feature = LIP_shapefile_layer.GetFeature(i)
    LIP_geom=LIP_feature.GetGeometryRef()

    # Get Envelope of large and LIP returns a tuple (minX, maxX, minY, maxY)
    large_extent = large_geom.GetEnvelope()
    LIP_extent=LIP_geom.GetEnvelope()

    print 'Clipping LIP array by extent of LIP polygon: .....'
    print "minX: %d, minY: %d, maxX: %d, maxY: %d" %(LIP_extent[0],LIP_extent[2],LIP_extent[1],LIP_extent[3])
    
    indexes_X=np.where((x_pos>=LIP_extent[0]) & (x_pos<=LIP_extent[1]))
    indexes_Y=np.where((y_pos>=LIP_extent[2]) & (y_pos<=LIP_extent[3]))

    rows = np.array(indexes_Y[0], dtype=np.intp)
    columns = np.array(indexes_X[0], dtype=np.intp)

    LIP_clipped_array=LIP_base_array[rows[:, np.newaxis], columns]


    print 'Clipping array by extent of large polygon: .....'
    print "minX: %d, minY: %d, maxX: %d, maxY: %d" %(large_extent[0],large_extent[2],large_extent[1],large_extent[3])
    
    indexes_X=np.where((x_pos>=large_extent[0]) & (x_pos<=large_extent[1]))
    indexes_Y=np.where((y_pos>=large_extent[2]) & (y_pos<=large_extent[3]))

    rows = np.array(indexes_Y[0], dtype=np.intp)
    columns = np.array(indexes_X[0], dtype=np.intp)

    large_clipped_array=large_base_array[rows[:, np.newaxis], columns]


    
    #imgplot = plt.imshow(large_clipped_array)
    #plt.show()

    
    #call calc_stats.py
    #call function that will calculate historgram stats and save histogram plot and then return histogram values to be written to LIP shapefile
    #inputs (numpy_array_large, output_histo_file, LIP_name)
    #returns (large_elev)

    large_elev=stat_calc.get_stats(large_clipped_array, LIP_clipped_array, path_histo+large_feature.GetField("NAME").replace('_polygon', '')+'.png', large_feature.GetField("NAME").replace('_polygon', ''))

    LIP_feature.SetField("LRG_ELEV", int(large_elev))
    large_feature.SetField("LRG_ELEV", int(large_elev))

    LIP_shapefile_layer.SetFeature(LIP_feature)
    large_shapefile_layer.SetFeature(large_feature)

    #### ---------- Clipping contours that are within LIP region and outputting to new shapefile ------------ #####


    deepest_cont=0
    shallowest_cont=-8000
    print 'Clipping the Isobands within the LIP regions .....'
    #now iterate through every feature in isoband layer:
    for j in range(iso_layer.GetFeatureCount()):
        iso_feature=iso_layer.GetFeature(j)
        iso_geo=iso_feature.GetGeometryRef()

        #see if the isoband intersects with LIP
        intersect=iso_geo.Intersects(LIP_geom)
            
        if intersect==True:

            #test to see if the LIPH is negative or not
            if iso_feature.GetField("ELEV")-int(large_elev)<0:
                continue

            new_isoband=iso_geo.Intersection(LIP_geom)

            #write the new geomerty to the contour layer
            cont_feature=ogr.Feature(cont_layer.GetLayerDefn())
            cont_feature.SetField("NAME", large_feature.GetField("NAME").replace('_polygon', ''))
            cont_feature.SetField("FROMAGE",LIP_feature.GetField("FROMAGE"))
            cont_feature.SetField("TOAGE",LIP_feature.GetField("TOAGE"))
            cont_feature.SetField("PLATEID", LIP_feature.GetField("PLATEID"))
            cont_feature.SetField("LIPH", iso_feature.GetField("ELEV")-int(large_elev))
            cont_feature.SetField("CON_ELEV", iso_feature.GetField("ELEV"))
            cont_feature.SetField("LRG_ELEV", int(large_elev))
            cont_feature.SetField("DEP_CONT", 0)
            cont_feature.SetField("SHA_CONT", 0)

            #find the deepest contour
            if iso_feature.GetField("ELEV") < deepest_cont:
                deepest_cont=iso_feature.GetField("ELEV")

            #find shallowest contour
            if iso_feature.GetField("ELEV") > shallowest_cont:
                shallowest_cont=iso_feature.GetField("ELEV")

            cont_feature.SetGeometry(new_isoband)
            cont_layer.CreateFeature(cont_feature)
    
            cont_feature.Destroy()


    #finally add the LIP outline to the contour shapefile but with unique name
    #write the new geomerty to the contour layer
    cont_feature=ogr.Feature(cont_layer.GetLayerDefn())
    cont_feature.SetField("NAME", large_feature.GetField("NAME").replace('_polygon', '')+'_outline')
    cont_feature.SetField("FROMAGE",LIP_feature.GetField("FROMAGE"))
    cont_feature.SetField("TOAGE",LIP_feature.GetField("TOAGE"))
    cont_feature.SetField("PLATEID", LIP_feature.GetField("PLATEID"))
    cont_feature.SetField("LIPH", deepest_cont-int(large_elev))
    cont_feature.SetField("CON_ELEV", deepest_cont)
    cont_feature.SetField("LRG_ELEV", int(large_elev))
    cont_feature.SetField("DEP_CONT", deepest_cont)
    cont_feature.SetField("SHA_CONT", shallowest_cont)

    cont_feature.SetGeometry(LIP_geom)
    cont_layer.CreateFeature(cont_feature)
    
    cont_feature.Destroy()


    print 'Done for ',large_feature.GetField("NAME").replace('_polygon', '')
    LIP_feature=None
    large_feature=None
    

print 'All Done!'
cont_source=None
LIP_shapefile_src=None
large_shapefile_src=None





