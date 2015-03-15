'''
Automates the post-data collection process.
	Syntax: python post_processing -getData infile nodename shortname
		    python post_processing -visualizations graphing_mode shortname
		    python post_processing.py -clientSeries infile nodename type_client num_graphs shortname

where infile is a scallion.log file.
      nodename is the name of a relay/node (ex: relaymiddle2)
	  shortname is a string in the format nodename_numclients (ex: rm2_50)
      graphing_mode is the plot wanted (-summarize, -horizon, -colorplots, -allPlots)
	  type_client is the name of the client wanted
			(web, bulk, perfclient50k, perfclient1m, perclient5m, -allClients)
	  num_graphs is an integer of the number of graphs wanted

@author: Shalisa Pattarawuttiwong
'''

import sys, re, subprocess
import timeplot_clients
import operator

'''
	Returns the number of nodes that are relays, non-relays, and a dictionary of
	{nodes:number of cells} in the scallion.log.
	Allows for picking relay with most cells going through.
	@param infile: a scallion.log file
	@return: a dictionary of {nodename:number of cells}
'''
def info_scallion(infile):
	with open(infile, "r") as f:
		nodes = {}
		for line in f:
			split = line.split() # split the log
			if "CLIENTLOGGING" in line:
				name = split[4].split("~")[0].replace("[", "")
				if name not in nodes:
					nodes[name] = 1
				else:
					num = nodes.get(name) + 1
					nodes[name] = num
		return sorted(nodes.items(), key=operator.itemgetter(1))

'''
	Filters and formats scallion.log data
		Syntax: python post_processing -get_data infile nodename shortname
	@param infile: a scallion.log file
	@param nodename: the name of a relay/node
	@param name: a string in the format nodename_numclients (ex: rm2_50)

'''
def get_data(infile, nodename, name):
	logshadow_in = "python logshadow.py " + infile + " " + nodename + " " + name + "_tor_fmt.log"
	subprocess.call(logshadow_in, shell=True)
	logparse_in = "python logparse.py " + name + "_tor_fmt.log " + name + "_parsed.pickle"
	subprocess.call(logparse_in, shell=True)
	window_in = "python window.py " + name + "_parsed.pickle " + name + "_windowed.pickle 5000"
	subprocess.call(window_in, shell=True)
	trim_in = "python trim_series.py " + name + "_windowed.pickle " + name + "_trimmed_good.pickle " + name + "_trimmed_bad.pickle"
	subprocess.call(trim_in, shell=True)

'''
	Runs visualization code
		Syntax: python post_processing -visualizations graphing_mode shortname
	@param graphing_mode: the plot wanted (-summarize, -horizon, -colorplots, -allPlots)
	@param name: a string in the format nodename_numclients (ex: rm2_50)
'''
def run_visualizations(graphing_mode, name):
	filename = name + "_trimmed_good.pickle"
	if graphing_mode  == "-summarize":
		sum_in = "python exploratory.py -summarize " + filename + " O"
		subprocess.call(sum_in, shell=True)
	elif graphing_mode == "-horizon":
		horizon_in = "python exploratory.py -horizon " + filename + " O 50"
		subprocess.call(horizon_in, shell=True)
	elif graphing_mode == "-colorplots":
		colorplots_in = "python exploratory.py -colorplots " + filename + " O 50"
		subprocess.call(colorplots_in, shell=True)
	elif graphing_mode == "-allPlots":
		print "\nPlotting Summary Plots..."
		run_visualizations("-summarize", name)
		print "\nPlotting Horizon Plot..."
		run_visualizations("-horizon", name)
		print "\nPlotting Color Plot..."
		run_visualizations("-colorplots", name)
	else:
		print "ERROR: Invalid graphing mode selected"

'''
	Runs visualization code which outputs time plots for a specific client
	@param typeclient: name of the client wanted
		(web, bulk, perfclient50k, perfclient1m, perclient5m, -allClients)
	@param name: a string in the format nodename_numclients (ex: rm2_50)
	@param ts_ident: identifier of the single series to view, in the format 'circ_id,ip_slug'.
'''
def time_plot_client(type_client, name, ts_ident):
	filename = name + "_trimmed_good.pickle"

	if type_client == "-allClients":
		print "\nPlotting WebClients..."
		time_plot_client('web', name, ts_ident.get('web'))
		print "\nPlotting BulkClients..."
		time_plot_client('bulk', name, ts_ident.get('bulk'))
		print "\nPlotting PerfClients50KiB..."
		time_plot_client('perf50k', name, ts_ident.get('perf50k'))
		print "\nPlotting PerfClients1MiB..."
		time_plot_client('perf1m', name, ts_ident.get('perf1m'))
		print "\nPlotting PerfClients5MiB..."
		time_plot_client('perf5m', name, ts_ident.get('perf5m'))
	else:
		timeplot_in = "python exploratory.py -timeplot " + filename + " O 50 " + ts_ident
		subprocess.call(timeplot_in, shell=True)


if __name__ == "__main__":
	command = sys.argv[1]
	if command == "-getData":
		infile = sys.argv[2]  # a scallion.log
		nodename = sys.argv[3] # a node/relay name
		name = sys.argv[4] # name in the format nodename_numclients (ex: rm2_50)
		get_data(infile, nodename, name)

	elif command == "-visualizations":
		graphing_mode = sys.argv[2]
		name = sys.argv[3] # name in the format nodename_numclients
		run_visualizations(graphing_mode, name)

	elif command == "-clientSeries":
		infile = sys.argv[2] # a scallion.log
		nodename = sys.argv[3]
		type_client = sys.argv[4] # web, bulk, perfclient1m, perfclient5m, perfclient50, -allClients
		num_graphs = int(sys.argv[5]) # number of graphs wanted
		name = sys.argv[6]

		ident_list = timeplot_clients.get_ident_list(name + "_trimmed_good.pickle")
		circ_name_map = timeplot_clients.circuit_client_map(infile, nodename, ident_list)

		# allClients for type_client will return a dict of all clients
		ts_ident = timeplot_clients.input_timeplot_clients(circ_name_map, ident_list, type_client, num_graphs)
		time_plot_client(type_client, name, ts_ident)

	else:
		print "Invalid command"









