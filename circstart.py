from __future__ import division
import cPickle
try: import matplotlib.pyplot as plt
except Exception: pass

def summarize(entry_tor):
    return {'entry':[[c.start_time() for c in entry_tor if c.is_entry],
                     [(len(c.cells_in),len(c.cells_out)) for c in entry_tor if c.is_entry]],
            'others':[[c.start_time() for c in entry_tor if not c.is_entry],
                      [(len(c.cells_in),0) for c in entry_tor if not c.is_entry]]}

def graph_start_time_distribution(summaries,scale=None,entry=True):
    if scale == None: scale = 10 if entry else 0.4
    dists = []
    for summary in summaries:
        times = summary['entry' if entry else 'others'][0]
        prev = times[0]
        for time in times[1:]:
            diff = time - prev
            prev = time
            dists.append(diff/1000)
    bin_count = 20
    l1,h1,w1 = hist_to_percent_bar(dists,bins=bin_count,range=(0,1*bin_count*scale))
    plot2 = hist_to_percent_bar(dists,bins=bin_count,range=(0,1*scale))
    plt.clf()
    sp1 = plt.subplot(211)
    plt.title('Time Distribution of '+('' if entry else 'Non-')+'Entry Circuit Creations')
    plt.ylabel('% of Circuits')
    sp2 = plt.subplot(212)
    sp1.bar(l1,h1,w1,color='#bbbbbb')
    sp1.bar(l1[0],h1[0],w1,color='#555555')
    sp2.bar(*plot2,color='#555555')
    plt.ylabel('% of Circuits')
    plt.xlabel('Seconds After Previous Circuit Formation')
    sp1.axis([0,bin_count*scale,0,40])
    sp2.axis([0,scale,0,10])

def graph_circuit_length_distribution(summaries):
    lengths_entry_in  = []
    lengths_others_in = []
    for summary in summaries:
        lengths_entry =  summary['entry'][1]
        lengths_others = summary['others'][1]
        lengths_entry_in += lengths_entry
        lengths_others_in += lengths_others

    lengths_others_in = [a for a,b in lengths_others]
    lengths_entry_in = [a for a,b in lengths_entry]
    plot1 = hist_to_percent_bar(lengths_entry_in,bins=20,range=(0,2000))
    plot2 = hist_to_percent_bar(lengths_others_in,bins=20,range=(0,2000))
    plt.clf()
    sp1 = plt.subplot(121)
    plt.title('Entry Circuits')
    plt.xlabel('Cell Count')
    plt.ylabel('% of Circuits')
    sp2 = plt.subplot(122)
    plt.title('Non-Entry Circuits')
    plt.xlabel('Cell Count')
    sp1.bar(*plot1,color='#555555')
    sp2.bar(*plot2,color='#555555')
    sp1.axis([0,2000,0,100])
    sp2.axis([0,2000,0,100])

def hist_to_percent_bar(dists,**kwargs):
    n,bins,patches = plt.hist(dists,**kwargs)
    plt.clf()
    nlist = list(n)
    totaln = sum(nlist)
    binslist = list(bins)[:-1]
    npercent = [v/totaln*100 for v in nlist]
    return binslist,npercent,binslist[1]

