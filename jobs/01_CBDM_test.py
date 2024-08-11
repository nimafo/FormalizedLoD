import sys
sys.path.append('/scratch/nforouzandehsh/FormalizedLoD')
sys.path.append('/scratch/nforouzandehsh/DelftBlueFiles')
# from input_station import GLODs, DB_s01, DB_s02, DB_s04, DB_s06, DB_s07, DB_s08, DB_s09, DB_s10, DB_s11
from input_station import DB_s08 # the input space
from definitions import AnnualSimulation
import os
import pathlib
# import wandb
import pandas as pd
import numpy as np
import mpi4py.MPI as MPI
# wandb.login(key = '2b8311264e061975b7272a261ea39d1d2c41ec5e')
# wandb.init(name = "Uncertainty Quantification - s07-GLOD3")

#user inputs: 
glod = 4



comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# List setup
#mcoa = [0.05, 0.10, 0.15, 0.20]
Mat_acc_levels = [0,0,0,0]  # 4 ground truth cases >> test the stability of the results
#Mat_acc_levels = [] 

# for i in range(121):
#     Mat_acc_levels.append(mcoa[0])
#     Mat_acc_levels.append(mcoa[1])
#     Mat_acc_levels.append(mcoa[2])
#     Mat_acc_levels.append(mcoa[3])

# Split the work among processes
chunk_size = len(Mat_acc_levels) // size
start = rank * chunk_size
end = (rank + 1) * chunk_size

# Loop over the assigned chunk
for i in range(start, end):
    print(f"i: {i}")
    space = DB_s08(Mat_acc_levels[i],cubic_grid=1)
    if glod == 1:
        to_simulate = space.GLOD1()
    elif glod == 2:
        to_simulate = space.GLOD2()
    elif glod == 0:
        to_simulate = space.GLOD0()
    elif glod == 3:
        to_simulate = space.GLOD3()
    elif glod == 4:
        to_simulate = space.GLOD4()
    else:
        print("GLOD not defined")
    epw_file = space.epw_file

    grid_points_txt = space.grid_points_txt # add cubic illuminance thingie here.
    if not os.path.exists('/scratch/nforouzandehsh/DelftBlueFiles/Outputs/RadFiles'):
        os.makedirs('/scratch/nforouzandehsh/DelftBlueFiles/Outputs/RadFiles')
    data, simulation_run_name = AnnualSimulation(to_simulate, epw_file, grid_points_txt, base_dir='/scratch/nforouzandehsh/DelftBlueFiles/Outputs/RadFiles')

    if data.size:
        print(f"size of data: {data.size}")
        data = pd.DataFrame(data)
        print("changing directory")
        os.chdir("/scratch/nforouzandehsh/DelftBlueFiles/Outputs/")
        data.astype(np.int32).to_csv(f'{space.ID}_{glod}_{Mat_acc_levels[i]}_{simulation_run_name}.csv.gz', index=False, compression='gzip')

    # Log data
    simulated = comm.allreduce(1, op=MPI.SUM)
    progress = 100 * (simulated / len(Mat_acc_levels))
#     wandb.log({f"Simulation progress[%]": progress})

# wandb.finish()



