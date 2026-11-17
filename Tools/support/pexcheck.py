"""Independent Skyrim PEX decoder and small test interpreter.

This is a mock Papyrus VM, not Skyrim: native game calls are supplied by tests.
Reads the actual compiled instructions, not a translated copy of the controller.
"""
import struct
from pathlib import Path

COUNTS = [0,3,3,3,3,3,3,3,3,3,2,2,2,2,2,3,3,3,3,3,1,2,2,3,2,3,1,3,3,3,2,2,3,3,4,4]

class Pex:
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        self.pos = 0
        self.endian = '>'
        assert self.take(4) == bytes.fromhex('fa57c0de'), 'Skyrim big-endian PEX magic'
        self.version = (self.num('B'), self.num('B'))
        assert self.version in [(3,1),(3,2)]
        assert self.num('H') == 1, 'Skyrim game ID'
        self.num('Q')
        self.source, self.user, self.computer = self.string(), self.string(), self.string()
        self.strings = [self.string() for _ in range(self.num('H'))]
        if self.num('B'):
            self.num('Q')
            for _ in range(self.num('H')):
                self.sid(); self.sid(); self.sid(); self.num('B')
                self.take(self.num('H') * 2)
        self.flags = {self.sid():self.num('B') for _ in range(self.num('H'))}
        self.objects = []
        for _ in range(self.num('H')):
            name = self.sid(); length = self.num('I'); end = self.pos + length - 4
            parent, doc, flags, state = self.sid(), self.sid(), self.num('I'), self.sid()
            variables = {}
            for _ in range(self.num('H')):
                vn, vt, vf, vv = self.sid(), self.sid(), self.num('I'), self.value()
                variables[vn.lower()] = (vt.lower(), vv[1])
            properties = {}
            for _ in range(self.num('H')):
                pn, pt, pd, pf, bits = self.sid(), self.sid(), self.sid(), self.num('I'), self.num('B')
                assert bits & 4, 'Only auto properties expected'
                properties[pn.lower()] = (pt.lower(), self.sid().lower())
            functions = {}
            for _ in range(self.num('H')):
                sn = self.sid()
                for _ in range(self.num('H')):
                    fn = self.sid()
                    functions[fn.lower()] = self.function()
            assert self.pos == end, (self.pos, end)
            self.objects.append(dict(name=name,parent=parent,variables=variables,properties=properties,functions=functions))
        assert self.pos == len(self.raw), 'Trailing/undecoded PEX bytes'
        assert len(self.objects) == 1
        self.obj = self.objects[0]

    def take(self,n):
        out=self.raw[self.pos:self.pos+n]; assert len(out)==n
        self.pos+=n; return out
    def num(self,fmt):
        return struct.unpack(self.endian+fmt,self.take(struct.calcsize(fmt)))[0]
    def string(self): return self.take(self.num('H')).decode('utf-8')
    def sid(self): return self.strings[self.num('H')]
    def value(self):
        t=self.num('B')
        if t==0:return (0,None)
        if t in (1,2):return (t,self.sid())
        if t==3:return (t,self.num('i'))
        if t==4:return (t,self.num('f'))
        if t==5:return (t,bool(self.num('B')))
        raise AssertionError(('bad value type',t))
    def function(self):
        ret,doc,flags,kind=self.sid(),self.sid(),self.num('I'),self.num('B')
        params=[(self.sid().lower(),self.sid().lower()) for _ in range(self.num('H'))]
        locals_=[(self.sid().lower(),self.sid().lower()) for _ in range(self.num('H'))]
        ins=[]
        for _ in range(self.num('H')):
            op=self.num('B'); assert op < len(COUNTS), ('non-Skyrim opcode',op)
            args=[self.value() for _ in range(COUNTS[op])]
            va=[]
            if op in (23,24,25):
                count=self.value(); assert count[0]==3
                va=[self.value() for _ in range(count[1])]
            ins.append((op,args,va))
        for pc,(op,a,va) in enumerate(ins):
            if op in (20,21,22):
                j=a[0] if op==20 else a[1]
                assert j[0]==3 and 0<=pc+j[1]<=len(ins), ('branch target out of range',pc,j,len(ins))
        return dict(ret=ret.lower(),params=params,locals=locals_,ins=ins,native=bool(kind&2))

