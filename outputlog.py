import time, sys

CELL_SIZE = 498 # size of a Tor cell in bytes
N_REPS = 5000   # number of times to output the log

logfile = open("logs/exit5.log")
lines = logfile.read()
start = time.time()

for i in range(0, N_REPS):
	print lines,

print

total_time = time.time() - start
cell_rate = 1.0*N_REPS*len(lines.split("\n"))/total_time
data_rate = cell_rate*CELL_SIZE/2**10

sys.stderr.write("********************\n")
sys.stderr.write("********************\n")
sys.stderr.write("cell rate: %d cells/second\n" % cell_rate)
sys.stderr.write("data rate: %d KB/s\n" % data_rate)
sys.stderr.write("total time: %i seconds\n" % total_time)
sys.stderr.write("********************\n")
sys.stderr.write("********************\n")

logfile.close()
