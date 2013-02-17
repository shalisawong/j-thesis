import datetime as dt

# cell directions. 1 means moving towards circuit origin (the OP), 2 away.
DIR_IN  = 1
DIR_OUT = 2

# a class for parsing/extracting data from hack_tor logfiles
# when there's only one stream/circuit in the file. (hack_tor v1, now obsolete)
class LogFile(object):
    def __init__(self,router=None,triples=None):
        if router:
            f = open(router.log.name,'r')
            self.lines = f.readlines()
    # takes a time string and returns the number of milliseconds since the epoch
    def time_from_string(self,time_str):
        # time string needs a year, and the format string needs time in nanoseconds,
        # but we're getting time in in milliseconds, so add some zeroes.
        s = '2010 ' + time_str + '000'
        d = dt.datetime.strptime(s,'%Y %b %d %H:%M:%S.%f')
        # (approx) milliseconds since the epoch
        st = int(d.strftime('%s'))*1000 + (d.microsecond/1000)
        if len(str(st)) != 13: print s,d,st
        return st
    def set_times_in(self):
        self.times = []
        for line in self.lines:
            if line.contains('RCI:'):
                time_str = line[:19]
                self.times.append((self.time_from_string(time_str),None,DIR_IN))
    # returns a TimeSeries containing times that match the filters
    # direc: direction. ip: self-explanatory. prune: ignore the first N
    # cells in the series.
    def filter(self,direc=None,ip=None,prune=0):
        if type(direc) == str: direc = {'in':DIR_IN,'out':DIR_OUT}[direc]
        times = [t for t,i,d in self.times if (not direc or direc==d) and (not ip or ip==i)]
        return TimeSeries(times,prune)

def lf_set_times_in(logfile):
    logfile.times = []
    for line in logfile.lines:
        if 'RCI:' in line:
            time_str = line[:19]
            logfile.times.append((logfile.time_from_string(time_str),None,DIR_IN))

def lf_set_times_out(logfile):
    logfile.times = []
    for line in logfile.lines:
        if 'RCO:' in line:
            time_str = line[:19]
            logfile.times.append((logfile.time_from_string(time_str),None,DIR_OUT))

# a class for extracting data from hack_tor logfiles where there are
# multiple streams and multiple circuits. (hack_tor v2, needs updating)
class MultiLogFile(object):
    def __init__(self,filename, direction=DIR_OUT):
        self.circs = {}
        f = open(filename,'r')
        lf = LogFile()
        i = 0;
        dir_str =  "I" if direction == DIR_IN else "O"
        for line in f:
            i += 1
            if i % 50000 == 0: print i
            if line[29:33] == 'RRC' + dir_str:
                split = line.split(' ')
                time = ' '.join(split[0:3])
                src_addr,dst_addr = split[5],split[7]
                circ = ' '.join(split[-3:])[0:-1]
                if circ not in self.circs:
                    self.circs[circ] = {
                            'times':[lf.time_from_string(time)],
                            'src_addr':src_addr,'dst_addr':dst_addr,
                            'src_circ':int(circ[1:-1].split('->')[0]),
                            'dst_circ':int(circ[1:-1].split('->')[1])
                            }
                else:
                    self.circs[circ]['times'].append(lf.time_from_string(time))
        self.times,self.src_addrs,self.dst_addrs,self.src_circs,self.dst_circs = [],[],[],[],[]
        for val in self.circs.values():
            self.times.append(val['times'])
            self.src_addrs.append(val['src_addr'])
            self.dst_addrs.append(val['dst_addr'])
            self.src_circs.append(val['src_circ'])
            self.dst_circs.append(val['dst_circ'])

# provides some operations on lists convenient for doing time series analysis
class TimeSeries(object):
    def __init__(self,data=[],prune=0):
        # prune lets us get rid of any extraneous values
        self.times = data[prune:]
    # divide into buckets so we can do levine correlation
    # bucket size is in milliseconds
    def bucketize(self,bucket_size=1000,adj=True):
        adj_times = [t - self.times[0] for t in self.times]
        bucketized = [t/bucket_size for t in adj_times]
        buckets = sorted(bucketized)
        ts = []
        i = 0
        for b in range(buckets[-1]+1):
            ts.append(0)
            while i < len(buckets) and b == buckets[i]:
                i += 1
                ts[b] += 1
        if adj:
            return ts
        else:
            return ([0] * int((self.times[0]-1266390000000)/bucket_size)) + ts
    def intervals(self):
        return [self.times[i] - self.times[i-1] for i in range(1,len(self.times))]
    def total_time(self):
        return self.times[-1] - self.times[0]
    def __len__(self):
        return len(self.times)
