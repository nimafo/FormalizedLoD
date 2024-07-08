if __name__ == "__main__":
    pass


# Dependencies
import numpy as np
import trimesh
from scipy.spatial.qhull import QhullError
import uuid
import os
import shutil
import subprocess
import datetime
import matplotlib.pyplot as plt
import json
import gzip
from SALib.analyze import morris
from SALib.plotting import morris as plot_morris
import re
import scipy.stats as stats
from scipy.stats import norm, lognorm, gamma, foldnorm, kstest
import pandas as pd
from typing import Union
import random
import matplotlib.font_manager as fm

#Functions for Dynamic Daylighting Simulation(DDS)
def set_radiance_variables():
    '''sets the radiance variables '''
    # Get the current values of the environment variables
    path = os.environ.get('PATH', '')
    raypath = os.environ.get('RAYPATH', '')
    manpath = os.environ.get('MANPATH', '')

    # Specify the paths to be added
    new_path = '/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/bin:' + path
    new_raypath = '/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/lib'
    new_manpath = '/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/man'

    # Update the environment variables
    os.environ['PATH'] = new_path
    os.environ['RAYPATH'] = new_raypath
    os.environ['MANPATH'] = new_manpath

    # Optionally, export the variables (specific to Unix-like systems)
    os.system('export PATH RAYPATH MANPATH')

    # Print the updated values
    print(os.environ.get('PATH', ''))
    print(os.environ.get('RAYPATH', ''))
    print(os.environ.get('MANPATH', ''))
def make_folders(Base_folder):#creates the folder structure for daylight simulation
    object_folder = Base_folder+"objects/"
    skydomes_folder = Base_folder+"skydomes/"
    octrees_folder = Base_folder+"octrees/"
    matrices_folder = Base_folder+"matrices/"
    matrices_cds_folder = matrices_folder + "cds/"
    dc_folder = matrices_folder+"dc/"
    dcd_folder = matrices_folder+"dcd/"
    assets_folder = Base_folder+"assets/"
    skyvectors_folder = Base_folder+"skyvectors/"
    results_folder = Base_folder + "results/"
    results_dcDDS = results_folder+"dcDDS/"
    results_dcDDS_cds = results_dcDDS+"cds/"
    results_DDS_dc = results_dcDDS+"dc/"
    results_DDS_dcd = results_dcDDS+"dcd/"
    skies_folder = Base_folder+"skies/"
    os.mkdir(Base_folder)
    os.mkdir(object_folder)
    os.mkdir(skydomes_folder)
    os.mkdir(octrees_folder)
    os.mkdir(matrices_folder)
    os.mkdir(dc_folder)
    os.mkdir(dcd_folder)
    os.mkdir(assets_folder)
    os.mkdir(skyvectors_folder)
    os.mkdir(results_folder)
    os.mkdir(results_dcDDS)
    os.mkdir(results_DDS_dc)
    os.mkdir(results_DDS_dcd)
    os.mkdir(skies_folder)
    os.mkdir(matrices_cds_folder)
    os.mkdir(results_dcDDS_cds)
    return Base_folder,object_folder,skydomes_folder,octrees_folder,matrices_folder,dc_folder,dcd_folder,assets_folder,skyvectors_folder,results_folder,results_dcDDS,results_DDS_dc,results_DDS_dcd,skies_folder,matrices_cds_folder,results_dcDDS_cds
def materials_rad(room):#generate the materials.rad
    '''generate the materials.rad
    inputs:
    room: dictionary of the procedurally generated room'''

    #write the material file for each of the surfaces in room_xyz dictionary
    string = ''
    for key in room:
        #put the material properties of each surface in a variable `prop`
        if room[key]["material"]["mat_type"] == "plastic":
            prop = f'5 {room[key]["material"]["reflectance"]} {room[key]["material"]["reflectance"]} {room[key]["material"]["reflectance"]} {room[key]["material"]["roughness"]} {room[key]["material"]["specularity"]}'
        elif room[key]["material"]["mat_type"] == "glass":
            #prop = f'3 {room[key]["material"]["tr"]} {room[key]["material"]["tr"]} {room[key]["material"]["tr"]}'
            prob = "This is glass"
        else:
            prop = None
        string = string + f'void {room[key]["material"]["mat_type"]} {key}\n0\n0\n{prop}\n \n'    
    return 
def add_random_object_to_rad_files(random_mesh,Base_folder):#adds the random_mesh to the existing room
    '''create the randomobject.rad, modify materials.rad, room.rad, '''
    #step1 create the randomobject.rad and put it in objects folder
    xyz = ''
    for face in range(len(random_mesh["mesh"].faces)):
        xyz_str = ''
        for vertex in range(len(random_mesh["mesh"].faces[face])):
            xyz_str+= str(random_mesh["mesh"].vertices[random_mesh["mesh"].faces[face][vertex]]).replace("[","").replace("]","\n  ")
        #xyz.append(xyz_str)
        xyz_str
    #xyz

    material_string = ''
    for i in range(len(xyz)):
        material_string+=(f'randomobject polygon {str(uuid.uuid1()).replace("-", "_")}\n0\n0\n{9} {xyz_str}\n\n')
    print(material_string[1])
    to_rad(object_folder,"randomobject",material_string)

    #step2 modify materials.rad
    material_file = f'{Base_folder}materials.rad'
    with open(material_file, 'a') as file:
        #file.write(f'void plastic randomobject\n0\n0\n5 {random_mesh["material"]["reflectance"]} {random_mesh["material"]["reflectance"]} {random_mesh["material"]["reflectance"]} {random_mesh["material"]["reflectance"]} {random_mesh["material"]["reflectance"]}\n \n')
        file.write(f'void plastic randomobject\n0\n0\n5 0 0 0 0 0\n \n')

    #step3 modify room.rad
    room_rad_file = f'{Base_folder}room.rad'
    with open(room_rad_file, 'a') as file:
        file.write(f'!xform ./objects/randomobject.rad')
    roomblack_rad_file = f'{Base_folder}roomBlack.rad'
    with open(roomblack_rad_file, 'a') as file:
        file.write(f'!xform -m black ./objects/randomobject.rad')
def to_rad(dir_name, base_filename, content): #.rad for a single surface
    outfile = open(os.path.join(dir_name, base_filename + '.' + 'rad'), 'a')
    outfile.write(content)
def write_objs(to_simulate, object_folder, print=0): 
    for key in to_simulate:
        if print:
            print(key)
            print(to_simulate[key]['file_address'])
        with open(to_simulate[key]['file_address'],'r') as obj_file:
            for line in obj_file:
                if line.startswith('g'): #assumes there is only one group in each input .obj
                    modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                cmd = rf"obj2rad '{to_simulate[key]['file_address']}' > '{os.path.join(object_folder,modifier_name+'.rad')}'"
        os.system(cmd)      
def write_materials(Base_folder, to_simulate):
    string = ''
    for key in to_simulate:
        if to_simulate[key]['attributes']['transparency_type'] == 'opaque':
            #find modifiers name
            with open(to_simulate[key]['file_address'],'r') as obj_file:
                for line in obj_file:
                    if line.startswith('g'): #assumes there is only one group in each input .obj
                        modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                        
            #create material string
            material_string_opaque = f"void plastic {modifier_name}\n0\n0\n5 "+\
                f"{to_simulate[key]['attributes']['material']['R']} "+\
                f"{to_simulate[key]['attributes']['material']['G']} "+\
                f"{to_simulate[key]['attributes']['material']['B']} "+\
                f"{to_simulate[key]['attributes']['material']['roughness']} "+\
                f"{to_simulate[key]['attributes']['material']['specularity']}\n\n"
                
            #print(material_string_opaque)
            string+=material_string_opaque
        elif to_simulate[key]['attributes']['transparency_type'] == 'transparent':
            with open(to_simulate[key]['file_address'],'r') as obj_file:
                for line in obj_file:
                    if line.startswith('g'): #assumes there is only one group in each input .obj
                        modifier_name = "_".join(line.strip().split(sep=" ")[1:])
            material_string_transparent = f"void glass {modifier_name}\n0\n0\n3 "+\
                f"{to_simulate[key]['attributes']['material']['R']} "+\
                f"{to_simulate[key]['attributes']['material']['G']} "+\
                f"{to_simulate[key]['attributes']['material']['B']}\n\n"
            #print(material_string_transparent)
            string+=material_string_transparent

    outfile = open(os.path.join(Base_folder, 'materials.rad'), 'w')
    if string != '':
        outfile.write(string)
