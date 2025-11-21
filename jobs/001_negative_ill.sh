#!/bin/bash

#SBATCH --job-name="001_negative_ill"
#SBATCH --time=10:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=research-abe-aet
#SBATCH --output=001_negative_ill.out

module load 2024r1
module load python
module load py-pip


/home/nforouzandehsh/.conda/envs/FormalizedLoD/bin/python /home/nforouzandehsh/RQ1/jobs/001_negative_ill.py > 001_negative_ill.log