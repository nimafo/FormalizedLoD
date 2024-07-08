#!/bin/bash

#SBATCH --job-name="CBDM_test"
#SBATCH --time=00:05:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=5GB
#SBATCH --account=research-abe-aet


module load 2022r2
module load openmpi
module load python
module load py-pip

# Create a virtual environment in the scratch directory, if it already exists, remove it
VENV_DIR=/scratch/nforouzandehsh/FormalizedLoD/.vs/py_env

if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Removed the existing virtual environment"
fi

python -m venv "$VENV_DIR"
echo "Created a new virtual environment"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip in the virtual environment
pip install --upgrade pip

# Install required packages in the virtual environment
pip install numpy scipy matplotlib packaging

# Environment variables
PATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/bin:$PATH
RAYPATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/lib
MANPATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/man
export PATH RAYPATH MANPATH

# Run the Python script and redirect output to a log file
srun python 01_CBDM_test.py > 01_CBDM_test.log

# Deactivate the virtual environment
deactivate