def write_room(Base_folder, to_simulate):
    room_rad = ""
    room_black_rad = ""
    for key in to_simulate:
        if to_simulate[key]['attributes']['transparency_type'] == 'opaque':
            #find modifiers name
            with open(to_simulate[key]['file_address'],'r') as obj_file:
                for line in obj_file:
                    if line.startswith('g'): #assumes there is only one group in each input .obj
                        modifier_name = "_".join(line.strip().split(sep=" ")[1:])
            room_rad += "!xform ./objects/"+modifier_name+".rad\n"
            room_black_rad += "!xform -m black ./objects/"+modifier_name+".rad\n"
    print(room_rad)

    ##write to file
    outfile = open(os.path.join(Base_folder, 'room.rad'), 'w')
    if room_rad != '':
        outfile.write(room_rad)
    #outfile.close()
    outfile_black = open(os.path.join(Base_folder, 'roomBlack.rad'), 'w')
    if room_black_rad != '':
        outfile_black.write(room_black_rad)
    #outfile.close()
def AnnualSimulation(to_simulate:dict,epw_file:str, grid_points_txt:str,base_dir:str, rad_params:dict={'-lw': 0.0001, '-ab': 5, '-ad': 10000}, wea_:str=None, direcory_cleanup:bool=True):
        simulation_run_name = str(datetime.datetime.now()).replace(" ", "_").replace("-", "").replace(":", "_").replace(".", "_")+f"_{str(uuid.uuid1())}"
        print("Simulation run name is:"+ simulation_run_name)
        base_folder = rf'{base_dir}/{simulation_run_name}/'
        print("Len to_simulate: "+str(len(to_simulate)))
        
        Base_folder,object_folder,skydomes_folder,octrees_folder,matrices_folder,dc_folder,dcd_folder,assets_folder,skyvectors_folder,results_folder,results_dcDDS,results_DDS_dc,results_DDS_dcd,skies_folder,matrices_cds_folder,results_dcDDS_cds = make_folders(base_folder)

        #Write the rad objects
        write_objs(to_simulate, object_folder)

        #Write material
        write_materials(Base_folder, to_simulate)

        #Write room.rad
        write_room(Base_folder, to_simulate)
            
        #Write points and count the number of sensors 
        shutil.copy2(grid_points_txt, os.path.join(Base_folder, "points.txt"))

        with open(grid_points_txt, 'r') as file:
            sensor_points_count = 0
            for line in file:
                if line.strip():  # check if line is not empty
                    sensor_points_count += 1

        # Write skyglow.rad
        reinhart_subdivisions = 2
        skydome = f'''#@rfluxmtx u=+Y h=u\nvoid glow groundglow\n0\n0\n4 1 1 1 0\n\ngroundglow source ground\n0\n0\n4 0 0 -1 180\n\n\n#@rfluxmtx u=+Y h=r{reinhart_subdivisions}\nvoid glow skyglow\n0\n0\n4 1 1 1 0\n\nskyglow source skydome\n0\n0\n4 0 0 1 180'''
        to_rad(skydomes_folder, "skyglow", skydome)

        #make the material black
        MaterialBlack = '#Black material that will be used for 5 phase calculations and Descretized daylight simulation \nvoid plastic black \n0 \n0 \n5 0 0 0 0 0'
        to_rad(Base_folder, "materialBlack", MaterialBlack)

        # Space separated string for the transparent surfaces to put it instead of Window.rad in oconv
        windows = '' # space separated string for the transparent surfaces and put it instead of Window.rad
        for key in to_simulate:
            if to_simulate[key]['attributes']['transparency_type'] == 'transparent':
                with open(to_simulate[key]['file_address'],'r') as obj_file:
                    for line in obj_file:
                        if line.startswith('g'): #assumes there is only one group in each input .obj
                            modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                windows+=("'"+object_folder+modifier_name+".rad"+"'")
                windows+=" "
        
        
        os.chdir(f'{Base_folder}')
        
        
        
        '''DDS -- STEP 1: Perform an annual daylight coefficient simulation > dcDDS/dc/annualR.ill'''
        print("running STEP 1")#OCTREE creation
        print("running oconv...")
        result = subprocess.run(f"oconv '{Base_folder}materials.rad' '{Base_folder}room.rad' {windows} > '{octrees_folder}roomDC.oc'", shell=True ) 

        
        print("running rfluxmtx...")#Daylight Coefficient creation
        result = subprocess.run(f"rfluxmtx -I+ -y {sensor_points_count} -lw {rad_params['-lw']} -ab {rad_params['-ab']} -ad {rad_params['-ad']} -n 16 - {skydomes_folder}skyglow.rad -i {octrees_folder}roomDC.oc < {Base_folder}points.txt > {dc_folder}illum.mtx", shell=True)
        epw_name = os.path.basename(epw_file)
        if wea_ == None:
            wea = f"{assets_folder}{epw_name[:-4]}.wea"
            try:#weatherfile preparation
                result = subprocess.run(f'cp {epw_file} {assets_folder}', shell=True)
            except:
                print("EPW copy failed")
                raise
            #wea creation
            print("running epw2wea...")
            result = subprocess.run(f'epw2wea {epw_file} {wea}', shell=True ,stdout = subprocess.PIPE) 
            ##Create an annual daylight matrix with 145 patches
        else:
            wea = wea_
            
        print("running gendaymtx...")
        result = subprocess.run(f'gendaymtx -m {reinhart_subdivisions} {wea} > {skyvectors_folder}{epw_name[:-4]}.smx', shell=True ,stdout = subprocess.PIPE)
        #results step 1
        print("running dctimestep...")
        result = subprocess.run(f'dctimestep {dc_folder}illum.mtx {skyvectors_folder}{epw_name[:-4]}.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {results_DDS_dc}annualR.ill', shell=True ,stdout = subprocess.PIPE)



        '''DDS -- STEP 2 : Perform an annual direct-only daylight coefficients simulation > dcd/annualR.ill'''
        #STEP 2: Perform an annual direct-only daylight coefficients simulation. 
        ##Create black octree for direct sun calculations.
        print("Performing the direct-only part...")
        print("running oconv...") 
        result = subprocess.run(f"oconv '{Base_folder}materialBlack.rad' '{Base_folder}materials.rad' '{Base_folder}roomBlack.rad' {windows} > '{octrees_folder}roomDCBlack.oct'", shell=True ,stdout = subprocess.PIPE)
        #Daylight Coefficient creation
        print("running rfluxmtx...") 
        result = subprocess.run(f'rfluxmtx -I+ -y {sensor_points_count} -lw {rad_params["-lw"]} -ab 1 -ad {rad_params["-ad"]} -n 16 - {skydomes_folder}skyglow.rad -i {octrees_folder}roomDCBlack.oct < {Base_folder}points.txt > {dcd_folder}illum.mtx', shell=True)
        ##Create an annual daylight matrix with 145 patches
        print("running gendaymtx...") 
        result = subprocess.run(f'gendaymtx -m {reinhart_subdivisions} {wea} > {skyvectors_folder}{epw_name[:-4]}_d.smx', shell=True ,stdout = subprocess.PIPE)
        #results step 2
        print("running dctimestep...") 
        result = subprocess.run(f'dctimestep {dcd_folder}illum.mtx {skyvectors_folder}{epw_name[:-4]}_d.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {results_DDS_dcd}annualR.ill', shell=True ,stdout = subprocess.PIPE)


        '''STEP 3 -- Perform an annual sun-coefficients simulation.> dcDDS/cds/annualR.ill'''
        print("running STEP3...") 
        print("running cnt 5165...") 
        ##Create sun primitive definition for solar calculations.
        result = subprocess.run(f"echo 'void light solar 0 0 3 1e6 1e6 1e6' > {skies_folder}suns.rad" , shell=True ,stdout = subprocess.PIPE)
        ##Create solar discs and corresponding modifiers for 5165 suns corresponding to a Reinhart MF:6 subdivision. 
        cmd= f"cnt 5165 | rcalc -e MF:{reinhart_subdivisions} -f reinsrc.cal" + " -e Rbin=recno -o 'solar source sun 0 0 4 ${Dx} ${Dy} ${Dz} 0.533'"
        to_rad(skies_folder,'suns',os.popen(cmd).read())
        print("running oconv...") 
        ##Create an octree black octree, shading device with proxy BSDFs and solar discs. 
        result = subprocess.run(f'oconv -f {Base_folder}materialBlack.rad {skies_folder}suns.rad {Base_folder}materials.rad {Base_folder}roomBlack.rad {windows} > {octrees_folder}sunCoefficientsDDS.oct' , shell=True ,stdout = subprocess.PIPE)
        print("running rcontriib...") 
        ##Calculate illuminance sun coefficients for illuminance calculations. 
        result = subprocess.run(f'rcontrib -I+  -y {sensor_points_count} -n 16 -lw {rad_params["-lw"]} -ab 1 -ad {rad_params["-ad"]} -dc 1 -dt 0 -dj 0 -faf -e MF:{reinhart_subdivisions} -f reinhart.cal -b rbin -bn Nrbins -m solar {octrees_folder}sunCoefficientsDDS.oct < {Base_folder}points.txt > {matrices_cds_folder}cdsDDS.mtx'  , shell=True ,stdout = subprocess.PIPE)
        print("running gendaymtx...") 
        #Create sun matrix with 5165 suns 
        result = subprocess.run(f'gendaymtx -5 0.533 -d -m {reinhart_subdivisions} {wea} > {skyvectors_folder}{epw_name[:-4]}sunM6.smx', shell=True ,stdout = subprocess.PIPE)
        print("running dctimestep...") 
        ##RESULTS 
        result = subprocess.run(f'dctimestep {matrices_cds_folder}cdsDDS.mtx {skyvectors_folder}{epw_name[:-4]}sunM6.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {results_dcDDS_cds}annualR.ill' , shell=True ,stdout = subprocess.PIPE)


        '''Final step:Combine results '''
        ##Final Step: Combine results
        print('running Final Step, rmtxop...')
        result = subprocess.run(f'rmtxop {results_DDS_dc}annualR.ill + -s -1 {results_DDS_dcd}annualR.ill + {results_dcDDS_cds}annualR.ill > {results_dcDDS}annualR.ill' , shell=True ,stdout = subprocess.PIPE)

        '''postprocessing the annual.ill file'''
        with open(f'{results_dcDDS}annualR.ill', "r") as file:
            lines = file.readlines()
            lines = lines[13:]
        with open(f'{results_dcDDS}annualR_clean.ill', "w") as file:
            file.writelines(lines)
        data = np.genfromtxt(f'{results_dcDDS}annualR_clean.ill', delimiter=' ')

        #Save HDR render
        #longitude, latitude = get_location(epw_file)
        #res = subprocess.run(f"gendaymtx -m 1 -d -O4 -o {skyvectors_folder}skyHDR.mtx 6 21 12 {longitude} {latitude}",shell=True)
        if direcory_cleanup:
            #Direcory Cleanup
            to_remove = [base_folder]
            #to_remove=[results_folder, object_folder,matrices_folder, octrees_folder, skyvectors_folder, skies_folder, skydomes_folder, assets_folder]
            #to_remove=[ object_folder, matrices_folder, octrees_folder, skyvectors_folder, skies_folder, skydomes_folder, assets_folder]
            for i in to_remove:
                shutil.rmtree(i)
        return data, simulation_run_name

