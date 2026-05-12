from pathlib import Path
import xarray as xr
import numpy as np

def get_saturated_vapor_pressure(temperature_in_degC):
    nonnegative_temperature = np.where(temperature_in_degC > 0, temperature_in_degC, 0)
    return 6.112 * np.exp( (17.67 * nonnegative_temperature) / (nonnegative_temperature + 243.5));

def get_saturated_specific_humidity(temperature_in_degC):
    es = get_saturated_vapor_pressure(temperature_in_degC)
    return 0.622 * es / (1013.0 - es)

freezing_point = 273.15 # Kelvin

root = Path("./data")
output_dir = Path("figures")

output_dir.mkdir(exist_ok=True, parents=True)
casenames = [
    "control",
#    "depl_all_prop_depl_wateruse_0017110101",
]

data_directories = {
    casename : root / f"{casename}" 
    for casename in casenames
}

skip_time = 12*0
control_casename = "control"

plotting_variables = [
#    ("atm", "t_ref", 1.0, "K"),
#    ("atm", "t_surf", 1.0, "K"),
#    ("lpjml", "soil_surf_temp", 1.0, "degC"),
#    ("atm", "q_ref"),
#    ("atm", "sphum_surf"),
#    ("atm", "wind", 1.0, "m/s"),

#    ("flx", "evap", 86400*30, "mm/month"),
#    ("flxlnd", "evap_land", 86400*30, "mm/month"),
    ("lpjml", "mprec", 1.0, "mm/month"),
    ("lpjml", "evap1", 86400*30, "mm/month"),
    ("estimated", "evap", 86400*30, "mm/month"),
    ("lpjml", "mswc1", 1, "scalar"),
    ("lpjml", "mswc2", 1, "scalar"),
#    ("estimated", "humidity_potential", 1e3, "g/kg"),
#    ("atm", "sphum_surf", 1e3, "g/kg"),
#    ("estimated", "surface_saturated_specific_humidity", 1e3, "g/kg"),
    ("lpjml", "soil_surf_temp", 1.0, "degC"),
    ("estimated", "ref_wind", 1.0, "m/s"),
#    ("lpjml", "mq_ca", 1e3, "g/kg"),


#    ("lpjml", "mgpp"),
#    ("lpjml", "vegc"),
]

data = dict()

#lat_rng = [-2, 12]
#lon_rng = [360-82, 360-46]

# South Amazon, all on land
#lat_rng = [-16, -2]
#lon_rng = [360-70, 360-50]

# A small box (3degx3deg)
#lat_rng = [-10, -7]
lat_rng = [2, 5]
lon_rng = [360-63, 360-60]

# A small box (3degx3deg)
#lat_rng = [-3, -0]
#lon_rng = [360-60, 360-57]

# load era5

try:    

    path_str = [
        "data/era5/data_stream-moda_stepType-avgad.nc",
        "data/era5/data_stream-moda_stepType-avgua.nc",
    ]
    print(f"Loading: ", path_str)

    # The times of these file shift due to different statistics
    # So, I drop these times so that the time will be stacked,
    # instead of appended.
    ds_era5 = xr.merge([
        xr.open_dataset(_path).drop_vars("valid_time")
        for _path in path_str
    ])
    
    print(ds_era5)

    lat = ds_era5.coords["latitude"]
    lon = ds_era5.coords["longitude"] % 360
    ds_era5 = ds_era5.where(
          (lat > lat_rng[0]) & (lat < lat_rng[1])
        & (lon > lon_rng[0]) & (lon < lon_rng[1])
    ).weighted(np.cos(lat*np.pi/180)).mean(dim=["latitude", "longitude"])
    print(ds_era5)
    ds_era5 = ds_era5.coarsen(valid_time=12).construct(valid_time=("year", "month"))

except Exception as e:
    print(f"Error: Cannot load era5.")
    print(str(e))
    raise e



