"""Small independent VMAD v5 object-format-2 reader for this plugin's quests."""
import struct
class Reader:
 def __init__(self,b):self.b=b;self.i=0
 def n(self,f):
  x=struct.unpack_from('<'+f,self.b,self.i)[0];self.i+=struct.calcsize(f);return x
 def s(self):
  n=self.n('H');x=self.b[self.i:self.i+n].decode();self.i+=n;return x
 def obj(self):return dict(unused=self.n('H'),alias=self.n('h'),form=self.n('I'))
 def scripts(self):
  result={}
  for _ in range(self.n('H')):
   name=self.s();flag=self.n('B');assert flag==0;props={}
   for _ in range(self.n('H')):
    key=self.s();ty=self.n('B');status=self.n('B');assert status==1
    props[key]=self.obj() if ty==1 else self.s() if ty==2 else self.n('i') if ty==3 else [self.obj() for _ in range(self.n('I'))] if ty==11 else [self.n('i') for _ in range(self.n('I'))] if ty==13 else None
    assert props[key] is not None
   result[name]=props
  return result

def quest_vmad(record):
 r=Reader(record.get_subrecord('VMAD').data);assert (r.n('H'),r.n('H'))==(5,2)
 main=r.scripts();assert r.n('B')==2 and r.n('H')==0 and r.s()==''
 aliases=[]
 for _ in range(r.n('H')):
  obj=r.obj();assert (r.n('H'),r.n('H'))==(5,2)
  aliases.append((obj,r.scripts()))
 assert r.i==len(r.b)
 return main,aliases
