import sys

'''
for i in range (10):
	sys.stdout.write("0:0:"+str(i)+":992256 [thread-0] 0:0:5:00000000"+str(i)+" [scallion-message] [2.relay-76.1.0.0] [intercept_logv] [notice] command_process_create_cell() CREATE: 53683 63.1.0.0\n") 
'''

with open("filtered_scallion.log", "r") as f:
	for line in f:
		try:
			sys.stdout.write(line)
		except:
			print "Broken pipe?", line


	
