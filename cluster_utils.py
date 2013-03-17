def partition(X, k, labels):
	clusters = [[] for i in range(0, k)]
	for i in xrange(0, len(labels)):
		clusters[labels[i]-1].append(X[i])
	return clusters
