# logparse is a module for parsing logs from hack_tor
import string,random,datetime,os,pickle

# faster to return a tuple and use these indices than to do dict lookup
TIME,DIRECTION,SRC_ADDR,DST_ADDR,SRC_CIRC,DST_CIRC = 0,1,2,3,4,5
# in means towards origin (OP), out means away from origin
DIR_IN,DIR_OUT = 1,2
KURTZ_ADDR = '129.133.8.19'

test_line = "Mar 27 02:13:36.561 [info] RRCI: 46.4.237.146 -> 129.133.8.19 (51747 -> 31703)"

# separates out the parts of a single relevant line in the logfile
def parse_line(line):
    time = parse_time(line[:19])
    direction = DIR_IN if line[30] == 'I' else DIR_OUT
    split = line.strip().split(' ')
    src_addr = split[5]
    dst_addr = split[7]
    src_circ = split[8][1:]
    dst_circ = split[10][:-1]

    # then our sources/dests are backwards in the logs...
    if not (dst_addr == 'EDGE' or dst_addr == 'END'):
        src_addr,dst_addr = dst_addr,src_addr
        src_circ,dst_circ = dst_circ,src_circ
    
    return time,direction,src_addr,dst_addr,src_circ,dst_circ

# takes a time string and returns the number of milliseconds since the epoch
def parse_time(time_str):
    # time string needs a year, and the format string needs time in nanoseconds,
    # but the time string is in milliseconds, so add some zeroes.
    s = '2010 ' + time_str + '000'
    d = datetime.datetime.strptime(s,'%Y %b %d %H:%M:%S.%f')
    # (approx) milliseconds since the epoch
    st = int(d.strftime('%s'))*1000 + (d.microsecond/1000)
    if len(str(st)) != 13: print s,d,st
    return st

# we replace addresses (that aren't kurtz) with random strings
# for privacy purposes. this keeps track of which random strings
# correspond to which addresses. uses a closure to keep track
# of necessary state, since we don't need/want to know those
# values outside of the replacement function.
def replace_func():
    # we don't want to repeat random strings
    used_strings = set(['kurtz','KURTZ','edge','EDGE','end','END'])
    mapping = {KURTZ_ADDR:'KURTZ','EDGE':'EDGE','END':'EDGE'}

    def _unique_random_str():
        def _rand_str():
            return ''.join(random.choice(string.lowercase) for i in range(5))
        while True:
            rs = _rand_str()
            if rs not in used_strings:
                return rs

    def _replace_addresses(split):
        rs1,rs2 = _unique_random_str(),_unique_random_str()
        src = mapping.setdefault(split[2],rs1)
        dst = mapping.setdefault(split[3],rs2)
        if src == rs1: used_strings.add(rs1)
        if dst == rs2: used_strings.add(rs2)

        return split[0],split[1],src,dst,split[4],split[5]
    return _replace_addresses
replace_addresses = replace_func()

# lazily filters lines in a logfile to determine if they're relevant,
# and replaces IP addresses with random strings (identical addresses
# get replaced with identical strings, length 5, lowercase letters)
def filter_log(filename,pickled=False,consensus=set()):
    if not pickled: f = open(filename)
    else:           f = pickle.load(open(filename))[1].lines

    i = 0
    for line in f:
        if line[28:30] == 'RC':
            if i % 50000 == 0: print i
            i += 1
            try:
                split = parse_line(line)
                if split[SRC_ADDR] not in consensus:
                    yield [replace_addresses(split),'entry']
                else:
                    yield [replace_addresses(split)]
            except Exception:
                raise

# takes a logfile and returns a list of all of the circuits in that
# logfile, in order of appearance in the file
def partition_log(filename,**kwargs):
    circuits = {}
    circuits_list = []
    for val in filter_log(filename,**kwargs):
        line = val[0]
        pair = (line[SRC_CIRC],line[DST_CIRC])
        if pair not in circuits:
            circ = Circuit(line[SRC_ADDR],line[DST_ADDR],
                           line[SRC_CIRC],line[DST_CIRC],
                           is_entry=(True if len(val) > 1 else False))
            circuits[pair] = circ
            circuits_list.append(circ)
        circuits[pair].add_cell(line[TIME],line[DIRECTION])
    return circuits_list

def partition_all(directory,**kwargs):
    circs = []
    for f in os.listdir(directory): circs += partition_log(directory+f,**kwargs)
    return sorted(circs,key=Circuit.start_time)

def get_circs(filename,is_directory=False,**kwargs):
    if is_directory: return partition_all(filename,pickled=True)
    else:
        circs = sorted(partition_log(filename,**kwargs),key=Circuit.start_time)
        our_circs = list(filters(circs,Circuit.long_enough,Circuit.inward,Circuit.from_kurtz))
        tor_circs = list(filters(circs,Circuit.long_enough,Circuit.inward,Circuit.from_tor))
        if len(our_circs) > 0: return tor_circs,our_circs
        else:                  return tor_circs

# contains the recorded data from a single identifiable "circuit"
# circuits are identified by the (src_circ,dst_circ) pair of
# circuit ids used by the tor router.
class Circuit(object):
    def __init__(self,src_addr,dst_addr,src_circ,dst_circ,is_entry=False):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.src_circ = src_circ
        self.dst_circ = dst_circ
        self.is_entry = is_entry
        self.pair = (src_addr,self.dst_addr)
        self.cells = []
        self.cells_in = []
        self.cells_out = []
    def get_times_in(self):
        return [t for t,d in self.cells_in]
    def get_times_out(self):
        return [t for t,d in self.cells_out]
    def get_times(self):
        return [t for t,d in self.cells]
    def add_cell(self,time,direction):
        cell = (time,direction)
        self.cells.append(cell)
        if direction == DIR_IN: self.cells_in.append(cell)
        else:                   self.cells_out.append(cell)
    def start_time(self,direction=None):
        return self.get_cells(direction)[0][0]
    def end_time(self,direction=None):
        return self.get_cells(direction)[-1][0]
    def get_cells(self,direction=None):
        if direction == DIR_IN:    return self.cells_in
        elif direction == DIR_OUT: return self.cells_out
        else:                      return self.cells
    def __len__(self):
        return len(self.cells)
    def same(self):
        return self.src_circ == self.dst_circ
    def not_same(self): return not self.same()
    def outward(self):
        return self.src_circ == self.dst_circ and len(self.cells_out) > 0
    def inward(self): return not self.outward()
    def very_short(self):
        return len(self.cells) <= 2
    def long_enough(self): return not self.very_short()
    def matches(self,other):
        return (self.src_circ == other.src_circ and
                self.src_addr == other.src_addr and
                self.dst_addr == other.dst_addr)
    def at_end(self):
        return self.dst_addr == 'EDGE' or self.dst_addr == 'END'
    def not_at_end(self): return not self.at_end()
    def from_kurtz(self):
        return self.src_addr == 'KURTZ'
    def from_tor(self): return not self.from_kurtz()

# a filter that can take multiple filtering functions
# note: argument order is switched from standard python filter
def filters(seq,*funcs):
    for elem in seq:
        valid = True
        for func in funcs:
            if not func(elem):
                valid = False
                break
        if valid: yield elem

# returns a set of the ips of all of the routers in all
# of the consensus files in a given directory
def consensus_gen(directory):
    if directory[-1] != '/': directory += '/'
    router_addrs = set()
    count = 0
    for filename in os.listdir(directory):
        path = directory + filename
        with open(path) as f:
            for line in f:
                count += 1
                if line[0] == 'r':
                    try: router_addrs.add(line.split()[-3])
                    except Exception: pass
    print count
    return router_addrs


