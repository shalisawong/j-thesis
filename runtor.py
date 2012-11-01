import autotor as at
import time

def run(n=1,**kwargs):
    finished = 0
    repeated_failures = 0
    while finished < n:
        reload(at)
        print 'Trying to run trial %d.' % (finished+1)
        attempt = at.run_single_safe(**kwargs)
        if attempt:
            repeated_failures = 0
            finished += 1
            print 'Trial %d succeeded.' % finished
            time.sleep(2)
        else:
            repeated_failures += 1
            # if we're failing repeatedly, we'll try waiting for a bit between trials
            if repeated_failures > 1:
                wait_time = 2**repeated_failures
                print 'Failed',repeated_failures,'times in a row. Waiting',wait_time,'seconds.'
                time.sleep(wait_time)

