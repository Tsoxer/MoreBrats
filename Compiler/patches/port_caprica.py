from pathlib import Path
root=Path('work/deps/caprica-linux/Caprica')
for fname,method,startneedle,endneedle,ret,args in [
 ('common/CapricaBinaryReader.h','read','  template <typename T>\n  T read()', '\nprotected:', 'T',''),
 ('common/CapricaBinaryWriter.h','write','  template <typename T>\n  void write(T val)', '\n  void writeBuffer', 'void','T val'),
 ('pex/PexAsmWriter.h','writeKV','  template <typename T>\n  void writeKV', '\n  template <typename... Args>', 'void','const char* key, T val')]:
 p=root/fname;s=p.read_text();a=s.index(startneedle)
 if fname.endswith('CapricaBinaryWriter.h'):
  print(s[s.index('  template <>',a):][-1500:])
  end=s.index('\n  void pad',a) if '\n  void pad' in s[a:] else s.index('\nprotected:',a)
 else:end=s.index(endneedle,a)
 segment=s[a:end]
 import re
 matches=list(re.finditer(r'  template <>\n  (.+?) '+method+r'\((.*?)\) \{',segment))
 branches=[]
 for m in matches:
  beg=m.end();depth=1;j=beg
  while depth:
   if segment[j]=='{':depth+=1
   elif segment[j]=='}':depth-=1
   j+=1
  typ=m.group(1) if method=='read' else m.group(2).split(', ')[-1].rsplit(' ',1)[0]
  branches.append((typ,segment[beg:j-1]))
 replacement='  template <typename T>\n  '+ret+' '+method+'('+args+') {\n'
 for i,(typ,body) in enumerate(branches):
  replacement+=('    if' if i==0 else '    else if')+' constexpr (std::is_same_v<T, '+typ+'>) {'+body+'\n    }\n'
 replacement+='    else { static_assert(std::is_same_v<T, void>, "Unsupported type"); }\n  }\n'
 # Preserve any ordinary functions after the final specialization.
 last=matches[-1];d=1;j=last.end()
 while d:
  if segment[j]=='{':d+=1
  elif segment[j]=='}':d-=1
  j+=1
 replacement+=segment[j:]
 p.write_text(s[:a]+replacement+s[end:])
p=root/'common/IntrusiveLinkedList.h';p.write_text(p.read_text().replace('    friend LockstepIteratorWrapper<T2>;','').replace('    friend ConstLockstepIteratorWrapper<T2>;','').replace('  private:\n    \n    \n    struct','  public:\n    struct'))
p=root/'papyrus/parser/PapyrusLexer.cpp';s=p.read_text();a=s.index('static const __m128i identifierChars');b=s.index(';',a)+1;s=s[:a]+"static const __m128i identifierChars = _mm_setr_epi8('a','z','A','Z','0','9','_','_',':',':',0,0,0,0,0,0);"+s[b:];p.write_text(s)