# Method of morris, SA, Ranking
def _sort_Si(Si, key, sortby="mu_star"):
    return np.array([Si[key][x] for x in np.argsort(Si[sortby])])
def _sort_Si_by_index(Si, key, index):
    return np.array([Si[key][x] for x in index])
def horizontal_bar_plot(ax, Si, opts=None, sortby="mu_star", unit=""):
    """Updates a matplotlib axes instance with a horizontal bar plot
    of mu_star, with error bars representing mu_star_conf.
    """
    assert sortby in ["mu_star", "mu_star_conf", "sigma", "mu"]

    if opts is None:
        opts = {}

    # Sort all the plotted elements by mu_star (or optionally another
    # metric)
    names_sorted = _sort_Si(Si, "names", sortby)
    mu_star_sorted = _sort_Si(Si, "mu_star", sortby)
    mu_star_conf_sorted = _sort_Si(Si, "mu_star_conf", sortby)

    # Plot horizontal barchart
    y_pos = np.arange(len(mu_star_sorted))
    plot_names = names_sorted

    out = ax.barh(
        y_pos,
        mu_star_sorted,
        xerr=mu_star_conf_sorted,
        align="center",
        color='grey',
        ecolor="black",
        **opts
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_names)
    ax.set_xlabel(r"$\mu^\star$" + unit)

    ax.set_ylim(min(y_pos) - 1, max(y_pos) + 1)

    return out
def get_location(epw_file):
    with open(epw_file, 'r') as f:
        for line in f:
            match = re.match(r'^LOCATION,.*?,(-?\d+\.\d+),(-?\d+\.\d+)', line)
            if match:
                longitude = float(match.group(1))
                latitude = float(match.group(2))
                return longitude, latitude
    raise ValueError('Could not find location information in EPW file')
## vizualization
#source: https://salib.readthedocs.io/en/latest/_modules/SALib/plotting/morris.html#covariance_plot
def covariance_plot(ax, Si,problem:dict, opts=None, unit=""):
    """Plots mu* against sigma or the 95% confidence interval"""
    if opts is None:
        opts = {}

    if Si["sigma"] is not None:
        # sigma is not present if using morris groups
        #y = Si["sigma"]
        #out = ax.scatter(Si["mu_star"] , y, c=[*range(len(Si["mu_star"]))], cmap=plt.cm.viridis, edgecolors='black', s=100)
        out = ax.scatter(Si["mu_star"], Si["sigma"], c=list(range(problem['names'])), cmap=plt.cm.viridis, edgecolors='black', s=100)
        ax.set_xlim(
            0,
        )
        ax.set_ylim(
            0,
        )

        x_axis_bounds = np.array(ax.get_xlim())

        # (line1,) = ax.plot(x_axis_bounds, x_axis_bounds, "k-")
        # (line2,) = ax.plot(x_axis_bounds, 0.5 * x_axis_bounds, "k--")
        # (line3,) = ax.plot(x_axis_bounds, 0.1 * x_axis_bounds, "k-.")

        # ax.legend(
        #     (line1, line2, line3),
        #     (
        #         r"$\sigma / \mu^{\star} = 1.0$",
        #         r"$\sigma / \mu^{\star} = 0.5$",
        #         r"$\sigma / \mu^{\star} = 0.1$",
        #     ),
        #     loc="best",
        # )
        ax.legend(handles=out.legend_elements()[0], labels=problem['names'], bbox_to_anchor=(1, 1))
        (line1,) = ax.plot(x_axis_bounds, x_axis_bounds, "k-")
        (line2,) = ax.plot(x_axis_bounds, 0.5 * x_axis_bounds, "k--")
        (line3,) = ax.plot(x_axis_bounds, 0.1 * x_axis_bounds, "k-.")

        lines = [line1, line2, line3]
        labels = [r"$\sigma / \mu^{\star} = 1.0$", r"$\sigma / \mu^{\star} = 0.5$", r"$\sigma / \mu^{\star} = 0.1$"]
        handles = out.legend_elements()[0]
        handles_legend = ax.legend(handles, problem['names'], bbox_to_anchor=(1, 1))

        ax.legend(lines, labels, loc="best")
        ax.add_artist(handles_legend)
        #legend1 = ax.legend(handles=scatter.legend_elements()[0], labels=classes, bbox_to_anchor=(1, 1))
        #plt.gca().add_artist(legend1)

    else:
        y = Si["mu_star_conf"]
        out = ax.scatter(Si["mu_star"] , y, c=[*range(len(Si["mu_star"]))], cmap=plt.cm.viridis, edgecolors='black', s=100)
        ax.set_ylabel(r"$95\% CI$")

    ax.set_xlabel(r"$\mu^\star$ " + unit)
    ax.set_ylim(
        0 - (0.01 * np.array(ax.get_ylim()[1])),
    )

    return out
