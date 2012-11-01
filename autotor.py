import os,shutil,time,socket,random,pickle,math
import subprocess as sub
import datetime as dt
#import numpy as np

from TorCtl import TorCtl,PathSupport

# the Router class lets us start and stop Tor processes
# easily. processes started as Router objects are meant
# to be non-public and for testing only. config options
# are set using command-line args when the tor process
# is started rather than by a torrc file, for easy
# configurability.
class Router(object):
    number = 0
    routers = []
    def __init__(self):
        # by default, each router is assigned a unique number when
        # started. this number is used to assign the router unique
        # routing, proxy, and control ports, as well as a unique name.
        # this means that more than 9 routers will cause problems...
        Router.number += 1
        self.number = Router.number
        Router.routers.append(self)
        self.socksport = int('70%d0' % self.number)
        self.orport = int('700%d' % self.number)
        # we store logs/data for each router in the 'routers' directory
        self.path = 'routers/tr%d/' % self.number
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        self.nickname = 'tr%d' % self.number
        self.options = self.generate_options()
        self.running = False
        self.process = None
        self.conn = None
        self.log = None
        self.use_stdout = False
        self.log_all = False
        # the name of the default binary to use for invoking tor
        # for thesis purposes, 'hack_tor' is symlinked to a modified
        # version of tor that logs additional information.
        self.tor = 'hack_tor'
        self.circuits = []
    # the options to be passed to Tor. we do not use a torrc file.
    def generate_options(self):
        return {
            'SocksPort':self.socksport,
            'SocksBindAddress':'127.0.0.1',
            'DataDirectory':self.path,
            'ControlPort':self.socksport+1,
            'Nickname':self.nickname,
            'PublishServerDescriptor':0,
            'ORPort':self.orport,
            'ExitPolicy':'accept *:*',
            '__DisablePredictedCircuits':1,
            '__LeaveStreamsUnattached':1,
            'EnforceDistinctSubnets':0,
            'UseEntryGuards':0,
            'NewCircuitPeriod':2**30,
            'MaxCircuitDirtiness':2**30,
            'MaxOnionsPending':0,
            'SafeLogging':0,
            'Log':'info stdout',
            }
    # transforms the currently-set options to arguments to be passed to tor
    def args(self):
        args = [self.tor]
        for key,val in self.options.items():
            args.append(key)
            if ' ' in args: args.append('"'+str(val)+'"')
            else:           args.append(str(val))
        return args
    # starts the router process
    def start(self):
        if self.process:
            print "router %d is already running" % self.number
        else:
            print "starting router %d" % self.number
            if self.use_stdout:
                self.process = sub.Popen(self.args())
            else:
                self.log = open(os.getcwd()+'/'+self.path+'log.log','w')
                self.process = sub.Popen(self.args(),stdin=None,stdout=self.log,stderr=sub.STDOUT)
    # stops the router process
    def stop(self):
        if self.process:
            print "stopping router %d" % self.number
            self.process.terminate()
            self.process = None
            if self.log:
                self.log.close()
        else:
            print "router %d isn't running" % self.number
    # true if there's a running tor process
    def is_running(self):
        self.process and self.process.poll() == None
    # gets a list of the current circuits using TorCtl
    def get_circuits(self):
        c = self.get_control_conn()
        return c.get_info('circuit-status').values()[0].split('\n')
    # pretty-prints a list of the current circuits
    def print_circuits(self):
        for c in self.get_circuits(): print c
    # gets a list of the current streams using TorCtl
    def get_streams(self,status=None):
        c = self.get_control_conn()
        streams = c.get_info('stream-status').values()[0].split('\n')
        split = [tuple(s.split(' ')) for s in streams if s != '']
        if status == None:
            return split
        else:
            return [s for s in split if s[1].lower() == status.lower()]
    # returns a list of streams which are unassigned to circuits
    def new_stream_ids(self):
        return [int(stream[0]) for stream in self.get_streams(status='new')]
    # returns the id of the first available circuit
    def current_circuit_id(self):
        if len(self.circuits) > 0: return self.circuits[-1]
        else:                      return None
    # attaches any new streams to the first available circuit
    # returns True if streams all attached successfully, False otherwise
    def attach_streams(self):
        c = self.get_control_conn()
        attached = False
        circ_id = self.current_circuit_id()[0]
        if circ_id:
            for stream_id in self.new_stream_ids():
                c.attach_stream(stream_id,int(circ_id))
                attached = True
        return attached
    # builds a circuit given an arbitrary-length list of routers
    def build_circuit(self,*routers):
        names = [r.nickname for r in routers]
        self.add_descriptors(*routers)
        circid = self.get_control_conn().extend_circuit(circid=0,hops=names)
        self.circuits.append((int(circid),names))
    # builds a length-3 circuit with a random middle router
    def build_rand_circuit(self,entry,exit,middle=False):
        c = self.get_control_conn()
        if entry != 'WesCSTor': self.add_descriptors(entry,exit)
        else: self.add_descriptors(exit)
        ns = c.get_network_status()
        if not middle:
            sns = [n for n in ns if n.nickname not in set(['tr1','tr2','tr3','tr4','tr5','tr6','tr7','tr8','tr9'])]
            chosen = random.choice(sns)
        else:
            chosen = [n for n in ns if n.nickname == 'WesCSTor'][0]
        if entry == 'WesCSTor':
            entry = [n for n in ns if n.nickname == 'WesCSTor'][0]
        #print 'Chose random middle router:',chosen.nickname,chosen.orhash
        names = [entry.nickname,chosen.idhex,exit.nickname]
        print 'Building circuit:',entry.nickname,'->',chosen.nickname,'->',exit.nickname
        circid = self.get_control_conn().extend_circuit(circid=0,hops=names)
        self.circuits.append((int(circid),names))
    # gets a TorCtl.PathSupport.Connection for the router, allowing
    # us to communicate/control the router using TorCtl
    # will either create a new connection or return an existing live one
    def get_control_conn(self):
        if not (self.conn and self.conn.is_live()):
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect(('127.0.0.1',self.socksport+1))
            self.conn = PathSupport.Connection(s)
            # we're assuming the router doesn't have a passphrase
            self.conn.authenticate('')
        return self.conn
    # adds the descriptor from another router to this router,
    # allowing us to use it in circuits/refer to it by name
    def add_descriptor(self,router):
        c1 = self.get_control_conn()
        c2 = router.get_control_conn()
        key = 'desc/name/%s' % router.nickname
        print 'adding descriptor for',router.nickname,'to',self.nickname
        desc = c2.get_info(key)[key]
        c1.post_descriptor(desc)
    # add descriptors from many routers to this router
    def add_descriptors(self,*routers):
        for router in routers:
            self.add_descriptor(router)

