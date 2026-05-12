#!/bin/bash
# Plot multiple lat-lon regions for the default cases.
# Cases: articifial_wet_off, articifial_wet_on
#
# Each region entry: "label  lat_min  lat_max  lon_min  lon_max"

set -euo pipefail

SCRIPT="src/plot_atm_lpjml_wrapped_timeseries.py"
regions=(
    "north_amazon_point   2    5   -63  -60"
    "south_amazon_point -10   -7   -63  -60"
    "south_amazon       -16   -2   -70  -50"
    "north_amazon        -2   12   -82  -46"
)

for region in "${regions[@]}"; do
    read -r label lat_min lat_max lon_min lon_max <<< "${region}"
    echo "Plotting region: ${label} (lat: ${lat_min} to ${lat_max}, lon: ${lon_min} to ${lon_max})"
    python "${SCRIPT}" \
        --label "${label}" \
        --lat-min "${lat_min}" \
        --lat-max "${lat_max}" \
        --lon-min "${lon_min}" \
        --lon-max "${lon_max}" \
        --casenames articifial_wet_on articifial_wet_off
done

echo "All regions done."
