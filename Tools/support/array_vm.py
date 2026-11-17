"""Fault-aware test VM for actual Skyrim PEX, NOT the Skyrim engine.

The None->array CAST type-loss rule is an explicit hypothesis, corroborated by
external runtime reports but not Tsoxer's Papyrus log. Allocations can fail;
invalid array operations report errors and leave destinations unchanged. Native
functions, geometry and events are mocks. No game/save/pathfinding proof.
"""
from pexcheck import Pex,default,f32

class VM:
    def __init__(self, pex, native):
        self.obj=pex.obj; self.native=native
        self.vars={k:v[1] for k,v in self.obj['variables'].items()}
        self.types={k:v[0] for k,v in self.obj['variables'].items()}
        self.executed=0
        self.array_errors=[]
        self.allocations=[]
        self.deny_allocations=set()
        self.deny_stores=set()
        self.calls=[]
    def property(self,name,value):
        self.vars[self.obj['properties'][name.lower()][1]]=value
    def call(self,name,*params):
        fn=self.obj['functions'][name.lower()]
        self.calls.append(name.lower())
        assert not fn['native']
        local={k:default(t) for k,t in fn['params']+fn['locals']}
        local.update(dict(zip([k for k,t in fn['params']],params)))
        types=dict(fn['params']+fn['locals'])
        runtime_types=types.copy()
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
                if t and t.endswith('[]') and x is None:
                    # Explicitly model the suspected Skyrim failure rule.
                    # A None->array CAST removes the destination's array type.
                    runtime_types[a[0][1].lower()]='none'
                    self.array_errors.append((name,pc,'none-to-array CAST',a[0][1]))
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
                label=k
                if pc+1<len(fn['ins']):
                    next_op,next_args,_=fn['ins'][pc+1]
                    if next_op==13 and next_args[1]==a[0]:label=next_args[0][1].lower()
                size=get(a[1])
                live_type=runtime_types.get(k,t)
                if not t.endswith('[]') or not live_type.endswith('[]'):
                    self.array_errors.append((name,pc,'non-array allocation destination',label))
                elif label in self.deny_allocations:
                    self.array_errors.append((name,pc,'injected allocation failure',label))
                elif not isinstance(size,int) or not 1<=size<=128:
                    self.array_errors.append((name,pc,'invalid Skyrim array length',label))
                else:
                    put(a[0],[default(t[:-2]) for _ in range(size)])
                    self.allocations.append((name,label,t,size))
            elif op==31:
                value=get(a[1])
                if value is None:self.array_errors.append((name,pc,'None array length',a[1][1]))
                else:put(a[0],len(value))
            elif op==32:
                value,index=get(a[1]),get(a[2])
                if value is None or not 0<=index<len(value):
                    self.array_errors.append((name,pc,'invalid array read',a[1][1]))
                else:put(a[0],value[index])
            elif op==33:
                value,index=get(a[0]),get(a[1]);label=a[0][1].lower()
                if value is None or not 0<=index<len(value):
                    self.array_errors.append((name,pc,'invalid array write',label))
                elif (label,index) in self.deny_stores:
                    self.array_errors.append((name,pc,'injected store failure',label))
                else:value[index]=get(a[2])
            else:raise AssertionError(('unimplemented opcode',op))
            pc=nxt
        return None

