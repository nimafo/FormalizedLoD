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

geom_ids = {
    "DB_W01050_LoD_4_actual": DB_W01050(quality_representaion='actual').LoD4(),
    "DB_W01050_LoD_3_actual": DB_W01050(quality_representaion='actual').LoD3(),
    "DB_W01050_LoD_2_actual": DB_W01050(quality_representaion='actual').LoD2(),
    "DB_W01050_LoD_1_actual": DB_W01050(quality_representaion='actual').LoD1(),
    "DB_W01050_LoD_4_bounding_box": DB_W01050(quality_representaion='oriented bounding box').LoD4(),
    "DB_W01050_LoD_3_bounding_box": DB_W01050(quality_representaion='oriented bounding box').LoD3(),
    "DB_W01050_LoD_2_bounding_box": DB_W01050(quality_representaion='oriented bounding box').LoD2(),
    "DB_W01050_LoD_1_bounding_box": DB_W01050(quality_representaion='oriented bounding box').LoD1()
}
# geom_ids = {
#     "DB_550_LoD_4_actual": DB_W550(quality_representaion='actual').LoD4(),
#     "DB_550_LoD_3_actual": DB_W550(quality_representaion='actual').LoD3(),
#     "DB_550_LoD_2_actual": DB_W550(quality_representaion='actual').LoD2(),
#     "DB_550_LoD_1_actual": DB_W550(quality_representaion='actual').LoD1(),
#     "DB_550_LoD_4_bounding_box": DB_W550(quality_representaion='oriented bounding box').LoD4(),
#     "DB_550_LoD_3_bounding_box": DB_W550(quality_representaion='oriented bounding box').LoD3(),
#     "DB_550_LoD_2_bounding_box": DB_W550(quality_representaion='oriented bounding box').LoD2(),
#     "DB_550_LoD_1_bounding_box": DB_W550(quality_representaion='oriented bounding box').LoD1()
# }


# write this to a file named rf"{key}_iter{i}_cubic.csv"
for key, to_simulate in geom_ids.items():
    to_simulate = geom_ids[key]
    data_np = DDS(to_simulate = to_simulate,
                epw_file = DB_W550(quality_representaion='actual').epw_file,
                rad_params ='-ad 2048 -as 1024 -aa 0.1 -ar 1024 -ab 7',
                # grid_points_txt = r"/home/nforouzandehsh/RQ1/inputs/W01050/manual_surface_model/S06/workplane_overlap_removed.txt",
                grid_points_txt = r"/home/nforouzandehsh/RQ1/inputs/WBG550/manual_surface_model/S10/points_workplane_overlaps_removed.txt",
                base_dir = r"/scratch/nforouzandehsh/temp/RQ1",
                direcory_cleanup = True,
                verbose=0).data
    pd.DataFrame(data_np).to_csv(os.path.join("/scratch/nforouzandehsh/temp/RQ1",
                                              rf"{key}_workplane.csv.gz"),
                                 index=False,
                                 compression="gzip")