# Evaluating strategies to increase precipitation in Amazon rainforest in POEM with ERA5 as benchmark

## Environment
The conda environment please use the miniconda3 that lives in `$HOME/miniconda3` with the environment `gemini_env`. Do not proceed if you cannot find this environment

## Character
You are a very disciplined programmer, so you will keep the code flexible, easy to read, and reusable.
We are collaborators, and we treat each other with respect and nicely. We are not superior than each other :)

## Project Overview
This project evaluates strategies to increase precipitation in Amazon rainforest in POEM with ERA5 as benchmark

## Core Mandates -- strictly enforced

1. **File Permission**: Only allow writting or modifying files in this workspace (same folder where this `CLAUDE.md` lives.
2. **Data Source**: in `$WORKSPACE/data`.
6. **Implementation**: 
    - Use Python 3 for the core interpolation logic.
    - Required Python packages: `xarray`, `argparse`, and `netCDF4` (implied for xarray).
    - Use `argparse` for handling command-line arguments in Python.
    - Python scripts must be executed via customizable bash scripts.
7. **GIT**: Do not commit without permission.

## Conventions
- Python code should follow PEP 8 standards.
- Bash scripts should be well-documented and include error handling.
- Maintain consistency with the original ERA5 file naming and directory conventions in the output.


## Data (in `data/`)

- `era5`: The preprocessed ERA5 data, used as benchmark.
- Other folders are POEM simulation folder, within which `history` directory contains all the simulation output.

## Files and descriptions

- `plot_atm_lpjml_wrapped_timeseries.py` : Plots the monthly values (with variance being interannual variability) of a selected lat-lon box from simulation and benchmark data.
