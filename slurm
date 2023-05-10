#!/bin/bash
#
#SBATCH --job-name=test
#SBATCH --output=res.txt
#SBATCH --nodes=2
#SBATCH --time=05:00
#SBATCH -p short-28core
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=alexander.borca-tasciuc@stonybrook.edu

module load anaconda/3
module load gnu-parallel/6.0

parallel --jobs 5 python test.py {} ::: {1}