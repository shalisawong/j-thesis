from pprint import pprint
from hmm_utils import tripleToHMM, compositeTriple
from sequence_utils import toSequenceSet
from random import shuffle, seed
import matplotlib.pyplot as plt
import re, sys, cPickle

def get_real_ip_addrs(scallion_file):
	ip_addrs = {}
	with open(scallion_file) as f:
		print "\nReading file..."
		#n_entries = 0
		print "Mapping clients and ip addresses..."
		for line in f:
			'''[
			n_entries += 1
			if n_entries % 50000 == 0 and n_entries != 0:
				print "%i entries processed" % n_entries

			'''
			# done in the beginning of scallion.log	
			if "Created Host" in line:

				ip = '(([0-9][0-9]?[0-9]?\\.){3}([0-9][0-9]?[0-9]?))'

				# find name and ip address of host
				try:
					name = re.search("'(.+?)'", line).group(1)
					ip_addr = re.search(ip, line).group(0)

				except AttributeError:
					print "'Created Host' found with either no host name or ip address."
					return
 
				ip_addrs[ip_addr] = name
	return ip_addrs

def ip_addrs_to_names(scallion_file, cluster_ips, pseudo_ip_dict):

	ip_addrs = get_real_ip_addrs(scallion_file)
	clusters_names = []
	for cluster in cluster_ips:
		single_cluster = []
		for ip in cluster:
			real_ip = pseudo_ip_dict.get(hex(ip)[2:])
			name = ip_addrs.get(real_ip)

			if real_ip == None:
				raise ValueError("Could not find the real IP address of " +
						"Pseudonym " + hex(ip)[2:])
			if name == None:
				raise ValueError("Could not find the real name of the " +
						"Pseudonym " + hex(ip)[2:] + "with ip " +
						"address " + real_ip)
			single_cluster.append(name)
		clusters_names.append(single_cluster)
	return clusters_names

if __name__ == "__main__":
	results_path = sys.argv[1]
	k = int(sys.argv[2])
	scallion_file = sys.argv[3]
	ip_addr_pickle = sys.argv[4]
	with open(results_path) as results_file, open(ip_addr_pickle) as ip_file:
		trial = cPickle.load(results_file)
		pseudo_ip_dict = cPickle.load(ip_file)
		print trial['rand_seed']
		pprint(trial['times'])
		model = trial['components'][k]
		print "**** Models ****"
		for triple in model['hmm_triples']:
			print tripleToHMM(triple)
		print "**** Cluster sizes ****"
		print model['cluster_sizes']
	
		cluster_names = ip_addrs_to_names(scallion_file, 
				model['cluster_ips'], pseudo_ip_dict)
		print "\n**** Clusters with names of clients ****"
		for i, cluster in enumerate(cluster_names):
			print "Cluster %d: %s\n" % (i+1, str(cluster)) 
	
		clusters_name_num = []
		for cluster in cluster_names:
			name_num_dict = {
					"webclient": 0,
					"bulkclient": 0,
					"perfclient": 0
					}
			web = 0
			bulk = 0
			perf = 0
			for name in cluster:
				if "web" in name:
					web += 1
				elif "bulk" in name:
					bulk += 1
				elif "perf" in name:
					perf += 1
			name_num_dict["webclient"] = web
			name_num_dict["bulkclient"] = bulk
			name_num_dict["perfclient"] = perf
			clusters_name_num.append(name_num_dict)
		print "\n**** Clusters with binned clients ****"
		for i, cluster in enumerate(clusters_name_num):
			print "Cluster %d: %s\n" % (i+1, str(cluster)) 

		
