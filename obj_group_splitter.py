'''ASSUMPTIONS
faces listed under each group name use only the vertices declared under the same group
each vertex has only one normal thus the vertIDs and vertexnomalIDs for one vertex are always equal'''

import argparse
import os
import uuid

#Userinput
parser = argparse.ArgumentParser(description='Splits an input .obj file into its groups, and save each one in a separate obj file\n This program does not support .obj objects')
parser.add_argument("obj_file",metavar='obj_file', type=str,help="Input splittable(by group) obj file")
parser.add_argument("-o", "--output_direcotory", help="Output directory where each group will be saved as a single .obj . ")
args = parser.parse_args()

# Get the input file name and directory
input_file_name = os.path.basename(args.obj_file)[:-4]# Input file name
directory = os.path.dirname(os.path.abspath(args.obj_file))# Base directory
tmp_file_name = os.path.basename(args.obj_file)[:-4]+'_tmp.obj' # Input file name
# Get the output directory
if args.output_direcotory:
    output_dir = os.path.abspath(args.output_direcotory)
else:
    output_dir = os.path.join(directory, input_file_name)
    # create the directory 
    os.makedirs(output_dir, exist_ok=True)

print(f"Output directory: {output_dir}")

input_obj = args.obj_file
with open(input_obj, 'r') as f:
    lines = f.readlines()

#initialization
current_group_name = None
Vertex_index_local = 0
Vertex_normal_index_local = 0
Vertex_texture_index_local = 0
Vertex_index_global = 0
Vertex_normal_index_global = 0
Vertex_texture_index_global = 0

def face_global2local(face_line): #Takes a face_line in original obj, returns localized face content
    face = []
    for i in (face_line.split(" ")[1:]):
        #split
        v_global = int(i.split("/")[0]) if i.split("/")[0] != '' else ''
        vt_global = int(i.split("/")[1]) if i.split("/")[1] != '' else ''
        vn_global = int(i.split("/")[2]) if i.split("/")[2] != '' else ''
        
        #find local
        v_local = vertex_dict[v_global]['Vertex_index_local'] if v_global != '' else '' # I want this vertex dict to be valid accross all of the functions in a class, how can I do that? Define it as class variable using "self"!
        vt_local = vertex_dict[v_global]['Vertex_index_local'] if vt_global != '' else ''
        vn_local = vertex_dict[v_global]['Vertex_index_local'] if vn_global != '' else ''
        
        #merge
        face.append("/".join([str(v_local), str(vt_local), str(vn_local)]))

    face_replacement = " ".join(face) #replacemenet for the line in the localized obj
    return 'f ' + face_replacement

'''Create the Vertex dict'''
vertex_dict = {}
for line in lines:
    #tmp.write(line.strip())
    if line.strip().split(sep=" ")[0] == "g":
        #reset the local indices
        Vertex_index_local = 0 
        Vertex_normal_index_local = 0
        Vertex_texture_index_local = 0
        Id = str(uuid.uuid4())
        current_group_name = "_".join(line.strip().split(sep=" ")[1:])+"_ID_"+Id.replace("-","_")


    elif line.strip().split(sep=" ")[0] == "v":
        Vertex_index_local += 1
        Vertex_index_global += 1
        vertex_dict.update({Vertex_index_global:{ # Make this for each vertex 
        "Vertex_index_local": Vertex_index_local,
        #"Vertex_normal_index_local": None,
        #"Vertex_texture_index_local": None,
        "group_name": current_group_name,
        "x": line.strip().split(sep=" ")[1],
        "y": line.strip().split(sep=" ")[2],
        "z": line.strip().split(sep=" ")[3],
        "nx": None,
        "ny": None,
        "nz": None,
        "tx": None,
        "ty": None,
        "tz": None,
        }})

    elif line.strip().split(sep=" ")[0] == "vn":
        Vertex_normal_index_local += 1
        Vertex_normal_index_global += 1 # equivalent of the vertex index, assuming each vertex has only one normal assigned to it
        vertex_dict[Vertex_normal_index_global]["nx"] = line.strip().split(sep=" ")[1]
        vertex_dict[Vertex_normal_index_global]["ny"] = line.strip().split(sep=" ")[2]
        vertex_dict[Vertex_normal_index_global]["nz"] = line.strip().split(sep=" ")[3]

    elif line.strip().split(sep=" ")[0] == "vt":
        try:   
            Vertex_texture_index_local += 1
            Vertex_texture_index_global += 1 # equivalent of the vertex index
            vertex_dict[Vertex_texture_index_global]["tx"] = line.strip().split(sep=" ")[1]
            vertex_dict[Vertex_texture_index_global]["ty"] = line.strip().split(sep=" ")[2]
            vertex_dict[Vertex_texture_index_global]["tz"] = line.strip().split(sep=" ")[3]
        except:
            print("Error with texture Info")
            pass

#Replace global face verts to local in the tmp file
with open(os.path.join(directory,tmp_file_name), 'w') as tmp:
    # Write some data to the file
    for line in lines:
        if line.strip().split(sep=" ")[0] == "f":
            tmp.write(face_global2local(line.strip())+'\n') #Localized face
        elif line.startswith('#') or line.startswith(' ') or line.startswith('\t') or line.startswith('\n'): #delete the first lines before the first group
            pass
        elif line.startswith('g'):
            Id = str(uuid.uuid4())
            group_name =  "_".join(line.strip().split(sep=" ")[1:])+"_ID_"+Id.replace("-","_")
            tmp.write(f"g {group_name}\n")
        else:
            tmp.write(line.strip()+'\n')

###############
# Split the tmp file and save groups separately
with open(os.path.join(directory,tmp_file_name), 'r') as input_file:
    # Initialize the slice counter
    slice_number = 1
    # Initialize the current slice
    current_slice = []
    groupnames = []
    for line in input_file:
        if line.startswith('g'):
            groupnames.append("_".join(line.strip().split(sep=" ")[1:]))
        else:
            pass

with open(os.path.join(directory,tmp_file_name), 'r') as input_file:
    if groupnames:
        groupname = groupnames[0]
        # Loop over each line in the input file
        for line in input_file:
            # Check if the line starts with "g"
            if line.startswith('g'):
                # If the current slice is not empty, write it to a file
                if current_slice:
                    with open(f'{directory}/{input_file_name}/{input_file_name}_{slice_number:03}_{groupname}.obj', 'w') as output_file:
                        output_file.writelines(current_slice)
                    groupname = "_".join(line.strip().split(sep=" ")[1:])
                    # Increment the slice counter
                    slice_number += 1
                # Start a new slice
                current_slice = [line]
            elif line.startswith('#') or line.startswith(' ') or line.startswith('\t') or line.startswith('\n'):
                pass
                # Append the line to the current slice
            else:
                current_slice.append(line)
        # Write the last slice to a file
        if current_slice:
            with open(f'{directory}/{input_file_name}/{input_file_name}_{slice_number:03}_{groupname}.obj', 'w') as output_file:
                output_file.writelines(current_slice)

        os.remove(os.path.join(directory, tmp_file_name))

    else:
        print('ERROR: no group in the obj')