def morris_plt(results_folder,problem):
    '''Morrisplots, inputs: results folder,including the results_info.json'''
    os.chdir(results_folder)
    # Open JSON file
    with open('results_info.json', 'r') as f:
        # Load JSON data
        json_data = json.load(f)
    json_data = json.loads(json_data)

    for i in json_data["simulationResults"].keys():    
        # Open gzip file
        with gzip.open(f"{results_folder}/{i}.csv.gz", 'rt') as f:
            data = np.loadtxt(f, delimiter=',')
        json_data["simulationResults"][i].append(TAI(data))



    #analyze
    X = np.empty((0, 4))
    Y = np.empty((0, 1))
    for i in json_data["simulationResults"].keys():
        x_i = np.array(json_data["simulationResults"][i][:4]).reshape(1, 4)
        y_i = np.array(json_data["simulationResults"][i][4]).reshape(1, 1)
        X = np.concatenate((X, x_i), axis=0)
        Y = np.concatenate((Y, y_i), axis=0)

    #Sorting the results 
    results_mean = {
        'TAI' : Y
        }

    Si ={
        "TAI": morris.analyze(problem, X, results_mean['TAI'], conf_level=0.95, print_to_console=True, num_levels=8)
    }



    # Plotting the results 
    plt.rcParams['font.family'] = 'Times New Roman'
    fig, ax = plt.subplots(1,2,dpi=200,figsize=(9,4))
    # mu*
    for key in Si:
        ax[0].set_title(f'{key} [klx hrs]')
        p = plot_morris.horizontal_bar_plot(ax[0], Si[key], opts = {'color':'grey', 'alpha': 0.85, 'height':0.35})
        ax[0].grid(axis='x')
        ax[0].set_axisbelow(True)
        ax[0].set_xlim(left=0)
    
    # Covariance plot
    for key in Si:
        ax[1].set_title(f'{key} [klx hrs]')
        #define data
        x = Si[key]['mu_star'].data
        y = Si[key]['sigma']
        #define values, classes, and colors to map 
        #scatter
        values = [0, 1, 2, 3]
        colors = ['#8092bf', '#768f71', '#921e21', '#ffbb31']
        ax[1].grid(True)
        scatter = ax[1].scatter(x, y, c=values,cmap=plt.cm.tab20b, edgecolors='grey', s=50, zorder=2, marker='o')
        #scatter = ax[1].scatter(x, y, c=colors, edgecolors='black', s=100, zorder=2, marker='x')
        #scatter = ax[1].scatter(x, y, c=colors,  s=100, zorder=2,marker='.')
        x_axis_bounds = np.array([0, 1.2*max(x)])
        (line1,) = ax[1].plot(x_axis_bounds, x_axis_bounds, "k-",zorder=1)
        (line2,) = ax[1].plot(x_axis_bounds, 0.5 * x_axis_bounds, "k--", zorder=1)
        (line3,) = ax[1].plot(x_axis_bounds, 0.1 * x_axis_bounds, "k-.", zorder=1)
        lines = [line1, line2, line3]
        labels = [r"$\sigma / \mu^{\star} = 1.0$       ", r"$\sigma / \mu^{\star} = 0.5$       ", r"$\sigma / \mu^{\star} = 0.1$       "]
        ax[1].set_axisbelow(True)


    #legend
    ## create the second legend
    scatter_handles, scatter_labs= scatter.legend_elements()
    #scatter_labels = ['transmittance', r"$\rho$", 'Roughness','Specularity'] #
    scatter_labels = problem['names']
    scatter_legend = ax[1].legend(scatter_handles, scatter_labels, bbox_to_anchor=(1, 1))
    ## create a new legend that combines both legends
    handles = lines + scatter_handles
    labels = labels + scatter_labels
    combined_legend = ax[1].figure.legend(handles, labels,loc='upper right', bbox_to_anchor=(1.08, 0.88), borderaxespad=0.)
    ## remove the original legends
    scatter_legend.remove()

    ax[1].set_xlim([0, 1.2*max(x)])
    ax[1].set_ylim([0, 1.2*max(y)])
    ax[1].set_xlabel("\u03BC\u002A", fontstyle='italic')
    ax[1].set_ylabel("\u03C3", fontstyle='italic')

    plt.grid(True)
    plt.show()
    
'''Data visualisations for Uncertainty Quantification of the model
             MCOA
     0.05 0.10 0.15 0.20  < Invalid measurement(std > 0.2)
     |____|____|____|____|    (1) varying mcoa histogram
     |____|____|____|____|    (1) varying mcoa histogram
GLOD |____|____|____|____|    (1) varying mcoa histogram
     |____|____|____|____|    (1) varying mcoa histogram
  GT |____|____|____|____|    (1) varying mcoa histogram
'''
#Post processing
def udi(data):
    '''UDI function, outputs the UDI for each node in the grid as a list'''
    udi_300_ = []
    udi_300_3000_ = []
    udi_above_3000_ = []
    for node in range(len(data.T)):
        udi_300 = 0
        udi_300_3000 = 0
        udi_above_3000 = 0
        for i in range(len(data[:,node:node+1])):
            if data[:,node:node+1][i] <300:
                udi_300+=1
            elif 300 <= data[:,node:node+1][i] <3000:
                udi_300_3000 +=1
            elif data[:,node:node+1][i] >=3000:
                udi_above_3000+=1
        udi_300_.append(100*(udi_above_3000/len(data[:,node:node+1])))
        udi_300_3000_.append(100*(udi_300_3000/len(data[:,node:node+1])))
        udi_above_3000_.append(100*(udi_300/len(data[:,node:node+1])))
    return udi_300_ , udi_300_3000_, udi_above_3000_
def TAI(data): 
    '''Total annual illumination in klux.hours averaged over sensor points, returns a float [klux.hours/year]'''
    sensor_count, hours_count = data.shape
    return (np.sum(data.flatten())/(1000*sensor_count))
def nullified_array(results_array: np.array):
    '''Applies the occupancy schedule to the results array'''
    time_path = r"/scratch/nforouzandehsh/SA_optical-properties/referencesFiles/timesofYear.csv"
    time_array = np.array(pd.read_csv(time_path)) #array with time stamps
    total_array = np.concatenate((time_array, results_array), axis=1) #array with results and time stamps
    nullified_array = total_array.copy()
    index_to_delete = []
    for i in range(len(total_array)):
        timestamp = datetime.datetime.strptime(total_array[i][0], '%m/%d/%Y %H:%M:%S')
        if timestamp.hour < 8 or timestamp.hour > 17:
            index_to_delete.append(i)
    nullified_array = np.delete(nullified_array, index_to_delete, axis=0)
    #print(f"nullified_array.shape : {nullified_array.shape}")
    nullified_array = np.delete(nullified_array, 0, axis=1)
    return nullified_array
def D_A(data, DA_threshld = 300):
    DA_ = []
    for node in range(len(data.T)):
        DA=0
        for i in range(len(data[:,node:node+1])): #For TimeStep
            if data[:,node:node+1][i] >=DA_threshld:
                DA+=1
        DA_.append(100*(DA/len(data[:,node:node+1])))
    return DA_
def min_max_normalize(data):
    min_value = min(data)
    max_value = max(data)
    normalized_data = []
    for value in data:
        normalized_value = (value - min_value) / (max_value - min_value)
        normalized_data.append(normalized_value)
    return normalized_data
def sensor_timesteps_count(data):
    #sensor count from rows, and hours from column count
    sensor_count, hours_count = data.shape
    return sensor_count, hours_count
def CountNegative(res:str):
    '''counts the percentage of negative values relative the all the non-zero values
    input: ill.csv.gz'''
    arr = np.array(pd.read_csv(res))
    count = round(100 * np.sum(arr < 0)/ np.sum(arr != 0),3)
    return count

