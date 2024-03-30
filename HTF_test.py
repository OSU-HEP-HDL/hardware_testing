import random
import openhtf as htf
from openhtf.output.callbacks import json_factory

@htf.measures(
    htf.Measurement('power_time_series').with_dimensions('ms', 'V', 'A'))
@htf.measures(htf.Measurement('average_voltage').with_units('V'))
@htf.measures(htf.Measurement('average_current').with_units('A'))
@htf.measures(htf.Measurement('resistance').with_units('ohm').in_range(9, 11))
def multdim_measurements(test):
  """Phase with a multidimensional measurement."""
  # Create some fake current and voltage over time data
  for t in range(10):
    resistance = 10
    voltage = 10 + 10.0 * t
    current = voltage / resistance + .01 * random.random()
    dimensions = (t, voltage, current)
    test.measurements['power_time_series'][dimensions] = 0

  # When accessing your multi-dim measurement a DimensionedMeasuredValue
  # is returned.
  dim_measured_value = test.measurements['power_time_series']

  # Let's convert that to a pandas dataframe
  power_df = dim_measured_value.to_dataframe(columns=['ms', 'V', 'A', 'n/a'])
  test.logger.info('This is what a dataframe looks like:\n%s', power_df)
  test.measurements['average_voltage'] = power_df['V'].mean()

  # We can convert the dataframe to a numpy array as well
  power_array = power_df.values
  test.logger.info('This is the same data in a numpy array:\n%s', power_array)
  test.measurements['average_current'] = power_array.mean(axis=0)[2]

  # Finally, let's estimate the resistance
  test.measurements['resistance'] = (
      test.measurements['average_voltage'] /
      test.measurements['average_current'])

@htf.measures(
    htf.Measurement("signal_loss").with_units('dB').in_range(
        minimum=5, maximum=17, marginal_minimum=9, marginal_maximum=11))

def marginal_measurements(test):
  """Phase with a marginal measurement."""
  test.measurements.signal_loss = 13

test = htf.Test(marginal_measurements, multdim_measurements)
test.add_output_callbacks(
      json_factory.OutputToJSON('./measurements.json', indent=2))
test.execute()
from db_utils import authenticate_user_mongodb

client = authenticate_user_mongodb()
