if __name__ == "__main__":
    pass


import os
import trimesh
import pathlib
import numpy as np
from scipy.spatial.qhull import QhullError


def Thresholds(non_permanenet_objs, count = 10): # intended to define the thresholds for inclusion/exclusion of non-permanent objects as numpy array
    #Add non_permanent objects
    full_list = [] #list containing all the non permanent objects flattened
    values_of_interest = []
    bb_size_list = []
    non_perm_dict = {}
    #list the non_permanent dirs
    for i in non_permanenet_objs['dirs'].keys():
        #print(i)
        dir_list = [] #only path to the obj files in one directory
        directory_contents = os.listdir(i)
        # Print the absolute path of each item in the directory
        for item in directory_contents:
            abs_path = os.path.join(i, item)
            full_list.append(abs_path)
            dir_list.append(abs_path)
        for j in dir_list:
            #print(j)
            try:
                #print(j)
                mesh = trimesh.load(j)
                #print(os.path.basename(j))
                bb_size_list.append(mesh.bounding_box_oriented.area)
                values_of_interest.append(mesh.bounding_box_oriented.area)#Core of the inclusion/ exclusion
                OBB_size = mesh.bounding_box_oriented.area
            except QhullError:
                #print(f"QhullError creating mesh from {j}. Skipping...")
                continue
            except TypeError:
                #print(f"TypeError on {j}. Skipping...")
                continue
            except ValueError:
                #print(f"ValueError on {j}. Skipping...")
                continue
            object_Name = os.path.basename(j).split(".")[0]
            non_perm_dict.update({object_Name:{'attributes':{'transparency_type':'opaque',
                                                    'material' : non_permanenet_objs['dirs'][i],
                                                    'permanency': 'non-permanent',
                                                    'OBB_area': OBB_size},
                                                'file_address': j,
                                                'mesh': mesh}})
    min_value = min(values_of_interest)
    max_value = max(values_of_interest)
    thresholds = np.linspace(min_value,max_value,10)

    return thresholds, values_of_interest, non_perm_dict, bb_size_list #types: numpy, list

    #Add non_permanent objects
    full_list = [] #list containing all the non permanent objects flattened
    values_of_interest = []
    non_perm_dict = {}
    #list the non_permanent dirs
    for i in non_permanenet_objs['dirs'].keys():
        dir_list = []
        directory_contents = os.listdir(i)
        # Print the absolute path of each item in the directory
        for item in directory_contents:
            abs_path = os.path.join(i, item)
            full_list.append(abs_path)
            dir_list.append(abs_path)
        for j in dir_list:
            try:
                mesh = trimesh.load(j)
                if print:
                    print(mesh.bounding_box_oriented.area)
                values_of_interest.append(mesh.bounding_box_oriented.area)#Core of the inclusion/ exclusion
                OBB_size = mesh.bounding_box_oriented.area
            except QhullError:
                #print(f"QhullError creating mesh from {j}. Skipping...")
                continue
            except TypeError:
                #print(f"TypeError on {j}. Skipping...")
                continue
            except ValueError:
                #print(f"ValueError on {j}. Skipping...")
                continue
            object_Name = os.path.basename(j).split(".")[0]
            non_perm_dict.update({object_Name:{'attributes':{'transparency_type':'opaque',
                                                    'material' : non_permanenet_objs['dirs'][i],
                                                    'permanency': 'non-permanent',
                                                    'OBB_area': OBB_size},
                                                'file_address': j,
                                                'mesh': mesh}})
    min_value = min(values_of_interest)
    max_value = max(values_of_interest)
    thresholds = np.linspace(min_value,max_value,10)

    return thresholds, values_of_interest, non_perm_dict #types: numpy, list
def space_dict(permanent_objs_opaque, permanent_objs_transparent, non_perm_dict):
    space_dict = {} #contains all the objects in a space, their mesh, and material, and address 
    #Permanent objects
    for key in permanent_objs_opaque:
        object_Name = os.path.basename(key).split(".")[0]
        space_dict.update({object_Name:{'attributes':{'transparency_type':'opaque',
                                                'material': permanent_objs_opaque[key],
                                                'permanency': 'permanent'},
                                'file_address': key,
                                'mesh': trimesh.load(key)
                                
                                }})
    #Add window
    for key in permanent_objs_transparent:
        object_Name = os.path.basename(key).split(".")[0]
        space_dict.update({object_Name:{'attributes':{'transparency_type':'transparent',
                                                'material' : permanent_objs_transparent[key],
                                                'permanency': 'permanent'},
                                'file_address': key,
                                'mesh': trimesh.load(key)}})
    # Add nonpermanent
    space_dict.update(non_perm_dict)
    return space_dict
