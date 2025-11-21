if __name__ == "__main__":
    pass

import os
import trimesh
import numpy as np
import pathlib
from scipy.spatial import QhullError
import plotly.graph_objects as go
import shutil


solid_angle_thresholds = [0.02,0.035,1]
solid_angle_thresholds = [0.005, 0.007, 1] # this is for normalized solid angle over window area.  affects [GLOD2, GLOD3, GLOD4]
class Thresholds:
    """
    Thresholds(permanent_objs_transparent, non_permanenet_objs, window_count, verbose=False, quality_representaion='actual')
    Summary:
    1. Initializes a Thresholds object that loads window meshes and non-permanent object meshes, 
    2. Computes per-object cumulative solid angles subtended by window triangles as seen from each object's centroid, and 
    3. Records per-object SA (Solid Angle) values.
    4. The computed SAs are stored both in absolute steradians and normalized by total window area. 
            The normalized solid angle (NSA) for an object is defined as:
            \begin{equation}
                \mathrm{NSA} = \frac{\Omega}{A_w}
            \end{equation}
            where $\Omega$ is the total solid angle subtended by the object from all window triangles (in steradians),
            and $A_w$ is the total window area (in m²). NSA enables comparison across spaces with different window sizes.

            Here, $\Omega$ is computed as the sum of solid angles subtended by the object from all window triangles 
            that are not obstructed by other objects (i.e., only considering lines of sight that are not blocked).
    """
    
    def __init__(self,
                 permanent_objs_transparent: dict,
                 non_permanenet_objs: dict,
                 window_count:int,
                 verbose:bool = False,
                 quality_representaion:str = 'actual'):
        self.permanent_objs_transparent = permanent_objs_transparent
        self.non_permanenet_objs = non_permanenet_objs
        self.window_count = window_count 
        self.solid_angles = [] # this is to study the frequency of solid angles in a room
        self.total_window_area = 0.0 
        full_list = [] #l ist containing all the non permanent objects flattened.
        # values_of_interest = [] # list containing the values of interest for defining LoDs.
        non_perm_dict = {} 
        window_triangles_list = []
        window_mesh_list = []
        window_id = 0
        
        for i in permanent_objs_transparent.keys():
            if verbose:
                print(f"window id is {window_id}")
            window_id+=1
            try:
                mesh = trimesh.load(open(i, 'rb'), file_type='obj')
                window_mesh_list.append(mesh)
                window_triangles_list.append(mesh.triangles)
                self.total_window_area += mesh.area
                
            except ValueError:
                continue
        print(f"total window area is {self.total_window_area}")
        if verbose:
            print(f"there are {len(window_mesh_list)} window meshes")
        # Concatenate all window triangles in the list into a single numpy array
        window_triangles = np.concatenate(window_triangles_list, axis=0)
        if verbose:
            print (f"there are {len(window_triangles)} window triangles")            
        for i in non_permanenet_objs['dirs'].keys(): # each semantic.
            old_i = i
            if i.endswith('_obb'):
                i = i[:-4]
                
            dir_list = [] 
            directory_contents = os.listdir(i)
            for item in directory_contents: 
                abs_path = os.path.join(i,item)
                full_list.append(abs_path)
                dir_list.append(abs_path)
            for j in dir_list: 
                centroid_ = trimesh.load(open(j, 'rb'), file_type='obj').centroid
                try:
                    with open(j, 'rb') as f:
                        mesh = trimesh.load(f, file_type='obj')
                    
                except QhullError:
                    continue
                except TypeError:
                    continue
                except ValueError:
                    continue
                
                # Calculate solid angle
                '''
                Calculates the cumulative solid angle subtended by the mesh triangles from the point.                    
                    Parameters:
                    triangles (numpy.ndarray): Array of triangles, shape (n, 3, 3)
                    point (numpy.ndarray): Observation point, shape (3,)
                    Returns:
                    float: Solid angle in steradians.
                '''
                total_solid_angle = 0.0
                for tri in window_triangles:
                    if verbose: print(f"tri is {tri}")
                    window_triangle_center = tri.mean(axis=0)
                    if verbose: print(f"window_triangle_center is {window_triangle_center}")
                    if 1:
                        if verbose: print(str(j) + " is visible" + "from winow" + str(tri.mean(axis=0)))
                        a, b, c = tri - centroid_
                        norm = np.linalg.norm(np.cross(b - a, c - a))
                        volume = np.dot(np.cross(b - a, c - a), np.array([0.0, 0.0, 0.0]) - a) / 6.0 
                        angle = 2 * np.arctan2(volume, np.dot(a, b) * np.linalg.norm(c) + 
                                                    np.dot(b, c) * np.linalg.norm(a) + 
                                                    np.dot(c, a) * np.linalg.norm(b))
                        total_solid_angle += abs(angle)
                self.solid_angles.append(np.abs(total_solid_angle))
                
                object_Name = os.path.basename(j).split(".")[0]
                obj_path = os.path.join(old_i, object_Name + ".obj")
                with open(obj_path, 'rb') as f:
                    mesh = trimesh.load(f, file_type='obj')
                non_perm_dict.update({object_Name:
                    {'attributes':{'transparency_type':'opaque',
                                                        'material' : non_permanenet_objs['dirs'][old_i],
                                                        'permanency': 'non-permanent',
                                                        # 'OBB_area': OBB_size,
                                                        'solid_angle': np.abs(total_solid_angle)/self.total_window_area},
                                                        'file_address': os.path.join(old_i,object_Name + ".obj"),
                                                        'mesh':mesh,
                                                        }
                                      }
                                     )
        self.non_perm_dict = non_perm_dict
    def __is_visible(self, window_triangle_center, furn_path): 
        '''
        visibility criteria. 
        returns False if ray from object mesh centroid to window triangle center intersects with any other non_perm_object.
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
                        with open(j, 'rb') as f:
                            mesh = trimesh.load(f, file_type='obj')
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
    for key in permanent_objs_opaque.keys():
        object_Name = os.path.basename(key).split(".")[0]
        space_dict.update({object_Name:{'attributes':{'transparency_type':'opaque',
                                                'material': permanent_objs_opaque[key],
                                                'permanency': 'permanent'},
                                'file_address': key,
                                'mesh': trimesh.load(open(key, 'rb'), file_type='obj')
                                }})
    #Add window
    object_Name = os.path.basename(key).split(".")[0]
    with open(key, 'rb') as f:
        mesh = trimesh.load(f, file_type='obj')
    for key in permanent_objs_transparent.keys():
        object_Name = os.path.basename(key).split(".")[0]
        space_dict.update({object_Name:{'attributes':{'transparency_type':'transparent',
                                                'material' : permanent_objs_transparent[key],
                                                'permanency': 'permanent'},
                                'file_address': key,
                                'mesh': mesh}})
    # Add nonpermanent
    space_dict.update(non_perm_dict)
    return space_dict

class DB_W01050: #s06
    def __init__(self,quality_representaion:str = 'actual'):
        self.window_count = 1
        if quality_representaion not in ['actual','oriented bounding box']:
            raise ValueError("quality_representaion should be one of ['actual','oriented bounding box'")
        epw_file = r"/home/nforouzandehsh/RQ1/inputs/weather_files/NLD_ZH_Rotterdam.The.Hague.AP.063440_TMYx.epw"
        permanent_objs_transparent = {r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_window_glazing.obj": {'R':0.75,'G':0.75,'B': 0.75}}
        permanent_objs_opaque = {
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_ceiling.obj": {'R':0.9,'G':0.9,'B': 0.9, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_door.obj": {'R':0.7,'G':0.7,'B': 0.7, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_floor.obj": {'R':0.4,'G':0.4,'B': 0.4, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_lighting_fixtures.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_plinth.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_walls.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/Perm_window_sill.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},}
        non_permanenet_objs = { "dirs":{ #key: semantics, value: Parent directory containing all the non-permanent instances as .obj files. 
            r'/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/chairs':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/table':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/wall_painting':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/flipBoard':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},},
            'obj_path_list': {
            }}
        
        # make the OBB file/folders
        if quality_representaion == 'oriented bounding box':
            original_dirs = list(non_permanenet_objs["dirs"].items())  # (key, value) pairs

            updated_dirs = {}

            for key, value in original_dirs:
                dir = pathlib.Path(key)
                new_dir = dir.parent / (dir.name + "_obb")
                new_dir.mkdir(exist_ok=True)


                for obj_path in dir.iterdir():
                    if obj_path.suffix == '.obj':
                        mesh = trimesh.load(open(obj_path, 'rb'), file_type='obj')                    
                        obb_mesh = mesh.bounding_box_oriented
                        obj_str = obb_mesh.export(file_type='obj')
                        group_name = obj_path.stem
                        obj_str = f"g {group_name}\n" + obj_str
                        out_path = new_dir / obj_path.name
                        with open(out_path, 'w') as f:
                            f.write(obj_str)
                        # obb_mesh.export(new_dir / obj_path.name)

                updated_dirs[str(new_dir)] = value  # use the original value

            # Replace the entire dirs dict at once
            non_permanenet_objs["dirs"] = updated_dirs  
        
            
        # make obj_path_list
        for key in non_permanenet_objs["dirs"]:
            dir = pathlib.Path(key)
            non_permanenet_objs["obj_path_list"][key] = list(dir.iterdir()) #Iterdir() produces a generator
        
             
        thresh = Thresholds(permanent_objs_transparent,
                            non_permanenet_objs,
                            window_count = self.window_count,
                            quality_representaion=quality_representaion)
        non_perm_dict = thresh.non_perm_dict
        self.glod4 = space_dict(permanent_objs_opaque, permanent_objs_transparent, non_perm_dict)
        # save the glod4 dict to a json file

        self.epw_file = epw_file
    def LoD4(self):
        GLOD4 = self.glod4.copy()
        return GLOD4
    def LoD3(self): 
        LoD3 = self.glod4.copy() 
        LoD3_non_permanent_object_keys = []
        for key in LoD3.keys():
            if LoD3[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD3[key]['attributes']['permanency'] == 'non-permanent' and LoD3[key]['attributes']['solid_angle'] <= solid_angle_thresholds[0]: # remove
                LoD3_non_permanent_object_keys.append(key)
        for i in LoD3_non_permanent_object_keys:
            LoD3.pop(i)
        print(f"LoD: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD2 is {len(LoD3.keys())}")
        return LoD3
    def LoD2(self): 
        LoD2 = self.glod4.copy() 
        LoD2_non_permanent_object_keys = []
        for key in LoD2.keys():
            if LoD2[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD2[key]['attributes']['permanency'] == 'non-permanent' and LoD2[key]['attributes']['solid_angle'] <= solid_angle_thresholds[1]: # remove
                LoD2_non_permanent_object_keys.append(key)
        for i in LoD2_non_permanent_object_keys:
            LoD2.pop(i)
            
        print(f"LoD1: size of the original dict:{len(self.glod4.keys())}, and size of the LoD2 is {len(LoD2.keys())}")
        return LoD2
    def LoD1(self):
        LoD1 = self.glod4.copy()
        LoD1_non_permanent_object_keys = []
        for key in LoD1.keys():
            if LoD1[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD1[key]['attributes']['permanency'] == 'non-permanent' and LoD1[key]['attributes']['solid_angle'] <= solid_angle_thresholds[2]: # remove
                LoD1_non_permanent_object_keys.append(key)
        for i in LoD1_non_permanent_object_keys:
            LoD1.pop(i)
        print(f"LoD1: size of the original dict:{len(self.glod4.keys())}, and size of the LoD1 is {len(LoD1.keys())}")
        return LoD1
class DB_W550: 
    def __init__(self,quality_representaion:str = 'actual'):
        self.window_count = 10 # number of windows in the room
        if quality_representaion not in ['actual','oriented bounding box']:
            raise ValueError("quality_representaion should be one of ['actual','oriented bounding box'")
        # simulation folder
        epw_file = r"/home/nforouzandehsh/RQ1/inputs/weather_files/NLD_ZH_Rotterdam.The.Hague.AP.063440_TMYx.epw"
        permanent_objs_transparent = {r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_window_glazing.obj": {'R':0.75,'G':0.75,'B': 0.75}}
        permanent_objs_opaque = {
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_ceiling.obj": {'R':0.9,'G':0.9,'B': 0.9, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_door.obj": {'R':0.7,'G':0.7,'B': 0.7, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_floor.obj": {'R':0.4,'G':0.4,'B': 0.4, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_lighting_fixtures.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_windows_sill.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_windows_profile.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_wall.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},
            r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/Permanent_window_wallDepth.obj": {'R':0.75,'G':0.75,'B': 0.75, 'roughness': 0,'specularity': 0},}
        non_permanenet_objs = { "dirs":{ #key: semantics, value: Parent directory containing all the non-permanent instances as .obj files. 
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/chair':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/tables':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/else':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/monitor':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/case_boxes':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/closet':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/flowerbox':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/radiator':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/shelf':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            r'/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/sofa':{'R':0.2,'G':0.2,'B': 0.2,  'roughness': 0,'specularity': 0},
            },'obj_path_list': {}}
        
        # make the OBB file/folders
        if quality_representaion == 'oriented bounding box':
            original_dirs = list(non_permanenet_objs["dirs"].items())  # (key, value) pairs

            updated_dirs = {}

            for key, value in original_dirs:
                dir = pathlib.Path(key)
                new_dir = dir.parent / (dir.name + "_obb")
                new_dir.mkdir(exist_ok=True)


                for obj_path in dir.iterdir():
                    if obj_path.suffix == '.obj':
                        mesh = trimesh.load(open(obj_path, 'rb'), file_type='obj')                    
                        obb_mesh = mesh.bounding_box_oriented
                        obj_str = obb_mesh.export(file_type='obj')
                        group_name = obj_path.stem
                        obj_str = f"g {group_name}\n" + obj_str
                        out_path = new_dir / obj_path.name
                        with open(out_path, 'w') as f:
                            f.write(obj_str)
                        # obb_mesh.export(new_dir / obj_path.name)

                updated_dirs[str(new_dir)] = value  # use the original value

            # Replace the entire dirs dict at once
            non_permanenet_objs["dirs"] = updated_dirs  
        
            
        # make obj_path_list
        for key in non_permanenet_objs["dirs"]:
            dir = pathlib.Path(key)
            non_permanenet_objs["obj_path_list"][key] = list(dir.iterdir()) #Iterdir() produces a generator
        
             
        thresh = Thresholds(permanent_objs_transparent,
                            non_permanenet_objs,
                            window_count = self.window_count,
                            quality_representaion=quality_representaion)
        non_perm_dict = thresh.non_perm_dict
        self.glod4 = space_dict(permanent_objs_opaque, permanent_objs_transparent, non_perm_dict)
        # save the glod4 dict to a json file

        self.epw_file = epw_file
    def LoD4(self):
        GLOD4 = self.glod4.copy()
        return GLOD4
    def LoD3(self): # solid angle >
        LoD3 = self.glod4.copy() #initialization
        LoD3_non_permanent_object_keys = []
        for key in LoD3.keys():
            if LoD3[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD3[key]['attributes']['permanency'] == 'non-permanent' and LoD3[key]['attributes']['solid_angle'] <= solid_angle_thresholds[0]: # remove
                LoD3_non_permanent_object_keys.append(key)
        for i in LoD3_non_permanent_object_keys:
            LoD3.pop(i)
        print(f"LoD: size of the original dict:{len(self.glod4.keys())}, and size of the GLOD2 is {len(LoD3.keys())}")
        return LoD3
    def LoD2(self): # solid angle >
        LoD2 = self.glod4.copy() #initialization
        LoD2_non_permanent_object_keys = []
        for key in LoD2.keys():
            if LoD2[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD2[key]['attributes']['permanency'] == 'non-permanent' and LoD2[key]['attributes']['solid_angle'] <= solid_angle_thresholds[1]: # remove
                LoD2_non_permanent_object_keys.append(key)
        for i in LoD2_non_permanent_object_keys:
            LoD2.pop(i)
            
        print(f"LoD1: size of the original dict:{len(self.glod4.keys())}, and size of the LoD2 is {len(LoD2.keys())}")
        return LoD2
    def LoD1(self): # solid angle >
        LoD1 = self.glod4.copy() #initialization
        LoD1_non_permanent_object_keys = []
        for key in LoD1.keys():
            if LoD1[key]['attributes']['permanency'] == 'permanent':
                pass
            if LoD1[key]['attributes']['permanency'] == 'non-permanent' and LoD1[key]['attributes']['solid_angle'] <= solid_angle_thresholds[2]: # remove
                LoD1_non_permanent_object_keys.append(key)
        for i in LoD1_non_permanent_object_keys:
            LoD1.pop(i)
        print(f"LoD1: size of the original dict:{len(self.glod4.keys())}, and size of the LoD1 is {len(LoD1.keys())}")
        return LoD1

def extract_solid_angles(lod_dict):
    """
    Extracts solid angle values from a LoD dictionary.
    
    Parameters:
    - lod_dict (dict): Dictionary returned from e.g., DB_W550().LoD4()

    Returns:
    - List[float]: List of solid angle values for non-permanent objects.
    """
    solid_angles = []
    for obj in lod_dict.values():
        if obj["attributes"]["permanency"] == "non-permanent":
            solid_angles.append(obj["attributes"].get("solid_angle", 0.0))  # default to 0.0 if missing
    return solid_angles
def show_model(model: dict, camera: tuple = None, pdf_name: str = None):
    fig = go.Figure()
    for key in model.keys():
        obj = model[key]
        mesh = obj['mesh']
        attrs = obj['attributes']
        color = 'darkgrey' if attrs['permanency'] == 'non-permanent' else (
            'lightgrey' if attrs['transparency_type'] == 'opaque' else 'lightblue'
        )
        # if not opaque, render with wireframe
        if attrs['transparency_type'] != 'opaque':
            fig.add_trace(go.Mesh3d(
                x=mesh.vertices[:, 0], y=mesh.vertices[:, 1], z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0], j=mesh.faces[:, 1], k=mesh.faces[:, 2],
                opacity=0.5, color=color, flatshading=True
            ))
        fig.add_trace(go.Mesh3d(
            x=mesh.vertices[:, 0], y=mesh.vertices[:, 1], z=mesh.vertices[:, 2],
            i=mesh.faces[:, 0], j=mesh.faces[:, 1], k=mesh.faces[:, 2],
            opacity=0.5, color=color
        ))
    
    if not camera:# then let plotly decide the camera
        # Scene and layout updates, set size to 500x500
        fig.update_layout(
            width=500, height=400,
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, visible=False),
                yaxis=dict(showticklabels=False, showgrid=False, visible=False),
                zaxis=dict(showticklabels=False, showgrid=False, visible=False),
                camera=dict(projection=dict(type="orthographic")) 
            ),
            margin=dict(l=0, r=0, b=0, t=0)
        )
    else:
        # Scene and layout updates, set size to 500x500
        fig.update_layout(
            width=500, height=400,
            scene=dict(
                xaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False,
                        #    range=[min_bounds[0], max_bounds[0]]
                        ),
                yaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False,
                        #    range=[min_bounds[1], max_bounds[1]]
                        ),
                zaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False,
                        #    range=[min_bounds[2], max_bounds[2]]
                        ),
                # aspectmode='data',
                camera=dict(up=dict(x=0, y=0, z=1),
                            eye=dict(x=camera[0], 
                                    y=camera[1], 
                                    z=camera[2]), 
                            center=dict(x=camera[3], 
                                        y=camera[4]-0.4, 
                                        z=camera[5]-0.5), 
                            projection=dict(type="orthographic"))),
            margin=dict(l=0, r=0, b=0, t=0))
        
    if pdf_name:
        fig.write_image(f"{pdf_name}.pdf", scale = 3)
    else:
        fig.show()
    return fig
def show_solid_angles(model: dict, 
                      camera: tuple = None, 
                      pdf_name: str = None):
    fig = go.Figure()
    solid_angles = []

    # -------- First pass: gather solid angles --------
    for key, obj in model.items():
        attrs = obj['attributes']
        if attrs.get('permanency') == 'non-permanent' and 'solid_angle' in attrs:
            solid_angles.append(attrs['solid_angle'])

    # Fixed scale for legend
    cmin, cmax = 0.0, 0.01

    # We'll show the colorbar only on the first non-permanent trace
    show_scale_once = True

    # -------- Second pass: add geometry --------
    for key, obj in model.items():
        mesh = obj['mesh']
        attrs = obj['attributes']

        is_non_perm = attrs.get('permanency') == 'non-permanent'
        is_opaque = attrs.get('transparency_type') == 'opaque'

        if is_non_perm:
            val = float(attrs.get('solid_angle', 0.0))
            # uniform intensity per object (repeat per-vertex)
            intensity = np.full(mesh.vertices.shape[0], val, dtype=float)

            fig.add_trace(go.Mesh3d(
                x=mesh.vertices[:, 0], y=mesh.vertices[:, 1], z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0], j=mesh.faces[:, 1], k=mesh.faces[:, 2],
                opacity=0.7 if not is_opaque else 0.95,
                flatshading=True,
                intensity=intensity,
                colorscale='Viridis',
                cmin=cmin, cmax=cmax,
                showscale=show_scale_once,  # show the legend once
                colorbar=dict(
                    title=dict(
                        text='NSA [sr/m2]',
                        font=dict(family="Times New Roman", size=14)
                    ),
                    tickfont=dict(family="Times New Roman", size=12),
                ) if show_scale_once else None
            ))
            show_scale_once = False

        else:
            # permanent objects keep fixed colors
            color = 'lightgrey' if is_opaque else 'lightblue'
            fig.add_trace(go.Mesh3d(
                x=mesh.vertices[:, 0], y=mesh.vertices[:, 1], z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0], j=mesh.faces[:, 1], k=mesh.faces[:, 2],
                opacity=0.95 if is_opaque else 0.5,
                color=color,
                flatshading=True
            ))

    # -------- Layout / camera --------
    layout_kwargs = dict(
        width=500, height=400,
        font=dict(family="Times New Roman", size=12),
        margin=dict(l=0, r=0, b=0, t=0)
    )

    if not camera:  # let Plotly decide the camera
        print("No camera provided, using default view.")
        layout_kwargs["scene"] = dict(
            xaxis=dict(showticklabels=False, showgrid=False, visible=False),
            yaxis=dict(showticklabels=False, showgrid=False, visible=False),
            zaxis=dict(showticklabels=False, showgrid=False, visible=False),
            camera=dict(projection=dict(type="orthographic"))
        )
        
        
    else:
        layout_kwargs["scene"] = dict(
            xaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False),
            yaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False),
            zaxis=dict(showticklabels=False, showgrid=False, showbackground=False, title_text='', zeroline=False, visible=False, showspikes=False),
            camera=dict(
                up=dict(x=0, y=0, z=1),
                eye=dict(x=camera[0], y=camera[1], z=camera[2]),
                center=dict(x=camera[3], y=camera[4]-0.4, z=camera[5]-0.5),
                projection=dict(type="orthographic")
            )
        )

    fig.update_layout(**layout_kwargs)

    if pdf_name:
        fig.write_image(f"{pdf_name}.pdf", scale=3)
    else:
        fig.show()

    return fig, solid_angles