class UQviz:
    '''postprocessing the results,
    input: a folder path containig all spaces, glods, and mcoa
    str path:                       Path to the directory containing csv.gz results
    bool set_negative_lux_to_zero:  If False, calculates the number of negative values and pyt in the results_dict
    bool Calculate_TAI:             Calculates TAI if True'''
    def __init__(self, 
                 path:str,
                 set_negative_lux_to_zero:bool=False, 
                 calculate_TAI:bool=False,
                 calculate_UDI:bool=False,
                 calculate_grid_LE:bool=False,
                 calculate_mean_UDI_300_3000:bool=False,
                 spaceID:str="s06", 
                 calculate_time_series_LE:bool=False, 
                 threshold:int=0,
                 font_path:str=r'/scratch/nforouzandehsh/SA_optical-properties/referencesFiles/times.ttf'):
        '''
        calculate_time_series_LE: if True, calculates the time series light exposure(TAI)
        path: the path to the folder containing all the results
        spaceID: the space ID to be analysed
        calculate_TAI: if True, calculates the TAI for each simulation
        set_negative_lux_to_zero: if True, sets the negative lux values to zero
        threshold: the maximum number of points to be plotted in the histogram'''
        
        self.size = len(os.listdir(path))
        self.path = path
        self.threshold = threshold
        files = os.listdir(path)
        results = {}
        self.spaceID = spaceID
        self.font_path = font_path
        for file in files:
            name = os.path.basename(file)[:-7]
            if name and file.endswith("csv.gz") and file.startswith(spaceID):                    
                space = name.split(sep="_")[0]
                glod = name.split(sep="_")[1]
                mcoa = name.split(sep="_")[2]
                results[name]={'space':space, 'glod':glod, 'mcoa':mcoa, 'negative[%]':None, 'TAI': None}
                #processed attributes
                if set_negative_lux_to_zero or calculate_TAI or calculate_time_series_LE or calculate_UDI or calculate_mean_UDI_300_3000 or calculate_grid_LE:
                    array = np.array(pd.read_csv(os.path.join(path,os.path.basename(file))))
                    array = nullified_array(array)
                    if set_negative_lux_to_zero:
                        array[array<0] = 0
                    else:
                        self.negatives = CountNegative(os.path.join(self.path,file))
                        results[name]['negative[%]'] = self.negatives              
                    
                    if calculate_TAI:
                        tai = TAI(array)
                        results[name]['TAI'] = tai
                        
                    if calculate_time_series_LE: #light exposure for the whole room in each time step
                        results[name]['time_series_LE'] = list(np.mean(array, axis=1))
                        
                    if calculate_grid_LE: #light exposure for the whole room in each time step
                        results[name]['grid_LE'] = list(np.mean(array, axis=0))
                        
                    if calculate_UDI or calculate_mean_UDI_300_3000:
                        udi_300_ , udi_300_3000_, udi_above_3000_ = udi(array)
                        
                        if calculate_UDI:
                            results[name]['udi_300'] = udi_300_
                            results[name]['udi_300_3000'] = udi_300_3000_
                            results[name]['udi_above_3000'] = udi_above_3000_
                        if calculate_mean_UDI_300_3000:
                            results[name]['mean_udi_300_3000'] = np.mean(udi_300_3000_)
                        
                
        print("Number of simulations: ", len(results))
        if threshold:      
            mcoas = [0.05,0.1,0.15,0.20]
            glods = [0,1,2,3,4]
            for mcoa in mcoas:
                for glod in glods:
                    count = 0
                    for key in results.keys():
                        if results[key]['mcoa'] == str(mcoa) and results[key]['glod'] == str(glod):
                            count +=1
                    #print(f"count: {count}, mcoa: {mcoa}, glod: {glod}")
                    deleted_pairs = 0  # Track the number of deleted pairs
                    keys_to_delete = []  # Store the keys to delete here
                    if deleted_pairs < count - threshold:        
                        for key in results.keys():  # Convert keys to a list to avoid modifying the dict while iterating
                            if results[key]['mcoa'] == str(mcoa) and results[key]['glod'] == str(glod):
                                #del results[key]
                                keys_to_delete.append(key)
                                deleted_pairs += 1
                                if deleted_pairs >= count - threshold:
                                    break
                    for key in keys_to_delete:
                        del results[key]
        print("Number of simulations after thresholding: ", len(results))
        self.results_dict = results # dict containint keys as file names and values with GLOD, MCOA,and space information                         
    def generate_summary(self):
        dictionary = self.results_dict
        summary = {}
        # Count occurrences for each category
        for key in dictionary:
            item = dictionary[key]
            space_id = item['space']
            glod = item['glod']
            mcoa = item['mcoa']

            if space_id not in summary:
                summary[space_id] = {'total': 0, 'glod_counts': {}}

            if glod not in summary[space_id]['glod_counts']:
                summary[space_id]['glod_counts'][glod] = {'total': 0, 'mcoa_counts': {}}

            if mcoa not in summary[space_id]['glod_counts'][glod]['mcoa_counts']:
                summary[space_id]['glod_counts'][glod]['mcoa_counts'][mcoa] = 0

            summary[space_id]['total'] += 1
            summary[space_id]['glod_counts'][glod]['total'] += 1
            summary[space_id]['glod_counts'][glod]['mcoa_counts'][mcoa] += 1

        # Generate the summary string
        summary_string = "Summary:\n"
        for space_id, space_info in summary.items():
            summary_string += f"- {space_id}: {space_info['total']} occurrences, out of which:\n"
            for glod, glod_info in space_info['glod_counts'].items():
                summary_string += f"    - glod{glod}: {glod_info['total']} occurrences,\n"
                mcoa_counts = glod_info['mcoa_counts']
                for mcoa, count in mcoa_counts.items():
                    summary_string += f"        - mcoa{mcoa}: {count} occurrences,\n"

        # Remove trailing commas and return the summary string
        return summary_string.rstrip(",\n")
    def rmse_grid(self,outpath:str="/scratch/nforouzandehsh/SA_optical-properties/plots and results"):
        '''calculates the rmse for each point over the 8760 hours of the year and saves to the output -- benchmark is the MCOA0 with the same GLOD'''
        
        results_dict = self.results_dict
        #RMSE calculation
        for glod_ in [0,1,2,3,4]:
            for key in results_dict.keys():#find the benchmark
                if results_dict[key]['mcoa'] == '0' and results_dict[key]['glod'] == str(glod_) and results_dict[key]['space'] == self.spaceID:
                    bm_address = os.path.join(self.path,f"{key}.csv.gz")
                    bm = np.array(pd.read_csv(bm_address))
                    bm = nullified_array(bm)
                    
            for key in results_dict.keys():#calculate RMSE for all
                if results_dict[key]['glod'] == str(glod_) and results_dict[key]['space'] == self.spaceID:
                    array1 = np.array(pd.read_csv(os.path.join(self.path,f"{key}.csv.gz")))
                    array1= nullified_array(array1)
                    rmse_array = np.sqrt(np.mean((array1 - bm) ** 2,axis=0))
                    results_dict[key]['rmse_grid'] = rmse_array.tolist()

        with open(os.path.join(outpath, rf"results_dict_RMSEGrid_{self.spaceID}.json"), 'w') as out:
            json.dump(results_dict,out)
        print(f"Output path is written to {outpath}")
    def Error_histograms(self,glod:int, analysis_type: Union['ape', 'rmse'],benchmark_glod:int=None):
        '''Histogram plot from TAI API errors for each glod in multiple mcoa --
        valid spaceIDs from generate_summary function
        '''
        results_dict = self.results_dict
        if benchmark_glod is None:
            benchmark_glod = glod
        
        
        if analysis_type == 'rmse':
            #RMSE calculation
            for key in results_dict.keys():
                if results_dict[key]['mcoa'] == '0' and results_dict[key]['glod'] == str(benchmark_glod) and results_dict[key]['space'] == self.spaceID:
                    bm_address = os.path.join(self.path,f"{key}.csv.gz")
                    bm = np.array(pd.read_csv(bm_address))
            for key in results_dict.keys():
                array1 = np.array(pd.read_csv(os.path.join(self.path,f"{key}.csv.gz")))
                array1 = nullified_array(array1)
                rmse = np.sqrt(np.mean((array1 - bm) ** 2))
                results_dict[key][analysis_type] = rmse
            
        elif analysis_type == 'ape':
            
            #ape calculation
            for key in results_dict.keys():
                if not results_dict[key]['TAI']:
                    raise ValueError("TAI is not calculated")
                    break
                    
                if results_dict[key]['mcoa'] == '0' and results_dict[key]['glod'] == str(benchmark_glod) and results_dict[key]['space'] == self.spaceID:
                    benchmark = results_dict[key]['TAI']
            print(f"Benchmark TAI for GLOD{glod} and MCOA0 is {benchmark} klux.hrs")
            for key in results_dict.keys():
                ape = 100 * (results_dict[key]['TAI'] - benchmark)/benchmark
                results_dict[key][analysis_type] = ape
        else:
            print("Invalid analysis type")
                
        #monte carlo
        acc_level_1 = [results_dict[key][analysis_type] for key in results_dict.keys() if results_dict[key]['mcoa']==str(0.05) and results_dict[key]['space']==self.spaceID and results_dict[key]['glod']==str(glod)]
        acc_level_2 = [results_dict[key][analysis_type] for key in results_dict.keys() if results_dict[key]['mcoa']==str(0.10) and results_dict[key]['space']==self.spaceID and results_dict[key]['glod']==str(glod)]
        acc_level_3 = [results_dict[key][analysis_type] for key in results_dict.keys() if results_dict[key]['mcoa']==str(0.15) and results_dict[key]['space']==self.spaceID and results_dict[key]['glod']==str(glod)]
        acc_level_4 = [results_dict[key][analysis_type] for key in results_dict.keys() if results_dict[key]['mcoa']==str(0.20) and results_dict[key]['space']==self.spaceID and results_dict[key]['glod']==str(glod)]
        print(f"MCOA1 len{len(acc_level_1)}, MCOA2 len{len(acc_level_2)}, MCOA3 len{len(acc_level_3)}, MCOA4 len{len(acc_level_4)}, \n only the first {self.threshold} is selected for plotting")
            
            
        # Set the font to Times New Roman
        font_path = '/scratch/nforouzandehsh/SA_optical-properties/referencesFiles/times.ttf'  # Replace with the actual path to the font file
        font_prop = fm.FontProperties(fname=font_path, size=12)
        plt.rcParams['font.family'] = font_prop.get_name()
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10,6), dpi=200)
        font_path = '/scratch/nforouzandehsh/SA_optical-properties/referencesFiles/times.ttf'  # Replace with the actual path to the font file
        font_prop = fm.FontProperties(fname=font_path, size=12)
        plt.rcParams['font.family'] = font_prop.get_name()


        if analysis_type == 'ape':
            # Plot histograms of the data
            n1, bins1, patches1 = ax.hist(acc_level_1, bins=100, label=f'TAI-MCOA0.05', alpha=0.5, color='red') #[{len(acc_level_1)}]
            n2, bins2, patches2 = ax.hist(acc_level_2, bins=100, label=f'TAI-MCOA0.10', alpha=0.5, color='green') #[{len(acc_level_2)}]
            n3, bins3, patches3 = ax.hist(acc_level_3, bins=100, label=f'TAI-MCOA0.15', alpha=0.5, color='orange') #[{len(acc_level_3)}]
            n4, bins4, patches4 = ax.hist(acc_level_4, bins=100, label=f'TAI-MCOA0.20', alpha=0.5, color='brown') #[{len(acc_level_4)}]
            colors = ['red', 'green','orange','brown']

            # Fit distributions to the data and plot their PDFs
            ax2 = ax.twinx()  # create a single twinx axis for both PDFs
            for i, (acc_level, n, bins, patches) in enumerate(zip([acc_level_1, acc_level_2, acc_level_3,acc_level_4], [n1, n2,n3,n4], [bins1, bins2,bins3,bins4], [patches1, patches2,patches3,patches4])):
                # Fit a normal distribution to the data
                mu, sigma = stats.norm.fit(acc_level)

                # Generate x values for plotting the PDF
                x = np.linspace(-150, max(acc_level), 100)

                # Calculate the PDF of the fitted distribution at each x value
                pdf = stats.norm.pdf(x, loc=mu, scale=sigma)

                # Plot the PDF on top of the histogram
                ax2.plot(x, pdf, color=colors[i], linestyle='--', label=f'TAI-acc{i+1} fit')

            ax2.set_ylim([0, max(pdf)*2])
            ax2.set_ylabel('Probability Density', font_properties=font_prop)

            # Add legend and axis labels
            ax.legend()
            #ax.set_title(f"Error histogram for space {spaceID}")
            ax.set_xlabel(f'APE [%](Benchmark GLOD : {benchmark_glod})', font_properties=font_prop)
            ax.set_ylabel('Frequency', font_properties=font_prop)
            plt.xticks(fontproperties=font_prop)
            plt.yticks(fontproperties=font_prop)
            #plt.savefig(r"/scratch/nforouzandehsh/SA_optical-properties/varyingMCOA1.png")
            plt.show()
            
            #probability plot
            apes = []
            for key in self.results_dict.keys():
                apes.append(self.results_dict[key]['ape'])


            '''normality plot for the APEs for each MCOA''' # This is for each cell in the matrix. 
            
            #font
            
            plt.figure(dpi=300)

            # Create probability plot
            stats.probplot(apes, dist='norm', plot=plt)

            # Customize plot settings
            plt.xlabel('APE on the estimation of total annual illumination (TAI) [%]', font_properties=font_prop)
            plt.ylabel('Ordered Absolute Percentage Errors', font_properties=font_prop)


            # Change font of x and y ticks
            plt.xticks(fontproperties=font_prop)
            plt.yticks(fontproperties=font_prop)

            # Plt.title('Probability Plot')
            plt.grid(True)

            # Change markers to '+' and set color to red
            plt.gca().get_lines()[0].set_marker('x')
            plt.gca().get_lines()[0].set_color('grey')

            # Show the plot
            plt.show()      
            
            
        if analysis_type == 'rmse': 
            # Plot histograms of the data
            n1, bins1, patches1 = ax.hist(acc_level_1, bins=100, label=f'acc1[{len(acc_level_1)}]', alpha=0.5, color='red')
            n2, bins2, patches2 = ax.hist(acc_level_2, bins=100, label=f'acc2[{len(acc_level_2)}]', alpha=0.5, color='green')
            n3, bins3, patches3 = ax.hist(acc_level_3, bins=100, label=f'acc3[{len(acc_level_3)}]', alpha=0.5, color='orange')
            n4, bins4, patches4 = ax.hist(acc_level_4, bins=100, label=f'acc4[{len(acc_level_4)}]', alpha=0.5, color='brown')
            colors = ['red', 'green','orange','brown']

            # Fit distributions to the data and plot their PDFs
            ax2 = ax.twinx()  # create a single twinx axis for both PDFs
            for i, (acc_level, n, bins, patches) in enumerate(zip([acc_level_1, acc_level_2, acc_level_3,acc_level_4], [n1, n2,n3,n4], [bins1, bins2,bins3,bins4], [patches1, patches2,patches3,patches4])):
                # Fit a normal distribution to the data
                c, loc, scale = foldnorm.fit(acc_level)
                # Generate x values for plotting the PDF
                x = np.linspace(0, max(max(acc_level_1), max(acc_level_2), max(acc_level_3), max(acc_level_4)), 100)

                # Calculate the PDF of the fitted distribution at each x value
                pdf = foldnorm.pdf(x, c, loc=loc, scale=scale)

                # Plot the PDF on top of the histogram
                ax2.plot(x, pdf, color=colors[i], linestyle='--', label=f'acc{i+1} fit')

            # Set the same y-axis limit and label for both PDFs
            ax2.set_ylim([0, max(pdf)*2])
            ax2.set_ylabel('Probability Density')

            # Add legend and axis labels
            ax.legend()
            ax.set_title(f"space ID: {self.spaceID}")
            ax.set_xlabel(f'RMSE [lx](Benchmark glod : {benchmark_glod})')
            ax.set_ylabel('Frequency')

            # Show the plot
            plt.show()  
            return   
    def glod_influence(self, outputdir:str=None):
        '''Effects of GLOD on daylight results 
        '''
        files = os.listdir(self.path)
        mcoa0 = []
        for filename in files:
            filename_info = filename.split(sep="_")
            if filename_info[0] == self.spaceID and filename_info[2]==str(0):
                mcoa0.append(filename)

        #Calculate the mean for each glod(mcoa0) to acccount for randomness in the raytracing simulation
        mean_arrays = {} #contains the numpy arrays for each lod
        for i in range(5):
            glodN = [] #Contains the 8 result arrays in a certain glod
            for filename in mcoa0:
                filename_info = filename.split(sep="_")
                if filename_info[1] == str(i): #If the glod is i and the mcoa is 0
                    glodN.append(nullified_array(np.array(pd.read_csv(os.path.join(self.path,filename)))))
            #Create the average numpy array resutls:
            mean_array = np.mean(glodN,axis=0)
            mean_arrays[i] = mean_array

        #Calculate RMSE-grid for each glod
        rmse_arrays = {}
        mpe_arrays = {}
        for glod in mean_arrays.keys():
            rmse_array = np.sqrt(np.mean((mean_arrays[glod] - mean_arrays[4]) ** 2))
            non_zero_indices = np.nonzero(mean_arrays[4])
            mpe_array = 100*np.mean((mean_arrays[glod][non_zero_indices] - mean_arrays[4][non_zero_indices]) / mean_arrays[4][non_zero_indices])
            mpe_arrays[glod] = round(mpe_array,2)
            rmse_arrays[glod] = round(rmse_array,2)
        return mpe_arrays, rmse_arrays
    def TAI_varying_glod(self):
        average_tais = {}
        files = os.listdir(self.path) #All the result files
        for filename in files:
            for glod in range(5):
                if filename.split(sep="_")[0] == self.spaceID and filename.split(sep="_")[1] == str(glod) and filename.split(sep="_")[2] == str(0):
                    array = np.array(pd.read_csv(os.path.join(self.path,filename)))
                    array = nullified_array(array)
                    tai = TAI(array)
                    average_tais[glod] = tai
        return average_tais
                
            
        
    def rmse_total_varying_mcoa(self, save_fig:bool=False):
        '''Calculates the total rmse for each mcoa for each glod
        errors dict: dict with rmse values in lux
        errors_mpe dict: dict with mpe values in percentages'''
        benchmark_mcoa = 0
        mcoas=[0.05, 0.10,0.15,0.20]
        errors = {"mcoas": mcoas}
        errors_percentage = {"mcoas": mcoas}
        for glod in range(5):
            errors[f"glod{glod}"] = []
            errors_percentage[f"glod{glod}"] = []
            for mcoa in mcoas:
                #Benchmark
                for key in self.results_dict.keys():
                    if self.results_dict[key]['mcoa'] == str(benchmark_mcoa) and self.results_dict[key]['glod'] == str(glod) and self.results_dict[key]['space'] == self.spaceID:
                        bm_address = os.path.join(self.path,f"{key}.csv.gz")
                        bm = np.array(pd.read_csv(bm_address))
                        bm = nullified_array(bm)
                        
                #Each glod 
                same_glod = []
                for key in self.results_dict.keys():
                    if self.results_dict[key]['mcoa'] == str(mcoa) and self.results_dict[key]['glod'] == str(glod) and self.results_dict[key]['space'] == self.spaceID:
                        same_glod.append(key)
                same_glod_rmse = []
                same_glod_percentage = []
                for key in same_glod:
                    array1 = np.array(pd.read_csv(os.path.join(self.path,f"{key}.csv.gz")))
                    array1 = nullified_array(array1)
                    rmse = np.sqrt(np.mean((array1 - bm) ** 2))
                    rmse_percentage = round(100 * rmse / 1000 * TAI(bm),5) #TAI in klux.hour/year
                    same_glod_rmse.append(rmse)
                    same_glod_percentage.append(rmse_percentage)
                
                errors[f"glod{glod}"].append(np.mean(same_glod_rmse))
                errors_percentage[f"glod{glod}"].append(np.mean(rmse_percentage))
        
        # Create a new figure with desired DPI
        font_path = 'referencesFiles/times.ttf'  # Replace with the actual path to the font file
        font_prop = fm.FontProperties(fname=font_path, size=12)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.figure(dpi=200)

        # Plotting the lines
        plt.plot(errors["mcoas"], errors["glod0"], label='GLOD0')
        plt.plot(errors["mcoas"], errors["glod1"], label='GLOD1')
        plt.plot(errors["mcoas"], errors["glod2"], label='GLOD2')
        plt.plot(errors["mcoas"], errors["glod3"], label='GLOD3')
        plt.plot(errors["mcoas"], errors["glod4"], label='GLOD4')

        # Adding labels and title
        plt.xlabel(f'MCOA - Space: {self.spaceID}', fontproperties=font_prop)
        plt.ylabel('Uncertainty in illuminance calculation (RMSE) [lux]', fontproperties=font_prop)
        plt.grid(True)

        # Set the desired x ticks
        plt.xticks(errors["mcoas"],font_properties=font_prop)
        plt.yticks(font_properties=font_prop)
        # Adding legend
        legend = plt.legend()
        for text in legend.get_texts():
            text.set_fontproperties(font_prop)
        # Displaying and saving the plot
         
        if save_fig:
            plt.savefig(rf'varyingMCOA_{self.spaceID}_2.png', dpi=200, format='png', bbox_inches='tight')
        else:
            plt.show()
        return errors, errors_percentage
 
            
    def plot_UDI(self, points_path:str, glod:int=4):
        path = points_path #path to the points txt file (X Y Z Vx Vy Vz)
        res = self.path
        ress = os.listdir(res)
        for i in ress:
            if i.split("_")[0] == self.spaceID and i.split("_")[1] == str(glod) and i.split("_")[2] == "0":
                res = os.path.join(res, i)
                break
            
        font_path = self.font_path
        X = []
        Y = []
        Z = udi(nullified_array(np.array(pd.read_csv(res))))[1]

        prop = fm.FontProperties(fname=font_path)
        with open (path, 'r') as f:
            for line in f:
                line = line.strip()
                columns = line.split()
                X.append(float(columns[0]))
                Y.append(float(columns[1]))
                
        import matplotlib.pyplot as plt

        # Set the figure size and DPI
        fig = plt.figure(figsize=(6, 6), dpi=300)
        scatter = plt.scatter(X, Y, c=Z, cmap='plasma', marker='.')
        plt.gca().set_aspect('equal')
        plt.axis('off')
        colorbar = plt.colorbar(scatter,shrink=0.5,boundaries=np.linspace(0, 100, 256))
        colorbar.ax.set_xticklabels(colorbar.ax.get_xticks(), fontproperties=prop)
        colorbar.ax.set_yticklabels(np.array([0,10,20,30,40,50,60,70,80,90]), fontproperties=prop)

        colorbar.set_label('UDI [%]', fontproperties=prop, fontsize=12)

        plt.show()            
    def plot_TAI(self, points_path:str):
        path = points_path #path to the points txt file (X Y Z Vx Vy Vz)
        res = self.path
        ress = os.listdir(res)
        for i in ress:
            if i.split("_")[0] == self.spaceID and i.split("_")[1] == "4" and i.split("_")[2] == "0":
                res = os.path.join(res, i)
                break
            
        font_path = self.font_path
        X = []
        Y = []
        Z = np.mean(nullified_array(np.array(pd.read_csv(res))), axis=0).tolist()
        

        prop = fm.FontProperties(fname=font_path)
        with open (path, 'r') as f:
            for line in f:
                line = line.strip()
                columns = line.split()
                X.append(float(columns[0]))
                Y.append(float(columns[1]))
                
        # Set the figure size and DPI
        fig = plt.figure(figsize=(6, 6), dpi=300)
        scatter = plt.scatter(X, Y, c=Z, cmap='plasma', marker='.')
        plt.gca().set_aspect('equal')
        plt.axis('off')
        cbarr = list(range(100,int(max(Z)),int((max(Z)-100)/9)))
        colorbar = plt.colorbar(scatter,shrink=0.5,boundaries=np.linspace(0, max(cbarr), 256))
        colorbar.ax.set_xticklabels(colorbar.ax.get_xticks(), fontproperties=prop)
        colorbar.ax.set_yticklabels(np.array(cbarr), fontproperties=prop)

        colorbar.set_label('TAI [klux.hour/year]', fontproperties=prop, fontsize=12)

        plt.show()            