# convenience functions to start/stop all of the routers in a list.
def start(routers):
    map(Router.start,routers)
def stop(routers):
    map(Router.stop,routers)

def save_consensus(filename):
    f = open(filename,'w')
    r = Router()
    r.start()
    ns = r.get_control_conn().get_network_status()
    r.stop()
    pickle.dump(ns,f)

def test(n=3):
    rs = [Router() for i in range(n+1)]
    [r.start() for r in rs]
    print 'waiting for routers to start...'
    time.sleep(5)
    print 'routers started'
    rs[0].build_circuit(*rs[1:])
    return rs
def test_remote():
    rs = [Router() for i in range(3)]
    [r.start() for r in rs]
    print 'waiting for routers to start...'
    time.sleep(5)
    print 'routers started'
    rs[0].build_rand_circuit(rs[1],rs[2])
    return rs

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
    def __init__(self,filename):
        self.circs = {}
        f = open(filename,'r')
        lf = LogFile()
        i = 0;
        for line in f:
            i += 1
            if i % 50000 == 0: print i
            if line[27:31] == 'RRC:':
                split = line.split(' ')
                time = ' '.join(split[0:3])
                src_addr,dst_addr = split[5],split[7]
                circ = ' '.join(split[-3:])[1:-1]
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

def avg(l):
    return sum(l)/float(len(l))

# implements the time-series correlation algorithm described in Levine et al.
# NOTE: is undefined when len(ts1)==len(ts2)==1. possible solution: pre+appending
# a zero to every sequence.
# NOTE: right now we're assuming things start at the same time. need to examine
# the paper and see if that's what d=0 (delay) means, or if we're supposed to
# compare things happening at the same ACTUAL time rather than relative time instead.
def levine_correlation(ts1,ts2,**kwargs):
    b1,b2 = ts1.bucketize(**kwargs),ts2.bucketize(**kwargs)
    length = max(len(b1),len(b2))
    # zero-pad sequences to be the same length
    if length == len(b1) and length != len(b2):
        b2 += [0] * (length - len(b2))
    elif length == len(b2):
        b1 += [0] * (length - len(b1))
    # double-check that sequences are now the same length
    if len(b1) != len(b2): raise Exception("Corrected sequences are not the same length!")
    # pad with one zero on either side to prevent issues with length-1 sequences
    b1 = [0]+b1+[0]
    b2 = [0]+b2+[0]
    length += 2
    topsum = 0
    bsum_l = 0
    bsum_r = 0
    avg1,avg2 = avg(b1),avg(b2)
    for i in range(length):
        a = b1[i] - avg1
        b = b2[i] - avg2
        topsum += a*b
        bsum_l += a**2
        bsum_r += b**2
    return topsum / (math.sqrt(bsum_l) * math.sqrt(bsum_r))

