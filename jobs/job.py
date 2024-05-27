

# load the space
import sys
sys.path.append('/scratch/nforouzandehsh/FormalizedLoD')
from input_station import DB_s08 # input_station is in the parent directory of jobs --> it should be imported like the following: 
import plotly.graph_objects as go
import numpy as np
import time


print("starting time: ", time.ctime())

space = DB_s08(0).GLOD4()

maximum_solid_angle = 0
for key in space.keys():
    if space[key]['attributes']['permanency'] == 'non-permanent' and space[key]['attributes']['solid_angle'] > maximum_solid_angle:
        maximum_solid_angle = space[key]['attributes']['solid_angle']
print ("maximum solid angle is ", str(maximum_solid_angle))
windows = space["perm_windows_glass"]["mesh"]


# Function to create plotly mesh
def create_mesh(triangles, color):
    x, y, z = triangles[:, :, 0].flatten(), triangles[:, :, 1].flatten(), triangles[:, :, 2].flatten()
    I = np.arange(0, len(x), 3)
    J = np.arange(1, len(x), 3)
    K = np.arange(2, len(x), 3)
    mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=I,
        j=J,
        k=K,
        color=color,
        opacity=0.50
    )
    return mesh

windows_trace = create_mesh(windows.triangles, 'green')
data_to_plot = [windows_trace]
# Create traces for object_mesh and windows
for key in space.keys():
    if space[key]['attributes']['permanency'] == 'non-permanent':
        red_intensity = int((space[key]['attributes']['solid_angle'] / maximum_solid_angle) * 255)
        color = f'rgb({red_intensity},0,0)'  # Shades of red
        data_to_plot.append(create_mesh(space[key]['mesh'].triangles, color))

# find the bounding box of the space/ perm objects
min_x,max_x,min_y, max_y, min_z, max_z = 0,0,0,0,0,0
for key in space.keys():
    if space[key]['attributes']['permanency'] == 'permanent':
        # adjust the bounding box
        min_x = min(min_x, np.min(space[key]['mesh'].vertices[:,0]))
        max_x = max(max_x, np.max(space[key]['mesh'].vertices[:,0]))
        min_y = min(min_y, np.min(space[key]['mesh'].vertices[:,1]))
        max_y = max(max_y, np.max(space[key]['mesh'].vertices[:,1]))
        min_z = min(min_z, np.min(space[key]['mesh'].vertices[:,2]))
        max_z = max(max_z, np.max(space[key]['mesh'].vertices[:,2]))
print(min_x,max_x,min_y, max_y, min_z, max_z)

fig = go.Figure(data=data_to_plot)

# Update layout for better visualization
fig.update_layout(
    scene=dict(
        xaxis=dict(
            nticks=0, showticklabels=False, showgrid=False, zeroline=False, showline=False, range=[min_x, max_x]
        ),
        yaxis=dict(
            nticks=0, showticklabels=False, showgrid=False, zeroline=False, showline=False, range=[min_y, max_y]
        ),
        zaxis=dict(
            nticks=0, showticklabels=False, showgrid=False, zeroline=False, showline=False, range=[min_z, max_z]
        )
    ),
    width=700,
    margin=dict(r=20, l=10, b=10, t=10)
)

# Set aspect ratio to be equal
fig.update_layout(scene_aspectmode='data')


camera = dict(
    up=dict(x=0, y=0, z=1),
    center=dict(x=0, y=0, z=0),
    eye=dict(x=1.25, y=1.25, z=1.25)
)

fig.update_layout(scene_camera=camera)

# Show the figure
# save the figure to a png file
fig.write_image("/scratch/nforouzandehsh/FormalizedLoD/space_DA_solidAngles.png")

print ("ending time: ", time.ctime())