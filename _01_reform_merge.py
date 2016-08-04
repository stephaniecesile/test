#-------------------------Written by Ashby Cooper, 2016--------------------------
#-------------------------Stage 01 - Create LIP Polygons-------------------------



'''
Script to read in .dat files with individual LIP polygons and surrounding seafloor
(large) polygons using Gplates, merging all LIPs together then outputting them as a
shapefile.
Output is two shapefiles (and supporting files) in the directory: 02_Create_LIP_shapefile
    -LIP_polygons_0Ma.shp           -- Contains LIP polygons at present day 
    -large_polygons_0Ma.shp         -- Contains surrounding seafloor polygons at present day
'''



##++++++++++++++ Import Modules ++++++++++++++++##

import pygplates
from osgeo import ogr, osr
import os
import shutil




##+++++++++++++ File/Directory I/O +++++++++++++##

#read in the path text file
with open('temp_paths.txt', 'r') as f:
    temp_paths=f.read().split(' ')

path01=temp_paths[1]
path02=temp_paths[2]

output_LIP_shp=path02+'LIP_polygons_0Ma.shp'
output_large_shp=path02+'large_polygons_0Ma.shp'

path_LIP_dat=path01+'polygons/real/'
path_large_dat=path01+'polygons/large/'

#remove the output file if it already exists
if os.path.exists(output_LIP_shp):
    os.remove(output_LIP_shp)
if os.path.exists(output_large_shp):
    os.remove(output_large_shp)



    
##+++++++++++++ Define Functions +++++++++++++++##    

#function to remove space elements from list
def rem_space(a):
    b=[]
    for element in a:
        if not element=='':
            b.append(element)
    return b


#function to convert well-known-text line features to polygons
def forceToPoly(a):
    #if multilinestring
    if str(a)[0]=='M':
        sub=str(a)[16:]
        elements=sub.split('),(')
        wkt='MULTIPOLYGON ((('
        for i in range(len(elements)):
            poly=elements[i].replace('(', '').replace(')', '')
            wkt=wkt+poly+')),(('
        wkt=wkt[0:len(wkt)-3]+')'       
    #if linestring
    elif str(a)[0]=='L':
        wkt='POLYGON ('+str(a)[11:]+')'
    return wkt




##+++++++++ Process Data/Run Workflow ++++++++++##

#define empty lists to dump LIP shapefile objects into    
LIP_merged_polys=[]
large_merged_polys=[]

#get list of files in path_large_dat
large_list=os.listdir(path_large_dat)

