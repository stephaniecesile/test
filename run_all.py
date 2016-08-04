#-------------------------Written by Ashby Cooper, 2016--------------------------
#-----------------------Run All LIP Paleodepths Workflow-------------------------

'''
Script to run everything in the LIP Paleodepths workflow.
The User must update the path information below (depending on user's system)
The cooling models variable is a list of the abbreiviated cooling models to be processed
'''

##++++++++++++++ Import Modules ++++++++++++++++##
import os



##+++++++++++++ File/Directory I/O +++++++++++++##

#########------------------------User Input Required --------------------------######

#define the paths dependant on User's system
path_LIP_Paleodepths='/Volumes/Macintosh_HD_2/LIP_Paleodepths/'
path01=path_LIP_Paleodepths+'_01_Create_LIP_Polygons/'
path02=path_LIP_Paleodepths+'_02_Create_LIP_shapefile/'
path03=path_LIP_Paleodepths+'_03_Rotate_Polygons/'
path04=path_LIP_Paleodepths+'_04_Create_LIP_Height_Grids/'
path05=path_LIP_Paleodepths+'_05_Add_Grids/'
rot_frame_path=path03+'/ref_frames/'

#specify the rotation file used to rotate the LIPs
rot_frame='Seton_etal_ESR2012_Global_EarthByte_2012_Seton2012.rot'

#specify the cooling models used to calculate the seafloor subsidence and swell height 
cooling_models=['static_swell']#, 'stein_stein', 'parsons_sclater', 'hasterok']#, 'static_swell_buffer', 'hasterok_buffer','no_swell','stein_stein','parsons_sclater','hasterok','stein_stein_buffer','parsons_sclater_buffer']


#specify the contour interval for LIP height calculation (smaller interval increses processing time
contour_int=1000

#########----------------------------------------------------------------------######


#get the abrreviated string for a rotation file.
#i.e. Seton_etal_ESR2012_Global_EarthByte_2012_Seton2012.rot ==> Seton2012
rot_frame_abr=rot_frame.split('_')[6].replace('.rot', '')

#create savefile for the path info
savefile=open('temp_paths.txt', 'w')
savefile.write(path_LIP_Paleodepths+' '+path01+' '+path02+' '+path03+' '+path04+' '+path05)
savefile.close()

#create a savefile for the rotation file path and abbreiviated name
savefile=open('temp_runfile.txt', 'w')
savefile.write(rot_frame_path+rot_frame+' '+rot_frame_abr)
savefile.close()

#create a savefile for the contour interval
savefile=open('temp_cont.txt', 'w')
savefile.write(str(contour_int))
savefile.close()






##+++++++++ Process Data/Run Workflow ++++++++++##

#First:
#Run _01_Create_LIP_Polygons to create shapefiles for the LIP and large polygons
print 'Running _01_reform_merge.py............'
#execfile(path01+'_01_reform_merge.py')
#clear the terminal output
os.system('clear')


#Second:
#Run 02_Create_LIP_shapefile to calculate contours and LIP heights from surrounding ocean floor
print 'Running _01_write_LIP_shp.py............'
#execfile(path02+'_01_write_LIP_shp.py')
os.system('clear')

#create a directory based on the rotation file name
if not os.path.exists(path03+rot_frame_abr):
    os.mkdir(path03+rot_frame_abr)


### Now run the rotation script for the given rotation frame
print 'Running _01_rotate.py............'
#execfile(path03+'_01_rotate.py')


#iterate through cooling models specified
for cool in cooling_models:
    print ''
    print '#### --------------------------------------------------------------- ####'
    print '#### --------------------- Working on: ', cool, ' ----------------- ####'
    print '#### --------------------------------------------------------------- ####'
    print ''

    #temp savefile for cooling model name and rotation name
    savefile=open('temp_coolfile.txt', 'w')
    savefile.write(rot_frame_abr+' '+cool)
    savefile.close()

    print 'Running 01_buffer_calc.py.........'
    execfile(path04+'01_buffer_calc.py')
    print 'Running 02_rearrange.py...........'
    execfile(path04+'02_rearrange.py')
    print 'Running 03_calc_height.py.........'
    execfile(path04+'03_calc_height.py')

    print 'Running graph_cooling.py........'
    execfile(path03+'graph_cooling.py')

#run script to combine the LIP height grids to the basement grids (calculated form agegrids)
os.chdir(path05)
print 'Running combine_time.py........'
execfile(path05+'01_combine_time.py')



#os.remove('temp_coolfile.txt')
os.remove('temp_runfile.txt')
#os.remove('options_temp.txt')
os.remove('temp_paths.txt')
os.remove('temp_cont.txt')

