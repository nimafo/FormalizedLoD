#!/bin/bash

#SBATCH --job-name="002_glare"
#SBATCH --time=50:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=research-abe-aet
#SBATCH --output=002_glare.out

module load 2024r1
module load python
module load py-pip


/home/nforouzandehsh/.conda/envs/RQ2_performance_evaluation/bin/python /home/nforouzandehsh/RQ1/jobs/002_glare.py > 002_glare.log