#iterate through the large polygons
for large_poly in large_list:
    if large_poly[0]=='.':
        continue

    #print 'Working on: ',large_poly.replace('_polygon.dat', '')


    #LIP polygon .dat file
    LIP_dat=path_LIP_dat+large_poly.replace('_polygon.dat', '')+'.dat'
    #large polygon .dat file
    large_dat=path_large_dat+large_poly


    #make a temporary lip shapefile
    temp_LIP_shp=path01+'temp_LIP.shp'
    temp_large_shp=path01+'temp_large.shp'

   
    #make the LIP .dat file into shapefile
    LIP_feature=pygplates.FeatureCollection(LIP_dat)
    LIP_feature.write(temp_LIP_shp)

    #make the large .dat file into shapefile
    large_feature=pygplates.FeatureCollection(large_dat)
    large_feature.write(temp_large_shp)

    #open the recently created LIP and large shapefiles into OGR
    LIP_source=ogr.Open(temp_LIP_shp, 1)
    LIP_layer=LIP_source.GetLayer(0)

    large_source=ogr.Open(temp_large_shp, 1)
    large_layer=large_source.GetLayer(0)

    #get the LIP and large feature
    LIP_feature=LIP_layer.GetFeature(0)
    large_feature=large_layer.GetFeature(0)


    #### ------ Creating new temp shapefile for updated polygons ----- ####
    
    ##create new shapefile
    driver=ogr.GetDriverByName("ESRI Shapefile")
    #create spatial ref
    srs=osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    #create LIP data source
    LIP_new_source=driver.CreateDataSource(path01+'temp_2_LIP.shp')
    LIP_new_layer=LIP_new_source.CreateLayer("LIPs", srs, ogr.wkbPolygon)

    #create large data source
    large_new_source=driver.CreateDataSource(path01+'temp_2_large.shp')
    large_new_layer=large_new_source.CreateLayer("large", srs, ogr.wkbPolygon)

    ##Add new fields to LIP layer
    field_name=ogr.FieldDefn("NAME", ogr.OFTString)
    field_name.SetWidth(24)
    LIP_new_layer.CreateField(field_name)
    LIP_new_layer.CreateField(ogr.FieldDefn("PLATEID", ogr.OFTInteger))
    LIP_new_layer.CreateField(ogr.FieldDefn("FROMAGE", ogr.OFTInteger))
    LIP_new_layer.CreateField(ogr.FieldDefn("TOAGE", ogr.OFTInteger))

    ##Add new fields to large layer
    large_new_layer.CreateField(field_name)
    large_new_layer.CreateField(ogr.FieldDefn("PLATEID", ogr.OFTInteger))
    large_new_layer.CreateField(ogr.FieldDefn("FROMAGE", ogr.OFTInteger))
    large_new_layer.CreateField(ogr.FieldDefn("TOAGE", ogr.OFTInteger))


    

    #### ------ Converting the feture to a polygon and saving ---- ####
    LIP_geometry = LIP_feature.GetGeometryRef()
    #call the function to convert to polygon
    LIP_wkt=forceToPoly(LIP_geometry)
    LIP_polygon=ogr.CreateGeometryFromWkt(LIP_wkt)
    LIP_polygon.CloseRings()
    
    large_geometry = large_feature.GetGeometryRef()
    #call the function to convert to polygon
    large_wkt=forceToPoly(large_geometry)
    large_polygon=ogr.CreateGeometryFromWkt(large_wkt)


    #set shapefile attribute fields
    LIP_new_feature=ogr.Feature(LIP_new_layer.GetLayerDefn())
    LIP_new_feature.SetField("NAME", large_poly.replace('_polygon.dat', ''))
    LIP_new_feature.SetField("FROMAGE",LIP_feature.GetField("FROMAGE"))
    LIP_new_feature.SetField("TOAGE",LIP_feature.GetField("TOAGE"))
    LIP_new_feature.SetField("PLATEID",LIP_feature.GetField("PLATEID1"))
    #create the geomerty object
    LIP_new_feature.SetGeometry(LIP_polygon)
    LIP_new_layer.CreateFeature(LIP_new_feature)
    
    LIP_new_feature.Destroy()
    

    #set shapefile attribute fields
    large_new_feature=ogr.Feature(large_new_layer.GetLayerDefn())
    large_new_feature.SetField("NAME", large_poly.replace('.dat', ''))
    large_new_feature.SetField("FROMAGE",large_feature.GetField("FROMAGE"))
    large_new_feature.SetField("TOAGE",large_feature.GetField("TOAGE"))
    large_new_feature.SetField("PLATEID",large_feature.GetField("PLATEID1"))
    #create the geomerty object
    large_new_feature.SetGeometry(large_polygon)
    large_new_layer.CreateFeature(large_new_feature)
    
    large_new_feature.Destroy()

    #set the OGR source empty
    LIP_new_source=None
    large_new_source=None

    
    #make the shapefile into a new feature and append it to the merged list
    LIP_feature=pygplates.FeatureCollection(path01+'temp_2_LIP.shp')
    LIP_merged_polys.extend(LIP_feature)
    large_feature=pygplates.FeatureCollection(path01+'temp_2_large.shp')
    large_merged_polys.extend(large_feature)


    if os.path.exists(temp_LIP_shp):
        os.remove(temp_LIP_shp)
    if os.path.exists(temp_large_shp):
        os.remove(temp_large_shp)

    if os.path.exists(path01+'temp_2_LIP.shp'):
        os.remove(path01+'temp_2_LIP.shp')
    if os.path.exists(path01+'temp_2_large.shp'):
        os.remove(path01+'temp_2_large.shp')


#write the merged polygons to a shapefile
LIP_merged_poly_collection=pygplates.FeatureCollection(LIP_merged_polys)
LIP_merged_poly_collection.write(output_LIP_shp)
large_merged_poly_collection=pygplates.FeatureCollection(large_merged_polys)
large_merged_poly_collection.write(output_large_shp)

#remove all temp files in the path01 directory
files = os.listdir(path01)
for file in files:
    if 'temp' in file:
        os.remove(path01+file)
