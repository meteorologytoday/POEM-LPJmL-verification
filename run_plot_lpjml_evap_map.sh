#!/bin/bash
# Plot LPJmL evaporation maps for all seasons.
# Cases: articifial_wet_off, articifial_wet_on

set -euo pipefail

CONDA_ENV="gemini_env"
CONDA_BASE="${HOME}/miniconda3"
SCRIPT="src/plot_lpjml_evap_map.py"

seasons=("DJF" "MAM" "JJA" "SON" "ANNUAL")

# Activate conda environment
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"

for season in "${seasons[@]}"; do
    echo "Plotting season: ${season}"
    python "${SCRIPT}" \
        --lat-min -60 \
        --lat-max  40 \
        --lon-min -120 \
        --lon-max -10 \
        --season "${season}" \
        --casenames \
            articifial_wet_off \
            articifial_wet_on
done

echo "All seasons done."