def point_selector(points_path:str,output_dir:str = r"/scratch/nforouzandehsh/SA_optical-properties/plots and results", relative_subset_size:float=0.05):
    '''select a subset of points for Radiance convergence test
    Input: path to points.txt
    output: path to newly written points_RadianceConvergenceTest.txt'''
    if 0.0 <= relative_subset_size <= 1.0:
        with open(points_path, "r") as infile:
            lines = infile.readlines()
        percent_to_delete = (1 - relative_subset_size)*100
        num_to_delete = int(len(lines) * percent_to_delete / 100)
        # Delete random lines from the list of lines
        lines_to_delete = random.sample(range(len(lines)), num_to_delete)
        new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
        # Write the remaining lines to a new file
        with open(os.path.join(output_dir,f"points_RadianceConvergenceTest.txt_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"), "w") as outfile:
            outfile.writelines(new_lines)
        
    else:
        print("relative portion should be between 0.0 and 1.0")
        
    return os.path.join(output_dir,'points_RadianceConvergenceTest.txt')
def create_colormap_figure(points:str,res0:str, res1:str, size=(8, 6), dpi=300, legend_size=1.0):
    '''vizualises the rmse between two simulations of the same space given the point location and RMSE'''
    
    #preprocessing: points
    points_pd = pd.read_csv(points,sep = "\s+", names=["X","Y","Z","vX","vY","vZ"]).iloc[:,:-3]
    X = points_pd["X"].values
    Y = points_pd["Y"].values
    
    #preprocessing: results
    res0_data = np.array(pd.read_csv(res0))
    res1_data = np.array(pd.read_csv(res1))
    
    # rmse: time-series error on 8760 hours
    RMSE = np.sqrt(np.mean((res0_data - res1_data)**2,axis=0))
    # Create a figure with specified size and dpi
    fig, ax = plt.subplots(figsize=size, dpi=dpi)

    # Plot the points
    sc = ax.scatter(X, Y, c=RMSE, cmap=cm.hot,marker=".")

    # Add colorbar for the RMSE values
    cbar = plt.colorbar(sc, ax=ax, pad=0.02, fraction=legend_size)
    cbar.set_label('RMSE[lux]')

    # Set the aspect ratio to 'equal' if you want the x and y scales to be equal
    ax.set_aspect('equal')

    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Scatter Plot with RMSE Colormap')
    ax.set_aspect('equal')
    # Show the figure
    plt.show()
