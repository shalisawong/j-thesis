"""
Utility functions for clustering.
@author: Julian Applebaum
"""

def partition(S, labels):
	"""
	Given a set of cluster labels, partition S into clusters. Works for any
	labeling scheme.
	@param S: a list of sequences
	@param labels: cluster labels for S
	@return: A list of lists, each of which contains the series from one cluster
	"""

    ## ND:  Is there a reason to use a dictionary here instead of directly
    ## computing the list of clusters?  I.e.,
    ## n_labels = len(set(labels))
    ## clusters = [[] for i in xrange(n_labels)]
    ## for i in xrange(n_labels):
    ##     clusters[label[i]].append(S[i])
    ## return clusters

	clust_ids = set(labels)
	clusters = dict(zip(clust_ids, [[] for i in xrange(0, len(clust_ids))]))
	for i in xrange(0, len(labels)):
		clusters[labels[i]].append(S[i])
	return clusters.values()
