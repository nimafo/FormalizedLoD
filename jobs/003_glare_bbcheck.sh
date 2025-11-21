#!/bin/bash

#SBATCH --job-name="003_glare_bbcheck"
#SBATCH --time=100:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=research-abe-aet
#SBATCH --output=003_glare_bbcheck.out

module load 2024r1
module load python
module load py-pip


/home/nforouzandehsh/.conda/envs/RQ2_performance_evaluation/bin/python /home/nforouzandehsh/RQ1/jobs/003_glare_bbcheck.py > 003_glare_bbcheck.log