def trn_ref_cnstraint(val:float): #puts 0-1 constaint on input reflectance/transmittance
    return 1 if val >= 1 else 0.03 if val <= 0.03 else val    


# S10_dir = r"C:\\Users\\Administrator\\source\\repos\\FormalizedLoD\\data\\Inputs\\S10
def dirTest():
    S10_dir = r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10"
    os.path.exists(S10_dir)
    print("it exists:" + str(os.path.exists(S10_dir)))


class DB_s10:
    def __init__(self, Mat_acc_level:float):
        self.Mat_acc_level = Mat_acc_level
        '''Input station for BG.West.550
        all paths are absolute on Windows Dir'''
        # Adress book
        #simulation folder
        epw_file = r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/weatherfiles/SGP_SG_Paya.Lebar.AB.486940_TMYx.epw"
        reinsrc_cal_file = r"C:/DAYSIM/lib/reinsrc.cal"
        reinhart_cal_file = r"C:/DAYSIM/lib/reinhart.cal"
        grid_points_txt = r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/points.txt"
        
        rand_mat = np.random.normal(0,Mat_acc_level,(1,11)).tolist()[0] #11 is more than or equal to the number of paths
        permanent_objs_transparent = {r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_window_glazing.obj": {'R':trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0])}}
        permanent_objs_opaque = {
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_ceiling.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0]),'roughness': 0.1,'specularity': 0.05},
            #r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_door.obj": {'R': trn_ref_cnstraint(0.48+rand_mat[1]),'G':trn_ref_cnstraint(0.48+rand_mat[1]),'B': trn_ref_cnstraint(0.48+rand_mat[1]),'roughness': 0.2,'specularity': 0.05},
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_floor.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[2]),'G':trn_ref_cnstraint(0.75+rand_mat[2]),'B': trn_ref_cnstraint(0.75+rand_mat[2]),'roughness': 0.1,'specularity': 0.05},
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_window_mullions.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[4]),'G':trn_ref_cnstraint(0.75+rand_mat[4]),'B': trn_ref_cnstraint(0.75+rand_mat[4]),'roughness': 0.1,'specularity': 0.05},
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_window_wallThickness.obj": {'R': trn_ref_cnstraint(0.5+rand_mat[4]),'G':trn_ref_cnstraint(0.5+rand_mat[4]),'B': trn_ref_cnstraint(0.5+rand_mat[4]),'roughness': 0.1,'specularity': 0.05},
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_walls.obj": {'R': trn_ref_cnstraint(0.3+rand_mat[5]),'G': trn_ref_cnstraint(0.3+rand_mat[5]),'B': trn_ref_cnstraint(0.3+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/perm_sill.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[6]),'G':trn_ref_cnstraint(0.75+rand_mat[6]),'B': trn_ref_cnstraint(0.75+rand_mat[6]),'roughness': 0.1,'specularity': 0.05}}
        non_permanenet_objs = { "dirs":{#key: semantics, value: Parent directory containing all the non-permanent instances as .obj files. 
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_chair':{'R': trn_ref_cnstraint(0.04+rand_mat[7]),'G':trn_ref_cnstraint(0.04+rand_mat[7]),'B': trn_ref_cnstraint(0.04+rand_mat[7]),'roughness': 0.2,'specularity': 0.15},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_closet':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_else':{'R': trn_ref_cnstraint(0.50+rand_mat[9]),'G':trn_ref_cnstraint(0.50+rand_mat[9]),'B': trn_ref_cnstraint(0.50+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_box':{'R': trn_ref_cnstraint(0.04+rand_mat[7]),'G':trn_ref_cnstraint(0.04+rand_mat[7]),'B': trn_ref_cnstraint(0.04+rand_mat[7]),'roughness': 0.2,'specularity': 0.15},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_desk':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_sofa':{'R': trn_ref_cnstraint(0.20+rand_mat[9]),'G':trn_ref_cnstraint(0.20+rand_mat[9]),'B': trn_ref_cnstraint(0.20+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_monitor':{'R': trn_ref_cnstraint(0.04+rand_mat[7]),'G':trn_ref_cnstraint(0.04+rand_mat[7]),'B': trn_ref_cnstraint(0.04+rand_mat[7]),'roughness': 0.2,'specularity': 0.15},
            # r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/radiator':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_table':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            #r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_desklamp':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_fan':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_lighting':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_shelf':{'R': trn_ref_cnstraint(0.50+rand_mat[9]),'G':trn_ref_cnstraint(0.50+rand_mat[9]),'B': trn_ref_cnstraint(0.50+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'C:/Users/Administrator/source/repos/FormalizedLoD/data/Inputs/S10/furn_vase':{'R': trn_ref_cnstraint(0.50+rand_mat[10]),'G':trn_ref_cnstraint(0.50+rand_mat[10]),'B': trn_ref_cnstraint(0.50+rand_mat[10]),'roughness': 0.1,'specularity': 0.02}},
            'obj_path_list': {
                }}


        # Read the folders with multiple objs
        for key in non_permanenet_objs["dirs"]:
            dir = pathlib.Path(key) #Parent directory
            non_permanenet_objs["obj_path_list"][key] = list(dir.iterdir()) #Iterdir() produces a generator
        thresholds, values_of_interest, non_perm_dict, bb_size_list = Thresholds(non_permanenet_objs, count = 10)
        
        
        #basic space info
        self.glod4 = space_dict(permanent_objs_opaque, permanent_objs_transparent, non_perm_dict)
        self.epw_file = epw_file
        self.reinsrc_cal_file = reinsrc_cal_file
        self.reinhart_cal_file = reinhart_cal_file
        self.bb_size_list = bb_size_list
        self.grid_points_txt = grid_points_txt
    def GLOD4(self):
        GLOD4 = self.glod4.copy()
        return GLOD4
    def GLOD3(self):
        #GLOD 3 : permanent + non_permanent larger than 75th percentile = 3.07 m2 [OBB area]
        GLOD3 = self.glod4.copy() #initialization
        GLOD3_non_permanent_object_keys = []
        for key in GLOD3.keys():
            if GLOD3[key]['attributes']['permanency'] == 'permanent':
                pass
            if GLOD3[key]['attributes']['permanency'] == 'non-permanent' and GLOD3[key]['attributes']['OBB_area'] <= 0.55:
                GLOD3_non_permanent_object_keys.append(key)

        for i in GLOD3_non_permanent_object_keys:
            GLOD3.pop(i)
            
        print(f"GLOD3: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD2 is {len(GLOD3.keys())}")
        return GLOD3
    def GLOD2(self):
        GLOD2 = self.glod4.copy() #initialization
        #GLOD 2 : permanent + non_permanent larger than 75th percentile = 3.07 m2 [OBB area]
        GLOD2_non_permanent_object_keys = []
        for key in GLOD2.keys():
            if GLOD2[key]['attributes']['permanency'] == 'permanent':
                pass
            if GLOD2[key]['attributes']['permanency'] == 'non-permanent' and GLOD2[key]['attributes']['OBB_area'] <= 2.41:
                GLOD2_non_permanent_object_keys.append(key)

        for i in GLOD2_non_permanent_object_keys:
            GLOD2.pop(i)
            
        print(f"GLOD2: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD2 is {len(GLOD2.keys())}")
        return GLOD2
    def GLOD0(self):
        #GLOD 0 : only the permanent objects
        GLOD0 = self.glod4.copy() #initialization
        GLOD0_non_permanent_object_keys = []
        for key in GLOD0.keys():
            if GLOD0[key]['attributes']['permanency'] == 'permanent':
                pass
            if GLOD0[key]['attributes']['permanency'] == 'non-permanent':
                GLOD0_non_permanent_object_keys.append(key)

        for i in GLOD0_non_permanent_object_keys:
            GLOD0.pop(i)
        print(f"GLOD0: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD0 is {len(GLOD0.keys())}")  
        return GLOD0
    def GLOD1(self):
        GLOD1 = self.glod4.copy() #initialization
        GLOD1_non_permanent_object_keys = []
        for key in GLOD1.keys():
            if GLOD1[key]['attributes']['permanency'] == 'permanent':
                pass
            if GLOD1[key]['attributes']['permanency'] == 'non-permanent' and GLOD1[key]['attributes']['OBB_area'] <= 3.07:
                GLOD1_non_permanent_object_keys.append(key)

        for i in GLOD1_non_permanent_object_keys:
            GLOD1.pop(i)
        
        
        print(f"GLOD1: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD1 is {len(GLOD1.keys())}") 
        return GLOD1
