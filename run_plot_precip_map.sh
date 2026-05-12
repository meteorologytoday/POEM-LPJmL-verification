#!/bin/bash
# Plot precipitation maps for all four seasons.
# Cases: articifial_wet_off, articifial_wet_on

set -euo pipefail

SCRIPT="src/plot_precip_response_map.py"

seasons=("DJF" "MAM" "JJA" "SON" "ANNUAL")

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
