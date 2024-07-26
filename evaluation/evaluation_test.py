
import os
os.chdir(f"/home/{os.getlogin()}/watttime-python-client-aer-algo")

import math
import numpy as np
import pandas as pd
import datetime
import pytz
from datetime import datetime, timedelta
from watttime import WattTimeForecast, WattTimeHistorical
from watttime.api_data_cache import DataCache

import optimizer.s3 as s3u
import evaluation.eval_framework as efu

import watttime.shared_anniez.alg.optCharger as optC
import watttime.shared_anniez.alg.moer as Moer



region = "PJM_NJ"
username = os.getenv("WATTTIME_USER")
password = os.getenv("WATTTIME_PASSWORD")

actual_moer_data = WattTimeHistorical(username, password)
hist_fcst_data = WattTimeForecast(username, password)


s3 = s3u.s3_utils()
key = '20240715_1k_synth_users.csv'
generated_data = s3.load_csvdataframe(file=key)


synth_data = generated_data.copy(deep=True)

# Sort by time if you want to minimize the data loaded (all rows will be for the same date)
synth_data = synth_data.sort_values('plug_in_time') 
synth_data = synth_data.head(100)


time_zone = efu.get_timezone_from_dict(region)
synth_data["plug_in_time"] = pd.to_datetime(synth_data["plug_in_time"]).apply(lambda x: efu.convert_to_utc(x, time_zone))
synth_data["unplug_time"] = pd.to_datetime(synth_data["unplug_time"]).apply(lambda x: efu.convert_to_utc(x, time_zone))

# Context for which to load and cache data
data_start = synth_data['plug_in_time'].min()
data_end = synth_data['unplug_time'].max()

print(f"Loading data for context: {data_start} to {data_end}")

forecast_data_cache = efu.setup_forecast_moer_data_cache(data_start, data_end, region)
moer_data_cache = efu.setup_actual_moer_data_cache(data_start, data_end, region)


# Gets moer forecasts at plug-in-time
synth_data['moer_data'] = synth_data.apply(
    lambda x: efu.get_historical_fcst_data(
        forecast_data_cache,
        x.plug_in_time,
    ), axis = 1
)

# Get actual moer from plug-in to unplug_time
synth_data['moer_data_actual'] = synth_data.apply(
    lambda x: efu.get_historical_actual_data(
        moer_data_cache, 
        x.plug_in_time,
        x.unplug_time,
    ), axis = 1
)


# Gets a charging schedule based on moer forecasts at plug-in time
synth_data['charger_simple_predicted'] = synth_data.apply(
    lambda x: efu.setup_charger(
        x.MWh_fraction,
        x.charge_MWh_needed,
        math.floor(x.total_intervals_plugged_in), # will throw an error if the plug in time is too shart to reach full charge, should soften to a warning
        x.moer_data,
        asap = False
    ), 
    axis = 1
)

# Gets a "perfect" charging schedule based on actual moer
synth_data['charger_simple_actual_perfect'] = synth_data.apply(
    lambda x: efu.setup_charger(
        x.MWh_fraction,
        x.charge_MWh_needed,
        math.floor(x.total_intervals_plugged_in), # will throw an error if the plug in time is too shart to reach full charge, should soften to a warning
        x.moer_data_actual,
        asap = False
    ), 
    axis = 1
)

# Setup an ASAP charger based on actual moer ()
synth_data['charger_asap_actual'] = synth_data.apply(
    lambda x: efu.setup_charger(
        x.MWh_fraction,
        x.charge_MWh_needed,
        math.floor(x.total_intervals_plugged_in), # will throw an error if the plug in time is too shart to reach full charge, should soften to a warning
        x.moer_data_actual,
        asap = True
    ), 
    axis = 1
)


# Gets projected cost of charging (predicted emissons))
synth_data['simple_fit_results_predicted'] = synth_data['charger_simple_predicted'].apply(
    lambda  x: x.get_total_cost() if x is not None else None
)

# Gets actual cost of using schedule produced at plug in time (actual emissions using predictions)
synth_data['simple_fit_results_realized'] = synth_data.apply(
    lambda x: efu.get_actual_cost_of_schedule(x.charger_simple_predicted, x.moer_data_actual),
    axis=1
)

# Gets cost given we had the actual data (optimal behavior based on perfect info)
synth_data['simple_fit_results_perfect'] = synth_data['charger_simple_actual_perfect'].apply(
    lambda  x: x.get_total_cost() if x is not None else None
)

# Gets cost of doing ASAP charging (baseline behavior)
synth_data['asap_fit_results_actual'] = synth_data['charger_asap_actual'].apply(
    lambda  x: x.get_total_cost() if x is not None else None
)



print(synth_data[['simple_fit_results_predicted', 'simple_fit_results_realized', 'simple_fit_results_perfect', 'asap_fit_results_actual']])