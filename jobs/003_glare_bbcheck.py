# CBDM -- workplane
import sys
import pandas as pd
sys.path.append('/home/nforouzandehsh/RQ1')
from FormalizedLoD.inputs.input_station import *
sys.path.append('/home/nforouzandehsh/daylight_codes')
from CBDM import *

geom_ids = {
    # "DB_550_LoD_4_actual": {"geometry": DB_W550(quality_representaion='actual').LoD4(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},
    "DB_550_LoD_4_bounding_box": {"geometry": DB_W550(quality_representaion='oriented bounding box').LoD4(), "view": (0.9864, 4.307539, 1.54326, 0, -1, 0)},

}

for ts in [
            (3,20,12,0),
           ]:
    for room_name, item in geom_ids.items():
        render_scene(to_simulate = item["geometry"],
                    view = item["view"],
                    time = ts,
                    sim_save_parent_directory = rf"/scratch/nforouzandehsh/temp/RQ1",
                    remove_temp = True,
                    remove_hdr_and_fc = False,
                    simulation_name = f"glare_bbcheck_{room_name}_{ts[0]}_{ts[1]}_{ts[2]}_{ts[3]}",
                    verbose=0)
        