if __name__ == "__main__":
    pass

import os
import trimesh
import pathlib
import numpy as np
from scipy.spatial import QhullError

class Thresholds:
    def __init__(self, permanent_objs_transparent, non_permanenet_objs, count = 10):
        self.permanent_objs_transparent = permanent_objs_transparent
        self.non_permanenet_objs = non_permanenet_objs
        self.count = count
        #Add non_permanent objects
        full_list = [] #list containing all the non permanent objects flattened
        values_of_interest = []
        bb_size_list = []
        non_perm_dict = {}
        #list the non_permanent dirs
        # glazing triangles for solid angle calculation
        # empty numpy array to store the triangles
        window_triangles_list = []
        window_mesh_list = []
        window_id = 0
        for i in permanent_objs_transparent.keys():
            print(f"window id is {window_id}")
            window_id+=1
            try:
                mesh = trimesh.load(i)
                window_mesh_list.append(mesh)
                #print("window triangle shape:", mesh.triangles.shape)
                # add mesh triangles to list
                window_triangles_list.append(mesh.triangles)
            except ValueError:
                #print(f"ValueError on {i}. Skipping...")
                continue
        print(f"there are {len(window_mesh_list)} window meshes")
        # Concatenate all window triangles in the list into a single numpy array
        window_triangles = np.concatenate(window_triangles_list, axis=0)
        print (f"there are {len(window_triangles)} window triangles")
        
        for i in non_permanenet_objs['dirs'].keys(): # each category of non-permanent objects
            #print(i)
            dir_list = [] #only path to the obj files in one directory
            directory_contents = os.listdir(i)
            # Print the absolute path of each item in the directory
            for item in directory_contents:
                abs_path = os.path.join(i, item)
                full_list.append(abs_path)
                dir_list.append(abs_path)
            for j in dir_list: # j is the path to the .obj instance file
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
                    #print(f"ValueError on {j}. Skipping...") -- 
                    continue
                
                # calculate solid angle 
                '''Calculate the clumulative solid angle subtended by the mesh triangles from the point.
                    IT DOES NOT ACCOUNT FOR OCCULSIONS BY OTHER OBJECTS!!!!! how to resolve that? 
                    Parameters:
                    triangles (numpy.
                    .....ndarray): Array of triangles, shape (n, 3, 3)
                    point (numpy.ndarray): Observation point, shape (3,)
                    
                    Returns:
                    float: Solid angle in steradians '''
                total_solid_angle = 0.0
                triangle_id = 0
                for tri in window_triangles:
                    #print("'is visible' is", str(self.is_visible(window_triangle_center, j)), "for triangle id",str(triangle_id), str(tri.mean(axis=0)))
                    triangle_id+=1
                    #if self.is_visible(window_triangle_center, j):
                        #print(str(j) + " is visible" + "from winow" + str(tri.mean(axis=0)))
                    if 1==1: # ignore visibility for now
                    
                        a, b, c = tri - mesh.centroid
                        norm = np.linalg.norm(np.cross(b - a, c - a))
                        volume = np.dot(np.cross(b - a, c - a), np.array([0.0, 0.0, 0.0]) - a) / 6.0 
                        angle = 2 * np.arctan2(volume, np.dot(a, b) * np.linalg.norm(c) + 
                                                    np.dot(b, c) * np.linalg.norm(a) + 
                                                    np.dot(c, a) * np.linalg.norm(b))
                        total_solid_angle += abs(angle)
                    #else:
                        #print(str(j) + " is NOT visible" + "from winow" + str(tri.mean(axis=0)))
                        
                solid_angle = np.abs(total_solid_angle)
                
                object_Name = os.path.basename(j).split(".")[0]
                non_perm_dict.update({object_Name:{'attributes':{'transparency_type':'opaque',
                                                        'material' : non_permanenet_objs['dirs'][i],
                                                        'permanency': 'non-permanent',
                                                        'OBB_area': OBB_size,
                                                        'solid_angle': solid_angle},
                                                    'file_address': j,
                                                    'mesh': mesh}})
        self.min_value = min(values_of_interest)
        self.max_value = max(values_of_interest)
        self.thresholds = np.linspace(self.min_value,self.max_value,10)
        self.values_of_interest = values_of_interest
        self.bb_size_list = bb_size_list
        self.non_perm_dict = non_perm_dict
        return None
        #return thresholds, values_of_interest, non_perm_dict, bb_size_list #types: numpy, list 
    
    def is_visible(self, window_triangle_center, furn_path): # implement as is_visible(tri.mean(), j)
        '''
        visibility criteria. 
        returns False if ray from object mesh centroid to window triangle center intersects with any other non_perm_object
        
        parameters:
        window_triangle_center: numpy.ndarray
        furn_path: str, path to the .obj file of the object. 
        
        returns: boolean
        '''
        intersections = []
        for i in self.non_permanenet_objs['dirs'].keys(): # each category of non-permanent objects
            dir_list = [] #only path to the obj files in one directory
            directory_contents = os.listdir(i)
            # Print the absolute path of each item in the directory
            for item in directory_contents:
                abs_path = os.path.join(i, item)
                dir_list.append(abs_path)
            for j in dir_list: # j is the path to the .obj instance file
                if furn_path != j: # for all "other" objects:
                    try:
                        mesh = trimesh.load(j)
                        intersections.append(mesh.ray.intersects_location(ray_origins=[mesh.centroid], ray_directions=[window_triangle_center - mesh.centroid]))
                        if len(intersections) != 0:
                            return(not bool(len(intersections)))
                    except QhullError:
                        #print(f"QhullError creating mesh from {j}. Skipping...")
                        continue
                    except TypeError:
                        #print(f"TypeError on {j}. Skipping...")
                        continue
                    except ValueError:
                        #print(f"ValueError on {j}. Skipping...") -- 
                        continue
            else:
                print("Same object")
                
        
        return(not bool(len(intersections))) # if no intersections, means that window is visible. 
        
            
    
    
    
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