def create_colormap_figure_from_array(points:str,RMSE:np.ndarray, size=(8, 6), dpi=300, legend_size=1.0,legend_range=None):
    '''vizualises the mean RMSE for one glod, in only one mcoa'''
    #preprocessing: points
    points_pd = pd.read_csv(points,sep = "\s+", names=["X","Y","Z","vX","vY","vZ"]).iloc[:,:-3]
    X = points_pd["X"].values
    Y = points_pd["Y"].values
    
    # Create a figure with specified size and dpi
    fig, ax = plt.subplots(figsize=size, dpi=dpi)

    # Plot the points
    sc = ax.scatter(X, Y, c=RMSE, marker=".") #cmap=cm.hot,

    # Add colorbar for the RMSE values
    cbar = plt.colorbar(sc, ax=ax, pad=0.02, fraction=legend_size)
    cbar.set_label('RMSE[lux]')

    # Set the aspect ratio to 'equal' if you want the x and y scales to be equal
    ax.set_aspect('equal')

    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    #ax.set_title('Scatter Plot with RMSE Colormap')
    ax.set_aspect('equal')
    # Set legend range if specified
    if legend_range:
        sc.set_clim(vmin=0,vmax=legend_range)
    # Show the figure
    plt.show()

#Convergence experiment to determine the number of simulation
def fitness_calcualtor(input:list):
    loc, scale = norm.fit(input)
    histogram, bin_edges = np.histogram(input, bins=10, density=True)
    cdf = np.cumsum(histogram * np.diff(bin_edges))
    pdf = norm.cdf(bin_edges[1:], loc=loc, scale=scale) - norm.cdf(bin_edges[:-1], loc=loc, scale=scale)
    norm_ks_stat, norm_p_val = kstest(cdf, norm(loc=loc, scale=scale).cdf)

    # Calculate the error of the histogram using KS test
    shape, loc, scale = lognorm.fit(input)
    histogram, bin_edges = np.histogram(input, bins=10, density=True)
    cdf = np.cumsum(histogram * np.diff(bin_edges))
    pdf = lognorm.cdf(bin_edges[1:], shape, loc=loc, scale=scale) - lognorm.cdf(bin_edges[:-1], shape, loc=loc, scale=scale)
    lognorm_ks_stat, lognorm_p_val = kstest(cdf, lognorm(shape, loc=loc, scale=scale).cdf)

    # Fit a gamma distribution to the data
    shape, loc, scale = gamma.fit(input)

    # Calculate the error of the histogram using KS test
    cdf = np.cumsum(histogram * np.diff(bin_edges))
    pdf = gamma.cdf(bin_edges[1:], shape, loc=loc, scale=scale) - gamma.cdf(bin_edges[:-1], shape, loc=loc, scale=scale)
    gamma_ks_stat, gamma_p_val = kstest(cdf, gamma(shape, loc=loc, scale=scale).cdf)
    return norm_ks_stat
    # convergence[acc_class] = {"norm": {"ks_stat":norm_ks_stat, 
    #                                 "p_val":norm_p_val},
    #                         "lognorm": {"ks_stat":lognorm_ks_stat,
    #                                     "p_val":lognorm_p_val},
    #                         "gamma": {"ks_stat":gamma_ks_stat,
    #                                     "p_val":gamma_p_val}}
    #dict of convergences after adding one iteration
