#!/bin/bash

#SBATCH --job-name="CBDM_test"
#SBATCH --time=00:15:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=compute
#SBATCH --mem-per-cpu=1GB
#SBATCH --account=research-abe-aet

# # Cleanup: remove previous log files
# JOB_NAME=$SLURM_JOB_NAME
# for file in slurm*.out; do
#     if [ "$file" != "slurm-${JOB_NAME}.out" ]; then
#         rm $file
#     fi
# done

# Load the required modules
module load 2022r2
module load openmpi
module load python
module load py-pip

# Define virtual environment directory
VENV_DIR=/scratch/nforouzandehsh/.vs/py_venv

# Remove the existing virtual environment if it exists
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Removed the existing virtual environment"
fi

# Create a new virtual environment
python -m venv "$VENV_DIR"
echo "Created a new virtual environment"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip in the virtual environment
pip install --upgrade pip

# Install the required packages in the virtual environment with the correct numpy version range
pip install "numpy>=1.16.5,<1.23.0" scipy==1.7.3 matplotlib==3.7.5 packaging==24.1 trimesh==4.4.1 salib==1.3.12

# Verify installations
pip list

# Check if trimesh is installed
python -c "import trimesh; print('trimesh version:', trimesh.__version__)" || { echo 'Failed to import trimesh'; exit 1; }

# Environment variables
PATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/bin:$PATH
RAYPATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/lib
MANPATH=/scratch/nforouzandehsh/radiance-5.3.012cb17835-Linux/usr/local/radiance/man
export PATH RAYPATH MANPATH

# Run the Python script and redirect output to a log file
srun bash -c "source $VENV_DIR/bin/activate && echo 'Using virtual environment:' && which python && python -c 'import sys; print(sys.path)' && python 01_CBDM_test.py" > 01_CBDM_test.log

# Deactivate the virtual environment
deactivate
