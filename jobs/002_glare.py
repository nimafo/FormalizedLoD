# CBDM -- workplane
import sys
import pandas as pd
sys.path.append('/home/nforouzandehsh/RQ1')
from FormalizedLoD.inputs.input_station import *
sys.path.append('/home/nforouzandehsh/daylight_codes')
from CBDM import *

geom_ids = {
    # "DB_W01050_LoD_4_actual": {"geometry": DB_W01050(quality_representaion='actual').LoD4(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_3_actual": {"geometry": DB_W01050(quality_representaion='actual').LoD3(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_2_actual": {"geometry": DB_W01050(quality_representaion='actual').LoD2(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_1_actual": {"geometry": DB_W01050(quality_representaion='actual').LoD1(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_4_bounding_box": {"geometry": DB_W01050(quality_representaion='oriented bounding box').LoD4(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_3_bounding_box": {"geometry": DB_W01050(quality_representaion='oriented bounding box').LoD3(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_2_bounding_box": {"geometry": DB_W01050(quality_representaion='oriented bounding box').LoD2(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_W01050_LoD_1_bounding_box": {"geometry": DB_W01050(quality_representaion='oriented bounding box').LoD1(), "view": (-4.391694, -0.118099, 1.482738, -0.85443,0.519567,0)},
    # "DB_550_LoD_4_actual": {"geometry": DB_W550(quality_representaion='actual').LoD4(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    # "DB_550_LoD_3_actual": {"geometry": DB_W550(quality_representaion='actual').LoD3(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    # "DB_550_LoD_2_actual": {"geometry": DB_W550(quality_representaion='actual').LoD2(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    # "DB_550_LoD_1_actual": {"geometry": DB_W550(quality_representaion='actual').LoD1(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    "DB_550_LoD_4_bounding_box": {"geometry": DB_W550(quality_representaion='oriented bounding box').LoD4(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    "DB_550_LoD_3_bounding_box": {"geometry": DB_W550(quality_representaion='oriented bounding box').LoD3(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    "DB_550_LoD_2_bounding_box": {"geometry": DB_W550(quality_representaion='oriented bounding box').LoD2(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    "DB_550_LoD_1_bounding_box": {"geometry": DB_W550(quality_representaion='oriented bounding box').LoD1(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)}
}


for ts in [
           (3,20,12,0),
           (6,21,12,0),
           (12,21,12,0),
           (3,20,9,0),
           (6,21,9,0),
           (12,21,9,0),
           (3,20,15,0),
           (6,21,15,0),
           (12,21,15,0)
           ]:
    for room_name, item in geom_ids.items():
        render_scene(to_simulate = item["geometry"],
                    view = item["view"],
                    time = ts,
                    sim_save_parent_directory = rf"/scratch/nforouzandehsh/temp/RQ1",
                    remove_temp = True,
                    remove_hdr_and_fc = True,
                    simulation_name = f"glare_{room_name}_{ts[0]}_{ts[1]}_{ts[2]}_{ts[3]}",
                    verbose=0)
        