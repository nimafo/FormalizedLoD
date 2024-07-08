#!/bin/bash

#SBATCH --job-name="solid_angle_viz"
#SBATCH --time=10:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=12GB
#SBATCH --account=research-abe-aet

module load 2023r1

srun /usr/bin/python3.11 00_space_DA_solidAngles.py > 00_space_DA_solidAngles.log