def WindowTriangleVisible(triangles: np.ndarray, point: np.ndarray) -> float:
    """
    Is the 'center of a the triangle' visible from the 'centroid of the furniture'?
    
    Inputs: space_dict, point ###(remember to exclude the furniture itself)
    """
    

class DB_s08:
    def __init__(self, Mat_acc_level:float, cubic_grid = False):
        self.Mat_acc_level = Mat_acc_level
        '''Input station for DA200'''
        # Adress book
        #simulation folder
        epw_file = r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/weatherfiles/CAN_ON_Toronto.City.715080_CWEC2016.epw"
        reinsrc_cal_file = r"/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/lib/reinsrc.cal"
        reinhart_cal_file = r"/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/lib/reinhart.cal"
        
        if cubic_grid: # this does not seem to be a good idea for point definition. 
            grid_points_txt = r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/points_cubic_spaceAngle0.txt"
        else:
            grid_points_txt = r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/points.txt"
        
        rand_mat = np.random.normal(0,Mat_acc_level,(1,11)).tolist()[0] #11 is more than or equal to the number of paths
        permanent_objs_transparent = {r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_roomabove_glass.obj": {'R':trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0])},
                                    r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_windows_glass.obj": {'R':trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0])},}
        
        permanent_objs_opaque = {
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_ceiling_white.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_roomabove_ceiling.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[0]),'G':trn_ref_cnstraint(0.75+rand_mat[0]),'B': trn_ref_cnstraint(0.75+rand_mat[0]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_doors.obj": {'R': trn_ref_cnstraint(0.48+rand_mat[1]),'G':trn_ref_cnstraint(0.48+rand_mat[1]),'B': trn_ref_cnstraint(0.48+rand_mat[1]),'roughness': 0.2,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_floor.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[2]),'G':trn_ref_cnstraint(0.75+rand_mat[2]),'B': trn_ref_cnstraint(0.75+rand_mat[2]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_walls_plaster_beige.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[3]),'G':trn_ref_cnstraint(0.75+rand_mat[3]),'B': trn_ref_cnstraint(0.75+rand_mat[3]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Perm_trim.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[4]),'G':trn_ref_cnstraint(0.75+rand_mat[4]),'B': trn_ref_cnstraint(0.75+rand_mat[4]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_window_trims.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[4]),'G':trn_ref_cnstraint(0.75+rand_mat[4]),'B': trn_ref_cnstraint(0.75+rand_mat[4]),'roughness': 0.1,'specularity': 0.05},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_walls_white.obj": {'R': trn_ref_cnstraint(0.9+rand_mat[5]),'G': trn_ref_cnstraint(0.9+rand_mat[5]),'B': trn_ref_cnstraint(0.9+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_mullions.obj": {'R': trn_ref_cnstraint(0.3+rand_mat[5]),'G': trn_ref_cnstraint(0.3+rand_mat[5]),'B': trn_ref_cnstraint(0.3+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_walls_brick.obj": {'R': trn_ref_cnstraint(0.3+rand_mat[5]),'G': trn_ref_cnstraint(0.3+rand_mat[5]),'B': trn_ref_cnstraint(0.3+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_windows_lintels_sides.obj":{'R': trn_ref_cnstraint(0.3+rand_mat[5]),'G': trn_ref_cnstraint(0.3+rand_mat[5]),'B': trn_ref_cnstraint(0.3+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_windows_blinds.obj": {'R': trn_ref_cnstraint(0.3+rand_mat[5]),'G': trn_ref_cnstraint(0.3+rand_mat[5]),'B': trn_ref_cnstraint(0.3+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_roomabove_wals.obj": {'R': trn_ref_cnstraint(0.9+rand_mat[5]),'G': trn_ref_cnstraint(0.9+rand_mat[5]),'B': trn_ref_cnstraint(0.9+rand_mat[5]),'roughness': 0.3,'specularity': 0.0},
            r"/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/perm_wooden_beams.obj": {'R': trn_ref_cnstraint(0.75+rand_mat[6]),'G':trn_ref_cnstraint(0.75+rand_mat[6]),'B': trn_ref_cnstraint(0.75+rand_mat[6]),'roughness': 0.1,'specularity': 0.05}}
        
        non_permanenet_objs = { "dirs":{#key: semantics, value: Parent directory containing all the non-permanent instances as .obj files. 
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_chairs':{'R': trn_ref_cnstraint(0.04+rand_mat[7]),'G':trn_ref_cnstraint(0.04+rand_mat[7]),'B': trn_ref_cnstraint(0.04+rand_mat[7]),'roughness': 0.2,'specularity': 0.15},
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_desk':{'R': trn_ref_cnstraint(0.85+rand_mat[8]),'G':trn_ref_cnstraint(0.85+rand_mat[8]),'B': trn_ref_cnstraint(0.85+rand_mat[8]),'roughness': 0.1,'specularity': 0.02},
            #r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_else':{'R': trn_ref_cnstraint(0.50+rand_mat[9]),'G':trn_ref_cnstraint(0.50+rand_mat[9]),'B': trn_ref_cnstraint(0.50+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_AC_UNIT':{'R': trn_ref_cnstraint(0.50+rand_mat[9]),'G':trn_ref_cnstraint(0.50+rand_mat[9]),'B': trn_ref_cnstraint(0.50+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_electricbox':{'R': trn_ref_cnstraint(0.50+rand_mat[9]),'G':trn_ref_cnstraint(0.50+rand_mat[9]),'B': trn_ref_cnstraint(0.50+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_screen':{'R': trn_ref_cnstraint(0.09+rand_mat[9]),'G':trn_ref_cnstraint(0.09+rand_mat[9]),'B': trn_ref_cnstraint(0.09+rand_mat[9]),'roughness': 0.1,'specularity': 0.02},
            r'/scratch/nforouzandehsh/DelftBlueFiles/Inputs/S08/Furn_FnCoil':{'R': trn_ref_cnstraint(0.50+rand_mat[10]),'G':trn_ref_cnstraint(0.50+rand_mat[10]),'B': trn_ref_cnstraint(0.50+rand_mat[10]),'roughness': 0.1,'specularity': 0.02}},
            'obj_path_list': {
                }}
        
        # Read the folders with multiple objs
        for key in non_permanenet_objs["dirs"]:
            dir = pathlib.Path(key) #Parent directory
            non_permanenet_objs["obj_path_list"][key] = list(dir.iterdir()) #Iterdir() produces a generator
        print("there are " + str(len(non_permanenet_objs["obj_path_list"].keys())) + " directories with non-permanent objects")
        
        thresh = Thresholds(permanent_objs_transparent,non_permanenet_objs, count = 10)
        # thresholds, values_of_interest, non_perm_dict, bb_size_list = Thresholds(permanent_objs_transparent,non_permanenet_objs, count = 10)
        min_value = thresh.min_value
        values_of_interest = thresh.values_of_interest
        non_perm_dict = thresh.non_perm_dict
        bb_size_list = thresh.bb_size_list

        
        
        
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
