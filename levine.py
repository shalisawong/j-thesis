# levine correlation is the normalized dot product of two vectors
from __future__ import division # float division by default
import math

DIR_IN,DIR_OUT = 1,2

# a correlation function to operate specifically on circuits
def correlate_circuits(entry_circ,exit_circ,**kwargs):
    # get cell timings
    # we ignore the first entry time, because that's a cell
    # from the middle router that was part of circuit setup
    entry_times = [t[0] for t in entry_circ.cells_in][1:]
    exit_times  = [t[0] for t in exit_circ.cells_in]
    return correlate(entry_times,exit_times,**kwargs)

# a generic correlation function
def correlate(entry_times,exit_times,bucket_size=1000):
    # adjust cell timings to be relative to the first recorded time
    start_time = min(entry_times[0],exit_times[0])
    adj_entry_times = [t-start_time for t in entry_times]
    adj_exit_times  = [t-start_time for t in exit_times]
    # get the time series to use for correlation
    bounds = (min(adj_entry_times[ 0],adj_exit_times[ 0]),
              max(adj_entry_times[-1],adj_exit_times[-1]))
    entry_ts = bucketize(adj_entry_times,bounds,bucket_size)
    exit_ts  = bucketize(adj_exit_times, bounds,bucket_size)
    return perform_correlation(entry_ts,exit_ts)

def relative_correlate(entry_times,exit_times,bucket_size=1000):
    adj_entry_times = [t-entry_times[0] for t in entry_times]
    adj_exit_times =  [t-exit_times[0]  for t in exit_times]
    bounds = (0,max(adj_entry_times[-1],adj_exit_times[-1]))
    entry_ts = bucketize(adj_entry_times,bounds,bucket_size)
    exit_ts  = bucketize(adj_exit_times, bounds,bucket_size)
    return perform_correlation(entry_ts,exit_ts)

def perform_correlation(entry_ts,exit_ts):
    # correlation has divide by zero issues if length == 1
    ts_length = len(entry_ts)    
    entry_avg = sum(entry_ts)/ts_length
    exit_avg  = sum(exit_ts)/ts_length
    # Correlation formula:
    #  top =            SUM (x_i-x_avg)*(y_i-y_avg)
    #        ---------------------------------------------------
    #        SQRT{SUM (x_i-x_avg)**2} * SQRT{SUM (y_i-y_avg)**2}
    #             |--- bot_left ---|         |--- bot_right --|
    top,bot_left,bot_right = 0,0,0
    for i in range(len(entry_ts)):
        entry = entry_ts[i] - entry_avg
        exit =  exit_ts[i]  - exit_avg
        top       += entry * exit
        bot_left  += entry**2
        bot_right += exit**2
    bottom = math.sqrt(bot_left) * math.sqrt(bot_right)
    try:
        result = top / bottom
    except Exception:
        result = -1
    return result

# bucketize divides a list of times into a time series for levine correlation.
#    'times' is a list of times (in milliseconds)
#    'bounds' is a pair that's the first and last time for the time series.
#       If bounds is None, it defaults to the first and last times in 'times'.
#       If bounds is not none, the time series is padded with zeros to fill
#       it in. bounds must not be inside 'times'.
#    'bucket_size' is the size of buckets to use (again in milliseconds)
def bucketize(times,bounds=None,bucket_size=1000):
    # given a time, returns the bucket it should be placed into
    def _time_bucket(time):
        return time // bucket_size

    if bounds == None: bounds = times[0],times[-1]
    total_time = bounds[1] - bounds[0] + 1
    series_length = int(math.ceil(total_time / bucket_size))
    series = [0] * series_length
    for time in times:
        try:
            series[_time_bucket(time)] += 1
        except Exception:
            print len(series),time,bucket_size,bounds,_time_bucket(time)
            raise
    return series
    
