import sys
sys.path.append('/scratch/nforouzandehsh/FormalizedLoD')
sys.path.append('/scratch/nforouzandehsh/DelftBlueFiles')
from input_station import DB_s09_unceraintyIsolation, DB_s11_unceraintyIsolation, DB_s06_unceraintyIsolation
from definitions import AnnualSimulation
import os
from mpi4py import MPI
import numpy as np
import pandas as pd

# Space_ID = "s06"
# reflectance_MCOAs= [0.05,0.10,0.15,0.20]
# transmittance_MCOAs = reflectance_MCOAs.copy()
# Mat_acc_levels = []
# # for ref in reflectance_MCOAs:
# #     for trans in transmittance_MCOAs:
# #         for i in range(500):
# #             Mat_acc_levels.append({"reflectance": ref,
# #                                    "transmittance": trans})
            
# # make ground truth
# for i in range(4):
#     Mat_acc_levels.append({"reflectance": 0,
#                             "transmittance": 0})

# #____________________________
# comm = MPI.COMM_WORLD
# rank = comm.Get_rank()
# size = comm.Get_size()
# # Split the work among processes
# chunk_size = len(Mat_acc_levels) // size
# start = rank * chunk_size
# end = (rank + 1) * chunk_size

# # Loop over the assigned chunk
# for i in range(start, end):
#     print(f"i: {i}")
#     space = DB_s06_unceraintyIsolation(trans_Mat_acc_level=Mat_acc_levels[i]["transmittance"], 
#                                        reflect_Mat_acc_level=Mat_acc_levels[i]["reflectance"])
#     to_simulate = space.GLOD4()
#     epw_file = space.epw_file

#     grid_points_txt = space.grid_points_txt
#     data, simulation_run_name = AnnualSimulation(to_simulate, epw_file, grid_points_txt, base_dir='/scratch/nforouzandehsh/DelftBlueFiles/Outputs/RadFiles')

#     if data.size:#ensures non-emptiness in the results file 
#         print(f"size of data: {data.size}")
#         data = pd.DataFrame(data)
#         print("Changing directory")
#         os.chdir("/scratch/nforouzandehsh/DelftBlueFiles/Outputs/tranmittance_reflectance_Uncertainty_isolation")
#         data.astype(np.int32).to_csv(f'{Space_ID}_T_{Mat_acc_levels[i]["transmittance"]}_R_{Mat_acc_levels[i]["reflectance"]}_{simulation_run_name}.csv.gz', index=False, compression='gzip')

#     # Log data  
#     # simulated = comm.allreduce(1, op=MPI.SUM)
#     # progress = 100 * (simulated / len(Mat_acc_levels))
# # wandb.log({f"Simulation progress[%]": progress})

# # wandb.finish()