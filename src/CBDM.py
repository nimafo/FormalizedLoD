if __name__ == "__main__":
    pass


# Dependencies
import numpy as np
# import trimesh
# from scipy.spatial.qhull import QhullError
import uuid
import os
import shutil
import subprocess
import datetime
import cv2
import matplotlib.pyplot as plt

class DDS: # to be tested.
    '''
    E = CdcS - CdcdSd + CsunSsun
            CdcS : Cds is daylight cofficient S is sky                          -> {self.results_DDS_dc}annualR.ill
          CdcdSd : Cdcd is direct-sky coefficients and Sd is direct-sky matrix. -> {self.results_DDS_dcd}annualR.ill
        CsunSsun : Csun is direct-sun coefficients and Ssun sun matrix          -> {self.results_dcDDS_cds}annualR.ill
    '''
    def __init__(self,
                 to_simulate:dict,
                 epw_file:str,
                 grid_points_txt:str,
                 base_dir:str,
                 rad_params:str='-ad 2048 -as 1024 -aa 0.5 -ar 1024 -ab 6',
                 wea_:str=None,
                 direcory_cleanup:bool=True,
                 simulation_run_name:str=None,
                 verbose:bool=False):
        self.to_simulate = to_simulate
        self.epw_file = epw_file
        self.grid_points_txt = grid_points_txt
        self.base_dir = base_dir
        self.rad_params = rad_params
        self.wea_ = wea_
        self.direcory_cleanup = direcory_cleanup
        self.verbose = verbose
        self.simulation_run_name = simulation_run_name
        #-- 
        if simulation_run_name is None:
            self.simulation_run_name = str(datetime.datetime.now()).replace(" ", "_").replace("-", "").replace(":", "_").replace(".", "_")+f"_{str(uuid.uuid1())}"
        self.base_folder = rf'{self.base_dir}/{self.simulation_run_name}/'
        print("Len to_simulate: "+str(len(self.to_simulate))) if verbose else None
        
        self.Base_folder,self.object_folder,self.skydomes_folder, self.octrees_folder,self.matrices_folder,self.dc_folder,self.dcd_folder,self.assets_folder,self.skyvectors_folder,self.results_folder,self.results_dcDDS,self.results_DDS_dc,self.results_DDS_dcd,self.skies_folder,self.matrices_cds_folder,self.results_dcDDS_cds = self.__make_folders()
        self.__write_objs()
        self.__write_materials()
        self.__write_room()

        shutil.copy2(self.grid_points_txt, os.path.join(self.Base_folder, "points.txt"))
        with open(self.grid_points_txt, 'r') as file:
            self.sensor_points_count = 0
            for line in file:
                if line.strip():  # check if line is not empty
                    self.sensor_points_count += 1

        # Write skyglow.rad
        reinhart_subdivisions = 2
        skydome = f'''#@rfluxmtx u=+Y h=u\nvoid glow groundglow\n0\n0\n4 1 1 1 0\n\ngroundglow source ground\n0\n0\n4 0 0 -1 180\n\n\n#@rfluxmtx u=+Y h=r{reinhart_subdivisions}\nvoid glow skyglow\n0\n0\n4 1 1 1 0\n\nskyglow source skydome\n0\n0\n4 0 0 1 180'''
        self.__to_rad(self.skydomes_folder, "skyglow", skydome)

        #make the material black
        MaterialBlack = '#Black material that will be used for 5 phase calculations and Descretized daylight simulation \nvoid plastic black \n0 \n0 \n5 0 0 0 0 0'
        self.__to_rad(self.Base_folder, "materialBlack", MaterialBlack)
        
        # Space separated string for the transparent surfaces to put it instead of Window.rad in oconv
        windows = '' # space separated string for the transparent surfaces and put it instead of Window.rad
        for key in self.to_simulate:
            if self.to_simulate[key]['attributes']['transparency_type'] == 'transparent':
                with open(self.to_simulate[key]['file_address'],'r') as obj_file:
                    for line in obj_file:
                        if line.startswith('g'): #assumes there is only one group in each input .obj
                            modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                windows+=("'"+self.object_folder+modifier_name+".rad"+"'")
                windows+=" "
        os.chdir(f'{self.Base_folder}')

        '''DDS -- STEP 1: Perform an annual daylight coefficient simulation > dcDDS/dc/annualR.ill'''
        result = subprocess.run(f"oconv '{self.Base_folder}materials.rad' '{self.Base_folder}room.rad' {windows} > '{self.octrees_folder}roomDC.oc'", shell=True ) 
        result = subprocess.run(f"rfluxmtx -I+ -y {self.sensor_points_count} {self.rad_params} -n 16 - {self.skydomes_folder}skyglow.rad -i {self.octrees_folder}roomDC.oc < {self.Base_folder}points.txt > {self.dc_folder}illum.mtx", shell=True)
        print(rf"rfluxmtx -I+ -y {self.sensor_points_count} {self.rad_params} -n 16 - {self.skydomes_folder}skyglow.rad -i {self.octrees_folder}roomDC.oc < {self.Base_folder}points.txt > {self.dc_folder}illum.mtx")
        
        epw_name = os.path.basename(self.epw_file)
        if wea_ == None:
            self.wea = f"{self.assets_folder}{epw_name[:-4]}.wea"
            try:
                result = subprocess.run(f'cp {epw_file} {self.assets_folder}', shell=True)
            except:
                raise
            result = subprocess.run(f'epw2wea {self.epw_file} {self.wea}', shell=True ,stdout = subprocess.PIPE) 
        else:
            wea = wea_

        result = subprocess.run(f'gendaymtx -m {reinhart_subdivisions} {self.wea} > {self.skyvectors_folder}{epw_name[:-4]}.smx', shell=True ,stdout = subprocess.PIPE)
        #results step 1
        result = subprocess.run(f'dctimestep {self.dc_folder}illum.mtx {self.skyvectors_folder}{epw_name[:-4]}.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {self.results_DDS_dc}annualR.ill', shell=True ,stdout = subprocess.PIPE)

        '''DDS -- STEP 2 : Perform an annual direct-only daylight coefficients simulation > dcd/annualR.ill'''
        #STEP 2: Perform an annual direct-only daylight coefficients simulation. 
        result = subprocess.run(f"oconv '{self.Base_folder}materialBlack.rad' '{self.Base_folder}materials.rad' '{self.Base_folder}roomBlack.rad' {windows} > '{self.octrees_folder}roomDCBlack.oct'", shell=True ,stdout = subprocess.PIPE)
        result = subprocess.run(f'rfluxmtx -I+ -y {self.sensor_points_count} {self.rad_params} -n 16 - {self.skydomes_folder}skyglow.rad -i {self.octrees_folder}roomDCBlack.oct < {self.Base_folder}points.txt > {self.dcd_folder}illum.mtx', shell=True)
        result = subprocess.run(f'gendaymtx -m {reinhart_subdivisions} {self.wea} > {self.skyvectors_folder}{epw_name[:-4]}_d.smx', shell=True ,stdout = subprocess.PIPE)
        result = subprocess.run(f'dctimestep {self.dcd_folder}illum.mtx {self.skyvectors_folder}{epw_name[:-4]}_d.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {self.results_DDS_dcd}annualR.ill', shell=True ,stdout = subprocess.PIPE)
        
        '''STEP 3 -- Perform an annual sun-coefficients simulation.> dcDDS/cds/annualR.ill'''
        result = subprocess.run(f"echo 'void light solar 0 0 3 1e6 1e6 1e6' > {self.skies_folder}suns.rad" , shell=True ,stdout = subprocess.PIPE)
        cmd= f"cnt 5165 | rcalc -e MF:{reinhart_subdivisions} -f reinsrc.cal" + " -e Rbin=recno -o 'solar source sun 0 0 4 ${Dx} ${Dy} ${Dz} 0.533'"
        self.__to_rad(self.skies_folder,'suns',os.popen(cmd).read())
        result = subprocess.run(f'oconv -f {self.Base_folder}materialBlack.rad {self.skies_folder}suns.rad {self.Base_folder}materials.rad {self.Base_folder}roomBlack.rad {windows} > {self.octrees_folder}sunCoefficientsDDS.oct' , 
                                shell=True ,
                                stdout = subprocess.PIPE)
        result = subprocess.run(f'rcontrib -I+  -y {self.sensor_points_count} -n 16 {self.rad_params} -dc 1 -dt 0 -dj 0 -faf -e MF:{reinhart_subdivisions} -f reinhart.cal -b rbin -bn Nrbins -m solar {self.octrees_folder}sunCoefficientsDDS.oct < {self.Base_folder}points.txt > {self.matrices_cds_folder}cdsDDS.mtx'  , 
                                shell=True ,
                                stdout = subprocess.PIPE)
        result = subprocess.run(f'gendaymtx -5 0.533 -d -m {reinhart_subdivisions} {self.wea} > {self.skyvectors_folder}{epw_name[:-4]}sunM6.smx', 
                                shell=True ,
                                stdout = subprocess.PIPE)
        result = subprocess.run(f'dctimestep {self.matrices_cds_folder}cdsDDS.mtx {self.skyvectors_folder}{epw_name[:-4]}sunM6.smx | rmtxop -fa -t -c 47.4 119.9 11.6 - > {self.results_dcDDS_cds}annualR.ill', 
                                shell=True ,
                                stdout = subprocess.PIPE)

        '''Final step:Combine results '''
        ##Final Step: Combine results
        result = subprocess.run(f'rmtxop {self.results_DDS_dc}annualR.ill + -s -1 {self.results_DDS_dcd}annualR.ill + {self.results_dcDDS_cds}annualR.ill > {self.results_dcDDS}annualR.ill', 
                                shell=True,
                                stdout = subprocess.PIPE)

        '''postprocessing the annual.ill file'''
        with open(f'{self.results_dcDDS}annualR.ill', "r") as file:
            lines = file.readlines()
            lines = lines[13:]
        with open(f'{self.results_dcDDS}annualR_clean.ill', "w") as file:
            file.writelines(lines)
        data = np.genfromtxt(f'{self.results_dcDDS}annualR_clean.ill', delimiter=' ')
        self.data = data
        print(rf" Total Annual illuminance: {np.sum(data)}") if self.verbose else None
        if direcory_cleanup:
            shutil.rmtree(self.base_folder)
    def __make_folders(self):
        '''creates the folder structure for daylight simulation'''
        Base_folder = self.base_folder
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
    def __write_objs(self): 
        '''
        Write the objects to rad files
        '''
        for key in self.to_simulate:
            if self.verbose:
                print(key)
                print(self.to_simulate[key]['file_address'])
            with open(self.to_simulate[key]['file_address'],'r') as obj_file:
                for line in obj_file:
                    if line.startswith('g'): #assumes there is only one group in each input .obj
                        modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                cmd = rf"obj2rad '{self.to_simulate[key]['file_address']}' > '{os.path.join(self.object_folder,modifier_name+'.rad')}'"
                res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    print(f"Error in obj2rad command for {key}: {res.stderr.decode('utf-8')}")
                    raise Exception(f"Error in obj2rad command for {key}: {res.stderr.decode('utf-8')}")     
    def __write_materials(self):
        '''
        writes the materials to rad file'''
        string = ''
        for key in self.to_simulate:
            if self.to_simulate[key]['attributes']['transparency_type'] == 'opaque':
                #find modifiers name
                with open(self.to_simulate[key]['file_address'],'r') as obj_file:
                    for line in obj_file:
                        if line.startswith('g'): #assumes there is only one group in each input .obj
                            modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                            
                #create material string
                material_string_opaque = f"void plastic {modifier_name}\n0\n0\n5 "+\
                    f"{self.to_simulate[key]['attributes']['material']['R']} "+\
                    f"{self.to_simulate[key]['attributes']['material']['G']} "+\
                    f"{self.to_simulate[key]['attributes']['material']['B']} "+\
                    f"{self.to_simulate[key]['attributes']['material']['roughness'] if self.to_simulate[key]['attributes']['material']['roughness'] else 0} "+\
                    f"{self.to_simulate[key]['attributes']['material']['specularity'] if self.to_simulate[key]['attributes']['material']['specularity'] else 0}\n\n"
                    
                #print(material_string_opaque)
                string+=material_string_opaque
            elif self.to_simulate[key]['attributes']['transparency_type'] == 'transparent':
                with open(self.to_simulate[key]['file_address'],'r') as obj_file:
                    for line in obj_file:
                        if line.startswith('g'): #assumes there is only one group in each input .obj
                            modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                material_string_transparent = f"void glass {modifier_name}\n0\n0\n3 "+\
                    f"{self.to_simulate[key]['attributes']['material']['R']} "+\
                    f"{self.to_simulate[key]['attributes']['material']['G']} "+\
                    f"{self.to_simulate[key]['attributes']['material']['B']}\n\n"
                #print(material_string_transparent)
                string+=material_string_transparent

        outfile = open(os.path.join(self.Base_folder, 'materials.rad'), 'w')
        if string != '':
            outfile.write(string)
    def __write_room(self):
        '''write room'''
        room_rad = ""
        room_black_rad = ""
        for key in self.to_simulate:
            if self.to_simulate[key]['attributes']['transparency_type'] == 'opaque':
                #find modifiers name
                with open(self.to_simulate[key]['file_address'],'r') as obj_file:
                    for line in obj_file:
                        if line.startswith('g'): #assumes there is only one group in each input .obj
                            modifier_name = "_".join(line.strip().split(sep=" ")[1:])
                room_rad += "!xform ./objects/"+modifier_name+".rad\n"
                room_black_rad += "!xform -m black ./objects/"+modifier_name+".rad\n"
        print(room_rad)

        ##write to file
        outfile = open(os.path.join(self.Base_folder, 'room.rad'), 'w')
        if room_rad != '':
            outfile.write(room_rad)
        #outfile.close()
        outfile_black = open(os.path.join(self.Base_folder, 'roomBlack.rad'), 'w')
        if room_black_rad != '':
            outfile_black.write(room_black_rad)
        #outfile.close()
    def __to_rad(self, dir_name, base_filename, content): #.rad for a single surface
        outfile = open(os.path.join(dir_name, base_filename + '.' + 'rad'), 'a')
        outfile.write(content)
