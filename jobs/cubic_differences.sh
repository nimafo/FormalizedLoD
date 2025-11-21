#!/bin/bash

#SBATCH --job-name="cubic_differences"
#SBATCH --time=25:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=research-abe-aet
#SBATCH --output=cubic_differences.out

module load 2024r1
module load python
module load py-pip


/home/nforouzandehsh/.conda/envs/FormalizedLoD/bin/python /home/nforouzandehsh/RQ1/jobs/cubic_differences.py > cubic_differences.log