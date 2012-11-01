import sys,pickle
#import numpy

import levine,bayesian,newcorr

def analyze_all(entry_tor,entry_ours,exit_ours,filename,entry_only=False):
    if entry_only:
        print 'removing non-entry circuits'
        entry_tor = filter(lambda c: c.is_entry,entry_tor)
    print 'starting analysis against',len(entry_tor),'circuits'
    print 'DOING NEWCORR'
    nc = analyze(entry_tor,entry_ours,exit_ours,newcorr.correlate_circuits)
    print 'DOING BAYESIAN'
    bayes = analyze(entry_tor,entry_ours,exit_ours,bayesian.log_correlate_circuits)
    print 'DOING LEVINE 100'
    lev_100 = analyze(entry_tor,entry_ours,exit_ours,levine.correlate_circuits,bucket_size=100)
    print 'DOING LEVINE 1000'
    lev_1000 = analyze(entry_tor,entry_ours,exit_ours,levine.correlate_circuits,bucket_size=1000)
    print 'DOING LEVINE 10000'
    lev_10000 = analyze(entry_tor,entry_ours,exit_ours,levine.correlate_circuits,bucket_size=10000)
    return {'nc':nc,'bayes':bayes,'levine':[lev_100,lev_1000,lev_10000]}


def analyze(entry_tor,entry_ours,exit_ours,corr_func,**kwargs):
    counts = []
    corrs  = []
    # for each circuit at the exit, get its corr values with every regular circuit
    # recorded at the entry, as well as with itself at the entry
    for i,circ in enumerate(exit_ours):
        print 'started',i
        correct_circ = entry_ours[i]
        correct_corr = corr_func(correct_circ,circ,**kwargs)
        other_corrs = []
        for other_circ in entry_tor:
            val = corr_func(other_circ,circ,**kwargs)
            other_corrs.append(val)
    
        better,worse = partition(other_corrs,lambda x: x >= correct_corr)
        better_count,worse_count = len(better),len(worse)
        counts.append((better_count,worse_count))
        corrs.append((correct_corr,other_corrs))
    return counts,corrs

def levine_analysis(pickled_file,**kwargs):
    entry_tor,entry_ours,exit_ours = unpickle_circs(pickled_file)
    print 'file loaded'
    return analyze(entry_tor,entry_ours,exit_ours,levine.correlate_circuits,**kwargs)
   
def bayesian_analysis(pickled_file):
    entry_tor,entry_ours,exit_ours = unpickle_circs(pickled_file)
    print 'file loaded'
    return analyze(entry_tor,entry_ours,exit_ours,bayesian.log_correlate_circuits)

def unpickle_circs(pickled_file):
    unpickled = pickle.load(open(pickled_file))
    entry_tor,entry_ours = unpickled['entry']
    exit_ours = unpickled['exit']
    return entry_tor,entry_ours,exit_ours

# partitions a list into two lists based on whether func is true or false
# for a given element.
def partition(seq,func):
    seq_t = []
    seq_f = []
    for elem in seq:
        if func(elem): seq_t.append(elem)
        else:          seq_f.append(elem)
    return seq_t,seq_f