# pickles+dumps two logfile objects. convenience function.
def save_logs(r1,r2,folder='logs/'):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    logs = [LogFile(r1),LogFile(r2)]
    f = open(folder+str(int(time.time()))+'.log','w')
    pickle.dump(logs,f)
    f.close()

# runs a single trial.
def run_single_safe(traffic=None,local=False,entry=False,small=False,middle=False):
    print "\n\nStarting single trial"
    rs = [Router() for i in range(3 if not local else 4)]
    try:
        start(rs)
        time.sleep(5)
        if not local:
            if not entry:
                if not middle:
                    rs[0].build_rand_circuit(rs[1],rs[2])
                else:
                    rs[0].build_rand_circuit(rs[1],rs[2],middle='WesCSTor')
            else: rs[0].build_rand_circuit('WesCSTor',rs[2])
        else:
            rs[0].build_circuit(*rs[1:])
        time.sleep(10 if not local else 5)
        if traffic == 'echo': # use nodejs ping client/server
            proc = sub.Popen(['proxychains','node','/home/sdefabbiakan/thesis/ping.js','client','40123','69.164.213.224','200','30000'])
        else: # default to a simple file download
            if not small:
                proc = sub.Popen(['proxychains','wget','http://69.164.213.224/tmp/rf1mb'],cwd='/home/sdefabbiakan')
            else:
                proc = sub.Popen(['proxychains','wget','http://69.164.213.224/tmp/rf10kb'],cwd='/home/sdefabbiakan')
        time.sleep(1)
        if not rs[0].attach_streams(): raise Exception("No streams to attach")
        while proc.poll() == None:
            time.sleep(1)
        stop(rs)
        save_logs(rs[1],rs[2 if not local else 3])
        print "\nTrial finished successfully\n\n"
        return True
    except Exception as e:
        print "\n\nError Occurred:",e,"\n\n"
        print "Attempting to stop routers..."
        stop(rs)
        print "Waiting for any running processes to finish..."
        # proxychains may retry for up to 5 seconds
        time.sleep(5)
        print "Killing any remaining router processes..."
        sub.call(['killall','-9','hack_tor'])
        time.sleep(1)
        print "Continuing with next trial\n\n"
        return False

def load_logs(directory='',prefix='logs/'):
    count = 0
    entry_logs = []
    exit_logs  = []
    for filename in os.listdir(prefix+directory):
        if filename.endswith('.log'):
            count += 1
            if count % 50 == 0: print count
            l1,l2 = pickle.load(open(prefix+directory+'/'+filename))
            entry_logs.append(l1)
            exit_logs.append(l2)
    return entry_logs,exit_logs

def filter_out(logs,**kwargs):
    return [log.filter(direc=DIR_OUT,**kwargs) for log in logs]
def filter_in(logs,**kwargs):
    return [log.filter(direc=DIR_IN,**kwargs) for log in logs]

def filter_good_echo(entry_logs,exit_logs):
    entry_ts = filter_out(entry_logs,prune=2)
    exit_ts  = filter_out(exit_logs)
    # filter out anything that doesn't have enough packets--indicates errors occurred
    good_entry_ts = []
    good_exit_ts  = []
    for i in range(len(entry_ts)):
        if len(entry_ts[i]) == len(exit_ts[i]) == 155:
            good_entry_ts.append(entry_ts[i])
            good_exit_ts.append(exit_ts[i])
    return good_entry_ts,good_exit_ts

def filter_good_dl(entry_logs,exit_logs):
    entry_ts = filter_in(entry_logs,prune=2)
    exit_ts  = filter_in(exit_logs)
    # filter out anything that doesn't have enough packets--indicates errors occurred
    good_entry_ts = []
    good_exit_ts  = []
    for i in range(len(entry_ts)):
        if len(entry_ts[i]) == len(exit_ts[i]) > 2000:
            good_entry_ts.append(entry_ts[i])
            good_exit_ts.append(exit_ts[i])
    return good_entry_ts,good_exit_ts

def get_jitter(ts):
    j = []
    for e in ts: j += e.intervals()
    return j

