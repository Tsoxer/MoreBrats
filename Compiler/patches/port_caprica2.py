from pathlib import Path
import re
root=Path('work/deps/caprica-linux/Caprica')
for fname,method,ret,args,fallback in [('pex/PexReader.h','read','T','','return CapricaBinaryReader::read<T>();'),('pex/PexWriter.h','write','void','T val','CapricaBinaryWriter::write<T>(std::forward<T>(val));')]:
 p=root/fname;s=p.read_text();a=s.index('  template <typename T>');matches=list(re.finditer(r'  template <>\n  (.+?) '+method+r'\((.*?)\) \{',s[a:]));branches=[]
 for m in matches:
  beg=a+m.end();depth=1;j=beg
  while depth:
   if s[j]=='{':depth+=1
   elif s[j]=='}':depth-=1
   j+=1
  typ=m.group(1) if method=='read' else m.group(2).rsplit(' ',1)[0];branches.append((typ,s[beg:j-1]));end=j
 replacement='  template <typename T>\n  '+ret+' '+method+'('+args+') {\n'
 for i,(typ,body) in enumerate(branches):replacement+=('    if' if i==0 else '    else if')+' constexpr (std::is_same_v<T, '+typ+'>) {'+body+'\n    }\n'
 replacement+='    else { '+fallback+' }\n  }\n';p.write_text(s[:a]+replacement+s[end:])
p=root/'common/IntrusiveLinkedList.h';s=p.read_text();s=s.replace('  private:\n\n\n    struct','  public:\n    struct');p.write_text(s)