def fit_goodness(paths:list, ground_truth:str):
    """Calculate the goodness of the fit for the given paths and ground truth"""
   
    # Benchmark
    bm = TAI(np.asarray(pd.read_csv(ground_truth))) #the ground truth TAI
    
    # List of errors
    goodness = {}
    apis =[]
    for i in range(len(paths)):
        tai = TAI(np.asarray(pd.read_csv(paths[i])))
        api = 100*(bm - tai)/bm
        apis.append(api)
        
    # Calculate the goodness of the fit
    return fitness_calcualtor(apis)
def fit_goodness(results_folder:list = os.listdir("/scratch/nforouzandehsh/sim_res")):
    '''measures goodness of the fitted curve from the results folder(Kolmogorov-Smirnov test)'''
    
    results = os.listdir(results_folder)
    gt = [] #filenames with 
    acc_1 = []
    acc_2 = []
    for filename in results:
        if filename.endswith("csv.gz"):
            if filename.startswith("0_"):
                gt.append(os.path.join(results_folder,filename))
            if filename.startswith("0.1_"):
                acc_1.append(os.path.join(results_folder,filename))
            if filename.startswith("0.2_"):
                acc_2.append(os.path.join(results_folder,filename))
    
    ground_truth = TAI(np.asarray(pd.read_csv(gt[0]))) #the ground truth TAI
    error_acc1 = []
    error_acc2 = []
    for res in acc_1:
        tai = TAI(np.asarray(pd.read_csv(res)))
        api = 100*(ground_truth - tai)/ground_truth
        error_acc1.append(api)
    for res in acc_2:
        tai = TAI(np.asarray(pd.read_csv(res)))
        api = 100*(ground_truth - tai)/ground_truth
        error_acc2.append(api)
        
    res_sim = {"GT":ground_truth,
            "acc_1":error_acc1,
            "acc_2":error_acc2}


    convergence={}
    acc_classes = ["acc_1","acc_2"]
    for acc_class in acc_classes:
        if len(res_sim[acc_class])>10:
            # fit a pdf to the error 1 and error 2, find the discriptors of the pdf, and find convergence
            loc, scale = norm.fit(res_sim[acc_class])
            histogram, bin_edges = np.histogram(res_sim[acc_class], bins=10, density=True)
            cdf = np.cumsum(histogram * np.diff(bin_edges))
            pdf = norm.cdf(bin_edges[1:], loc=loc, scale=scale) - norm.cdf(bin_edges[:-1], loc=loc, scale=scale)
            norm_ks_stat, norm_p_val = kstest(cdf, norm(loc=loc, scale=scale).cdf)

            # Calculate the error of the histogram using KS test
            shape, loc, scale = lognorm.fit(res_sim[acc_class])
            histogram, bin_edges = np.histogram(res_sim[acc_class], bins=10, density=True)
            cdf = np.cumsum(histogram * np.diff(bin_edges))
            pdf = lognorm.cdf(bin_edges[1:], shape, loc=loc, scale=scale) - lognorm.cdf(bin_edges[:-1], shape, loc=loc, scale=scale)
            lognorm_ks_stat, lognorm_p_val = kstest(cdf, lognorm(shape, loc=loc, scale=scale).cdf)

            # Fit a gamma distribution to the data
            shape, loc, scale = gamma.fit(res_sim[acc_class])

            # Calculate the error of the histogram using KS test
            cdf = np.cumsum(histogram * np.diff(bin_edges))
            pdf = gamma.cdf(bin_edges[1:], shape, loc=loc, scale=scale) - gamma.cdf(bin_edges[:-1], shape, loc=loc, scale=scale)
            gamma_ks_stat, gamma_p_val = kstest(cdf, gamma(shape, loc=loc, scale=scale).cdf)
            convergence[acc_class] = {"norm": {"ks_stat":norm_ks_stat, 
                                            "p_val":norm_p_val},
                                    "lognorm": {"ks_stat":lognorm_ks_stat,
                                                "p_val":lognorm_p_val},
                                    "gamma": {"ks_stat":gamma_ks_stat,
                                                "p_val":gamma_p_val}}

        else:
            continue
    return convergence