def jitter_plot(entry_ts,exit_ts,plt,exp="Control",**kwargs):
    bins = range(5,400,10)
    ent_jitter = get_jitter(entry_ts)
    ext_jitter = get_jitter(exit_ts)
    ent_txt = "ICD\nmin: %d\nmax: %d\navg: %.2f\nstd dev: %.2f" % (min(ent_jitter),max(ent_jitter),avg(ent_jitter),np.std(ent_jitter))
    ext_txt = "ICD\nmin: %d\nmax: %d\navg: %.2f\nstd dev: %.2f" % (min(ext_jitter),max(ext_jitter),avg(ext_jitter),np.std(ext_jitter))


    plot1 = hist_to_percent_bar(plt,ext_jitter,bins=39,range=(5,395))
    plot2 = hist_to_percent_bar(plt,ent_jitter,bins=39,range=(5,395))

    sp1 = plt.subplot(212)
    sp2 = plt.subplot(211)

    sp1.set_title("ICD at Exit")
    sp2.set_title("ICD at Entry")
    sp1.set_xlabel("Inter-Cell Delay (ms)")
    sp1.set_ylabel("Percent of Circuits")
    sp2.set_ylabel("Percent of Circuits")

    sp1.bar(plot1[0],plot1[1],10,color='#555555',**kwargs)
    sp2.bar(plot2[0],plot2[1],10,color='#555555',**kwargs)
    sp1.axis([0,400,0,100])
    sp2.axis([0,400,0,100])
    plt.suptitle(exp)
    sp1.text(250,35,ext_txt,ha='left',va='bottom')
    sp2.text(250,35,ent_txt,ha='left',va='bottom')

def levine_corr_plot(entry_ts,exit_ts,plt,title,bucket_size=1000,**kwargs):
    plt.clf()
    plt.xlabel("Trial Number")
    plt.ylabel("Normalized Correlation")
    plt.title(title)
    rcorrs = [levine_correlation(entry_ts[i],exit_ts[i],bucket_size=bucket_size) for i in range(len(entry_ts))]
    acorrs = [[levine_correlation(entry_ts[j],exit_ts[i],bucket_size=bucket_size) for j in range(len(entry_ts))] for i in range(len(exit_ts))]
    for i,corr in enumerate(acorrs): plt.plot([i for j in range(len(corr))],corr,'k.',alpha='0.1')
    maxes = [max(x) for x in acorrs]
    plt.plot(rcorrs,'go')
    plt.plot(maxes,'b.')
    plt.axis([0,len(entry_ts),-1,1.05])

def stretch_plot(control,exp1,exp2,plt,title,**kwargs):
    plt.clf()
    plt.xlabel("Percent Increase in Total Time")
    plt.ylabel("Count")

    percents_control = [100 * control[0][i].total_time() / float(control[1][i].total_time()) - 100 for i in range(len(control[1])) if control[1][i].total_time() > 0]
    percents_exp1 = [100 * exp1[0][i].total_time() / float(exp1[1][i].total_time()) - 100 for i in range(len(exp1[1])) if exp1[1][i].total_time() > 0]
    percents_exp2 = [100 * exp2[0][i].total_time() / float(exp2[1][i].total_time()) - 100 for i in range(len(exp2[1])) if exp2[1][i].total_time() > 0]
    bins=range(0,51,1)

    plot1 = hist_to_percent_bar(plt,percents_control,bins=25,range=(0,50))
    plot2 = hist_to_percent_bar(plt,percents_exp1,   bins=25,range=(0,50))
    plot3 = hist_to_percent_bar(plt,percents_exp2,   bins=25,range=(0,50))

    sp1 = plt.subplot(131)
    plt.title('Control')
    plt.ylabel('Percent of Circuits')
    sp2 = plt.subplot(132)
    plt.title('Experimental 1')
    plt.xlabel('Percent Increase in Time')
    sp3 = plt.subplot(133)
    plt.title('Experimental 2')

    sp1.bar(*plot1,color='#555555')
    sp2.bar(*plot2,color='#555555')
    sp3.bar(*plot3,color='#555555')
    sp1.axis([0,50,0,60])
    sp2.axis([0,50,0,60])
    sp3.axis([0,50,0,60])

def hist_to_percent_bar(plt,dists,**kwargs):
    n,bins,patches = plt.hist(dists,**kwargs)
    plt.clf()
    nlist = list(n)
    totaln = sum(nlist)
    binslist = list(bins)[:-1]
    npercent = [float(v)/totaln*100 for v in nlist]
    return binslist,npercent,binslist[1]