def f32(v): return struct.unpack('f',struct.pack('f',float(v)))[0]
def default(t):
    if t=='int':return 0
    if t=='float':return 0.0
    if t=='bool':return False
    if t=='string':return ''
    return None

class VM:
    def __init__(self, pex, native):
        self.obj=pex.obj; self.native=native
        self.vars={k:v[1] for k,v in self.obj['variables'].items()}
        self.types={k:v[0] for k,v in self.obj['variables'].items()}
        self.executed=0
    def property(self,name,value):
        self.vars[self.obj['properties'][name.lower()][1]]=value
    def call(self,name,*params):
        fn=self.obj['functions'][name.lower()]
        assert not fn['native']
        local={k:default(t) for k,t in fn['params']+fn['locals']}
        local.update(dict(zip([k for k,t in fn['params']],params)))
        types=dict(fn['params']+fn['locals'])
        def get(v):
            t,x=v
            if t!=1:return x
            k=x.lower()
            if k=='self':return self
            if k in local:return local[k]
            if k in self.vars:return self.vars[k]
            raise AssertionError(('unknown variable',k))
        def put(v,value):
            assert v[0]==1
            k=v[1].lower()
            if k in self.vars:self.vars[k]=value
            else:local[k]=value
        pc=0;steps=0
        while pc<len(fn['ins']):
            steps+=1;self.executed+=1
            assert steps<100000,'loop exceeded bound'
            op,a,va=fn['ins'][pc]; nxt=pc+1
            if op==0:pass
            elif op in (1,2,3,4,5,6,7,8,9):
                x,y=get(a[1]),get(a[2])
                if op in (1,2):z=x+y
                elif op in (3,4):z=x-y
                elif op in (5,6):z=x*y
                elif op==7:z=int(x/y)
                elif op==8:z=x/y
                else:z=x-int(x/y)*y
                put(a[0],f32(z) if op in (2,4,6,8) else z)
            elif op==10:put(a[0],not get(a[1]))
            elif op in (11,12):put(a[0],-get(a[1]))
            elif op==13:put(a[0],get(a[1]))
            elif op==14:
                t=types.get(a[0][1].lower(),self.types.get(a[0][1].lower()))
                x=get(a[1])
                z=int(x) if t=='int' else f32(x) if t=='float' else bool(x) if t=='bool' else str(x) if t=='string' else x
                put(a[0],z)
            elif op in (15,16,17,18,19):
                x,y=get(a[1]),get(a[2])
                z=(x==y) if op==15 else (x<y) if op==16 else (x<=y) if op==17 else (x>y) if op==18 else (x>=y)
                put(a[0],z)
            elif op==20:nxt=pc+get(a[0])
            elif op in (21,22):
                if bool(get(a[0]))==(op==21):nxt=pc+get(a[1])
            elif op==23:
                method,target=a[0][1],get(a[1]);argv=[get(v) for v in va]
                if target is self and method.lower() in self.obj['functions']:r=self.call(method,*argv)
                else:r=self.native(target,method,argv)
                put(a[2],r)
            elif op==25:put(a[2],self.native(a[0][1],a[1][1],[get(v) for v in va]))
            elif op==26:return get(a[0])
            elif op==27:put(a[0],str(get(a[1]))+str(get(a[2])))
            elif op==28:
                target=get(a[1]);assert target is self
                put(a[2],self.vars[self.obj['properties'][a[0][1].lower()][1]])
            elif op==29:
                target=get(a[1]);assert target is self
                self.vars[self.obj['properties'][a[0][1].lower()][1]]=get(a[2])
            elif op==30:
                k=a[0][1].lower(); t=types.get(k,self.types.get(k,''))
                assert t.endswith('[]'), ('array destination type', k, t)
                put(a[0],[default(t[:-2]) for _ in range(get(a[1]))])
            elif op==31:put(a[0],len(get(a[1])) if get(a[1]) is not None else 0)
            elif op==32:put(a[0],get(a[1])[get(a[2])])
            elif op==33:get(a[0])[get(a[1])]=get(a[2])
            else:raise AssertionError(('unimplemented opcode',op))
            pc=nxt
        return None

if __name__=='__main__':
    import sys,json
    for path in sys.argv[1:]:
        p=Pex(path)
        print(json.dumps(dict(file=path,version=p.version,script=p.obj['name'],parent=p.obj['parent'],properties=p.obj['properties'],functions=list(p.obj['functions'])),indent=2))
