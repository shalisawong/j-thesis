from __future__ import division
import math
# we need arbitary-precision arithmetic
#from decimal import *
# and we need it to not be absurdly slow...
from bigfloat import *

def log_correlate_circuits(entry_circ,exit_circ):
    # we ignore the first entry time, because that's a cell
    # from the middle router that was part of circuit setup
    entry_times = [t[0] for t in entry_circ.cells_in][1:]
    exit_times  = [t[0] for t in exit_circ.cells_in]
    return log_correlate(entry_times,exit_times)

def log_correlate(entry_times,exit_times):
    n_y = len(entry_times)
    n_x = len(exit_times)
    n_xy = n_x + n_y

    l_y = (entry_times[-1]  - entry_times[0])
    l_xy = (max(entry_times[-1],exit_times[-1]) - min(entry_times[0],exit_times[0]))
    #if n_xy > 30000: # avoid bigfloats!
    return do_faster_log_correlation(n_y,n_xy,l_y,l_xy)
    #else:
    #    return do_log_correlation(n_y,n_xy,l_y,l_xy)

def do_log_correlation(n_y,n_xy,l_y,l_xy):
    def Gamma(n): return math.factorial(n-1)
    B = BigFloat # gets us slightly nicer formatting

    # rate part:             correction part:    length part:
    #      Gamma(n_xy)        n_y * (n_y - 1)     l_y**(n_y - 1)
    # -------------------- * ----------------- * ----------------
    # 2**n_xy * Gamma(n_y)   n_xy * (n_xy - 1)   l_xy**(n_xy - 1)

    rate_part = B(Gamma(n_xy)) / B(2**n_xy * Gamma(n_y))
    correction_part = B(n_y * (n_y - 1)) / B( n_xy * (n_xy - 1))
    length_part = B(l_y**(n_y-1)) / B(l_xy**(n_xy-1))
    return float(log10(rate_part * correction_part * length_part))

# we can go much faster by distributing the log calls
# so that we never need to go into BigInts/BigFloats.
# in particular, we go deep enough that we never do any
# multiplication, exponentiation, and never directly
# calculate Gamma, which is a factorial. this gets us
# about an order of magnitude faster.
def do_faster_log_correlation(n_y,n_xy,l_y,l_xy):
    
    # rate part:             correction part:    length part:
    #      Gamma(n_xy)        n_y * (n_y - 1)     l_y**(n_y - 1)
    # -------------------- * ----------------- * ----------------
    # 2**n_xy * Gamma(n_y)   n_xy * (n_xy - 1)   l_xy**(n_xy - 1)

    # use logs early for faster computation:
    rate_part = stirling_log_Gamma(n_xy) - (stirling_log_Gamma(n_y) + fast_log_exp(2,n_xy))
    correction_part = log_prod(n_y,n_y-1) - log_prod(n_xy,n_xy-1)
    length_part = fast_log_exp(l_y,n_y-1) - fast_log_exp(l_xy,n_xy-1)
    
    # we're returning the log_11 because this is often a ridiculously
    # large/small number, and we only care about comparing it to other
    # values, not about the exact values.
    return rate_part + correction_part + length_part

def stirling_log_Gamma(n):
    n = n-1
    return n * math.log(n,10) - n
# takes advantage of the fact that log_b(a) = log_k(a)/log_k(b)
# so log_10(n**exp) = log_n(n**exp)/log_n(10)
def fast_log_exp(n,exp):
    return exp / math.log(10,n)
def log_Gamma(n):
    return sum((math.log(x,10) for x in xrange(1,n)))
def log_exp(n,exp):
    return sum((math.log(n,10) for x in xrange(exp)))
def log_prod(a,b):
    return math.log(a,10)+math.log(b,10)
