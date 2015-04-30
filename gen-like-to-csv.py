'''
Given a directory and outfile name, compiles the results of generation of
likelihood into one csv file.
This assumes the results are stored  with "-gen-like" in their filename.
@author Shalisa Pattarawuttiwong
'''
import os, csv, cPickle

if __name__ == "__main__":
	main_d = sys.argv[1] # directory of
	outfile = sys.argv[2] # outfile name	

	with open(outfile,"wb") as csvfile:
		csvwriter = csv.writer(csvfile, delimiter=',')
		# write out headers
		csvwriter.writerow(["","","Number of clusters",2,3,4,5,6,7,8,9,10])
		csvwriter.writerow(["Clustering Algorithm","Distance Function", "Number of states"])
		#main_d = "./data/shadow-500r-1800c/1"
		numFiles = 0
		for file_name in os.listdir(main_d):
			if "-gen-like" in file_name:
				file_path = main_d + "/" +file_name
				print ("\nPROCESSING: " + file_path)
				numFiles += 1
				with open(file_path) as results_file:
					results = cPickle.load(results_file)
					#print results
					#(k, target_m, rand_seed, likelihood)
					cluster_alg = ""
					dist_fun = ""
					if "hier" in file_name:
						if "wavg" in file_name:
							cluster_alg = "hierarchical weighted average"
						elif "avg" in file_name:
							cluster_alg = "hierarchical average"
						elif "cent" in file_name:
							cluster_alg = "hierarchical centroid"
						elif "comp" in file_name:
							cluster_alg = "hierarchical complete"
						elif "med" in file_name:
							cluster_alg = "hierarchical median"
						elif "single" in file_name:
							cluster_alg = "hierarchical single"
						elif "ward" in file_name:
							cluster_alg = "hierarchical ward"
						else: print "AGGLOMERATION METHOD NOT RECOGNIZED"
					elif "kmeans" in file_name:
						cluster_alg = "kmeans"
					elif "kmedoids" in file_name:
						cluster_alg = "kmedoids"
					else: print "CLUSTERING ALGORITHM NOT RECOGNIZED"

					if "euc" in file_name:
						dist_fun = "euclidean"
					elif "edit" in file_name:
						dist_fun = "edit"
					elif "man" in file_name:
						dist_fun = "manhattan"
					else: print "DISTANCE FUNCTION NOT RECOGNIZED"

					# assuming k always stored in an increasing manner
					print cluster_alg, dist_fun
					m_counter = results[0][1]
					k_like_lst = []
					for tup in results:
						print m_counter
						if m_counter != tup[1]:
							writeOut = ([cluster_alg,dist_fun,m_counter] + k_like_lst)
							csvwriter.writerow(writeOut)
							m_counter = tup[1]
							k_like_lst = []
						k_like_lst.append(tup[3])

					writeOut = [cluster_alg,dist_fun,m_counter] + k_like_lst
					csvwriter.writerow(writeOut)
		print numFiles, "files processed"
