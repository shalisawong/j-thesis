"""
Utility functions for working with sequence data.
@author: Julian Applebaum
"""

from ghmm import Float, SequenceSet, EmissionSequence

def sequenceEq(s1, s2):
	"""
	Returns true if s1 and s2 have the same observations, false otherwise
	@param s1: a ghmm.EmissionSequence
	@param s2: a ghmm.EmissionSequence
	@return: True if s1 and s2 have the same observations, false otherwise
	"""
	for i in range(0, len(s1)):
		if s1[i] != s2[i]: return False
	return True

def toSequenceSet(S, domain=Float()):
	"""
	Convert a list of sequences into a ghmm.SequenceSet
	@param S: a list of sequences as Python lists
	@return: the sequences as a ghmm.SequenceSet
	"""
	return SequenceSet(domain, S)

def toSequence(s, domain=Float()):
	"""
	Convert a sequence in list form to a ghmm.EmissionSequence
	@param: a sequence in Python list form
	@param domain: the ghmm emission domain
	@param: the sequence as a ghmm.EmissionSequence
	"""
	return EmissionSequence(domain, s)

def seqSetToList(S):
	"""
	Convert a a ghmm.SequenceSet to a list of sequences in Python list form
	@param S: a ghmm.SequenceSet
	@return: The sequences as Python lists
	"""
	return map(lambda s: list(s), S)

def flatten(lists):
	"""
	Flatten a list of lists
	@param lists: An iterable of lists, eg. [[1, 2, 3], [4, 5, 6]]
	@return: The flattened list, eg. [1, 2, 3, 4, 5, 6]
	"""
	return reduce(list.__add__, lists, [])

def trim_inactive(series):
	'''
	Edited on 8/12/14 to include ip_address
	@param series: A tuple of (time series, ip address)
	'''

	tail = len(series)
	lead_idx = 0
	trail_idx = tail
	found_nonzero = False

	for idx, obs in enumerate(series[0]):
		if obs < 2:
			if trail_idx == tail:
				trail_idx = idx
			if not found_nonzero:
				lead_idx = idx+1
		else:
			trail_idx = tail
			found_nonzero = True
	return series[lead_idx:trail_idx]



