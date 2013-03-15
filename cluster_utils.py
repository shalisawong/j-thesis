from ghmm import SequenceSet, Float
from fastcluster import linkage
from scipy.cluster.hierarchy import fcluster

def clusterFromDMatrix(S, k, dmatrix):
	"""
	Given a distance matrix dmatrix, partition the sequences in S into
	k clusters via hierarchical, complete linkage clustering.
	"""
	clustering = linkage(dmatrix, method='complete', preserve_input=False)
	assignments = fcluster(clustering, k, 'maxclust')
	clusters = [[] for i in range(0, k)]
	for i in xrange(0, len(assignments)):
		clusters[assignments[i]-1].append(S[i])

	return clusters