# load data
for casename in casenames:
    
    try:    

        data_directory = data_directories[casename] / "history"
        lpjml_data_directory = data_directories[casename] / "lpjml_output" 

        path_str = str(data_directory / "*.atmos_month.nc")

        print(f"Loading: {path_str:s}")
        ds_atm = xr.open_mfdataset(path_str, decode_times=False)
        ds_atm = ds_atm.where(
              (ds_atm.coords["lat"] > lat_rng[0]) & (ds_atm.coords["lat"] < lat_rng[1])
            & (ds_atm.coords["lon"] > lon_rng[0]) & (ds_atm.coords["lon"] < lon_rng[1])
        ).weighted(np.cos(ds_atm.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"])
        print(ds_atm)

        ds_lpjml = xr.open_mfdataset([
            lpjml_data_directory / f"{varname}.nc"
            for varname in [
                "mprec",
                "evap1",
                "mswc1",
                "mswc2",
                "mgpp",
                "vegc",
                "fpc",
                "soil_surf_temp",
                "mq_ca",
            ]
        ], decode_times=False)
        ds_lpjml = ds_lpjml.where(
              (ds_lpjml.coords["lat"] > lat_rng[0]) & (ds_lpjml.coords["lat"] < lat_rng[1])
            & (ds_lpjml.coords["lon"] % 360 > lon_rng[0]) & (ds_lpjml.coords["lon"] % 360 < lon_rng[1])
        ).weighted(np.cos(ds_lpjml.coords["lat"]*np.pi/180)).mean(dim=["lat", "lon"], skipna=True)
        sum_fpc = ds_lpjml["fpc"].isel()
        print(ds_lpjml)

        rho = 1.22
        drag_coefficient = 1e-3
        saturated_specific_humidity = get_saturated_specific_humidity(ds_lpjml["soil_surf_temp"].to_numpy())
        _humidity_potential_estimated = saturated_specific_humidity - ds_atm["q_ref"].to_numpy()
        _ref_wind_estimated = np.sqrt(ds_atm["u_ref"].to_numpy()**2 + ds_atm["v_ref"].to_numpy()**2)
        _evap_estimated = 1.22 * drag_coefficient * _ref_wind_estimated * _humidity_potential_estimated * ds_lpjml["mswc1"].to_numpy()

        surface_saturated_specific_humidity = xr.zeros_like(ds_atm["wind"]).rename("surface_saturated_specific_humidity").load()
        surface_saturated_specific_humidity.values[:] = saturated_specific_humidity
        
        humidity_potential_estimated = xr.zeros_like(ds_atm["wind"]).rename("humidity_potential").load()
        humidity_potential_estimated.values[:] = _humidity_potential_estimated


        evap_estimated = xr.zeros_like(ds_atm["wind"]).rename("evap").load()
        evap_estimated.values[:] = _evap_estimated[:]

        ref_wind_estimated = xr.zeros_like(ds_atm["wind"]).rename("ref_wind").load()
        ref_wind_estimated.values[:] = _ref_wind_estimated[:]

        print("==================")
        print(evap_estimated)
        ds_estimated = xr.merge([
            evap_estimated,
            ref_wind_estimated,
            surface_saturated_specific_humidity,
            humidity_potential_estimated,
        ])
        data[casename] = {
            'atm' : ds_atm.isel(time=slice(skip_time, None, None)),
#            'flx' : ds_flx,
#            'flxlnd' : ds_flxlnd,
            'lpjml' : ds_lpjml.isel(time=slice(skip_time, None, None)),
            'estimated' : ds_estimated.isel(time=slice(skip_time, None, None)),
        }

        for component, ds in data[casename].items():
            data[casename][component] = ds.isel(time=slice(skip_time, None, None)).coarsen(time=12).construct(time=("year", "month"))
    except Exception as e:
        print(f"Error: Cannot load {casename:s}.")
        print(str(e))
        raise e

print("Data loaded")
# plot time series
import matplotlib as mplt
#mplt.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory
from matplotlib.ticker import MultipleLocator
from datetime import datetime

colors = plt.colormaps["plasma"](np.linspace(0, 1, len(data.keys()) + 3))

fig, ax = plt.subplots(len(plotting_variables), 1, sharex=True, figsize=(10, len(plotting_variables)*3), squeeze=False)

ax_flattened = ax.flatten()

for j, (component, varname, factor, unit) in enumerate(plotting_variables):
    _ax = ax_flattened[j]
    for i, (case_name, _data) in enumerate(data.items()):
        da = _data[component][varname].to_numpy() * factor
        _ax.errorbar(x=np.arange(1, 13),
                 y=da.mean(axis=0), 
                 yerr=da.std(axis=0), 
                 fmt='-o',          # Line with circular markers
                 capsize=5,         # Adds horizontal 'caps' to the error bars
                 color=colors[i],
                 label=case_name,
        )

        if i == 0:

            da = None
            if varname == "mprec":
                da = ds_era5["tp"].to_numpy() * 30*1000
            elif varname == "ref_wind":
                da = ds_era5["si10"].to_numpy()
            elif varname == "soil_surf_temp":
                da = ds_era5["stl1"].to_numpy() - 273.15
            elif varname in ["evap1", "evap"]:
                da = - ds_era5["e"].to_numpy() * 30*1000
            elif varname == "mswc1":
                da = ds_era5["swvl1"].to_numpy()
            elif varname == "mswc2":
                da = ds_era5["swvl2"].to_numpy()
            elif varname == "mswc3":
                da = ds_era5["swvl3"].to_numpy()
            elif varname == "mswc4":
                da = ds_era5["swvl4"].to_numpy()





            if da is not None:
                _ax.errorbar(x=np.arange(1, 13),
                         y=da.mean(axis=0), 
                         yerr=da.std(axis=0), 
                         fmt='--o',          # Line with circular markers
                         capsize=5,         # Adds horizontal 'caps' to the error bars
                         color="red",
                         label="era5",
                )
     
        if i == 0:
            _ax.set_ylabel(f"[{unit:s}]")
    _ax.set_title(f"({component}: {varname})")
        
fig.suptitle(f"Average range : longitude $ \\in [{lon_rng[0]:.1f}, {lon_rng[1]:.1f}] $, latitude $ \\in [{lat_rng[0]:.1f}, {lat_rng[1]:.1f}] $")
for _ax in ax_flattened:
    _ax.xaxis.set_major_locator(MultipleLocator(1))
    _ax.grid()
    _ax.legend()
    _ax.set_xlabel("Year")

for extension in ["png", "svg"]:
    output_file = output_dir / f"atm_lnd_diagnostic_wrapped.{extension}"
    print(f"Write to file: {str(output_file)}")
    fig.savefig(output_file, dpi=200)

print("Showing figure")
plt.show()
