# graph generation + helper functions<F2>
from __future__ import division # float division by default

import cPickle

import matplotlib.pyplot as plt

# returns a pair with (partial,full) stats for 'corrs'
def corr_stats(corrs,percent=True):
    partial = len([a for a,b in corrs if a > max(b)])
    perfect_val = max([max(b) for a,b in corrs])
    perfect = len([a for a,b in corrs if a > perfect_val])
    if percent:
        return (partial/len(corrs)*100, perfect/len(corrs)*100)
    else:
        return (partial,perfect)

def draw_loaded_results(title,*vals):
    lev_100 = []
    lev_1000 = []
    lev_10000 = []
    bayes = []
    nc = []
    for val in vals:
        lev_100 += val['levine'][0][1]
        lev_1000 += val['levine'][1][1]
        lev_10000 += val['levine'][2][1]
        bayes += val['bayes'][1]
        nc += val['nc'][1]
    draw_results(title,lev_100,lev_1000,lev_10000,bayes,nc)

def draw_results(title,*methods):
    partials = []
    fulls = []
    for method in methods:
        if method == None:
            partials.append(0)
            fulls.append(0)
        else:
            cs = corr_stats(method)
            partials.append(cs[0])
            fulls.append(cs[1])

    plt.clf()
    widths = [0.3,0.3,0.3,0.97,1]
    positions = [0,0.33,0.67,1,2]
    p1 = plt.bar(positions,partials,widths,color='#bbbbbb')
    p2 = plt.bar(positions,fulls,widths,color='black')
    plt.title(title)
    plt.ylabel('Success %')
    plt.xticks([0.165,0.5,0.835,1.5,2.5],('0.1s','1s\nLevine','10s','\nBayesian','\nSimple'))
    #plt.xticks(np.arange(3)+width/2.0, ('0.1s        1s        10s\nLevine','\nBayesian','\nSimple'))
    plt.legend((p1[0],p2[0]),('Partial Success','Full Success'),loc='upper left')

def load_and_draw_results(title,group,directory='correlations/'):
    all_corrs = []
    for method in ['levine-100','levine-1000','levine-10000','bayes','newcorr']:
        try:
            with open(directory+group+'-'+method+'.pkl') as f:
                counts,corrs = cPickle.load(f)
                all_corrs.append(corrs)
        except Exception:
            all_corrs.append(None)
    draw_results(title,*all_corrs)

