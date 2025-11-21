# CBDM -- cubic
import sys
import pandas as pd

print("sys.path1")
print(sys.path)
sys.path.append('/home/nforouzandehsh/RQ1')
from FormalizedLoD.inputs.input_station import *
sys.path.append('/home/nforouzandehsh/daylight_codes')
print("sys.path2")
print(sys.path)
from postprocess import workplane
from CBDM import *
# cubic
room = DB_W01050(quality_representaion='actual')

geom_ids = {
    "LoD_4_actual": DB_W01050(quality_representaion='actual').LoD4(),
}

# write this to a file named rf"{key}_iter{i}_cubic.csv"
for key, to_simulate in geom_ids.items():
# key = "LoD_4_actual" # Debugging
    to_simulate = geom_ids[key] # Debugging
    data_np = DDS(to_simulate = to_simulate,
                epw_file = DB_W01050(quality_representaion='actual').epw_file,
                rad_params ='-ad 4096 -as 2048 -aa 0.01 -ar 4096 -ab 10',
                grid_points_txt = r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/cubic_locations_cubic_spaceAngle3D0.txt",
                base_dir = r"/scratch/nforouzandehsh/temp/RQ1",
                direcory_cleanup = False,
                verbose=0).data
    pd.DataFrame(data_np).to_csv(os.path.join("/scratch/nforouzandehsh/temp/RQ1",
                                              rf"{key}_ad4096_as2048_aa0_01_ar4096_ab10_negative_ill_cubic.csv.gz"), 
                                 index=False,
                                 compression="gzip")