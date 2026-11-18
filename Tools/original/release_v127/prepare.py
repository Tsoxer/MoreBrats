"""Two additions on v1.2.6: local donor uniqueness and shared-limit interior preparation."""
from pathlib import Path
import hashlib,json,re,shutil,difflib
W=Path('work');R=W/'release_v127';OUT=W/'v1.2.7/src';B=W/'build/v1.2.7'
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for root in [W/'build/v1.1.0',W/'build/v1.2.6',W/'v1.2.6/src'] for p in root.rglob('*') if p.is_file()}
(R/'protected-baselines.json').write_text(json.dumps(protected,indent=2)+'\n');patch=[]
def change(t,n,fn):
 m=re.search(r'^(?:[A-Za-z]+ )?Function '+n+r'\([^\n]*\)\n.*?^EndFunction',t,re.M|re.S);assert m,n
 return t[:m.start()]+fn(m.group())+t[m.end():]
for p in (W/'v1.2.6/src').glob('*.psc'):
 if 'Controller' not in p.stem:shutil.copyfile(p,OUT/p.name);continue
 white=p.stem=='MB_Controller';cap='6' if white else 'MaxPopulation';base='0x800' if white else 'ConfigBase'
 t=p.read_text().replace('v1.2.6','v1.2.7').replace('1206.0','1207.0')
 t=t.replace('Event OnInit()','''; v1.2.7: one interior opportunity, serviced by the EXISTING population worker.
Bool interiorArrivalPending = False
Int interiorArrivalCycle = -100000

Event OnInit()''',1)
 t=change(t,'Transition',lambda f:f.replace('    transitionPending = True','''    ; Capture an entry even when a quick exit precedes the deferred worker.
    If Game.GetPlayer().IsInInterior() && ArrivalRelevant()
        interiorArrivalPending = True
        interiorArrivalCycle = CycleAt(Utility.GetCurrentGameTime())
    EndIf
    transitionPending = True''',1))
 def arrival(f):
  needle='    Actor chosen = PoolActor(PoolIndex(s, selectedVariant[s]))';assert needle in f
  f=f.replace(needle,'''    ; All five colors of one donor share a key. Include saved carry-overs and
    ; reserved references; daily selectedVariant values alone are not identities.
    Bool[] usedDonors = new Bool[40]
    If !usedDonors || usedDonors.Length != 40
        Defer(s, 30, "arrival donor storage unavailable")
        Return
    EndIf
    Int peer = 0
    While peer < '''+cap+'''
        Actor existing = residents[peer]
        If existing != None && peer != s
            Int actualVariant = VariantForActor(existing)
            Int key = DonorKey(actualVariant)
            If key < 0
                Defer(s, 46, "cannot identify saved resident donor; slot=" + peer)
                Return
            EndIf
            usedDonors[key] = True
        EndIf
        peer += 1
    EndWhile
    If ticket != workEpoch
        Return
    EndIf
    selectedVariant[s] = UniqueVariant(s, selectedVariant[s], usedDonors)
    If selectedVariant[s] < 0
        Defer(s, 45, "no unused resolved donor available for this settlement")
        Return
    EndIf
'''+needle,1)
  needle='''    diagTargetContext = "TryArrival.random exterior door / existing outdoor ground"
    Int index = DoorArrivalIndex()''';assert needle in f
  return f.replace(needle,'''    diagTargetContext = "TryArrival.random exterior door / existing outdoor ground"
    Int index = -1
    If interiorArrivalPending
        diagTargetContext = "TryArrival.v110 interior opportunity / original street marker"
        index = StreetArrivalIndex()
    Else
        index = DoorArrivalIndex()
    EndIf''',1)
 t=change(t,'TryArrival',arrival)
 def process(f):
  needle='''    If !relevant
        arrivalWasRelevant = False
        Return
    EndIf''';assert needle in f
  f=f.replace(needle,'''    If !relevant
        arrivalWasRelevant = False
        interiorArrivalPending = False
        Return
    EndIf
    If interiorArrivalPending && interiorArrivalCycle != cycle
        interiorArrivalPending = False
    EndIf
    If Game.GetPlayer().IsInInterior()
        interiorArrivalPending = True
        interiorArrivalCycle = cycle
    EndIf''',1)
  needle='''        nextArrivalAt = 0.0
        Return
    EndIf
    If nextArrivalAt <= 0.0''';assert needle in f
  f=f.replace(needle,'''        nextArrivalAt = 0.0
        interiorArrivalPending = False
        Return
    EndIf
    If interiorArrivalPending
        FillInteriorOpportunity(cycle)
        Return
    EndIf
    If nextArrivalAt <= 0.0''',1)
  # Extract and reuse the exact empty-slot/repair guards for BOTH arrival paths.
  start=f.index('    If s < dailyPopulation\n');end=f.index('    ; After latent placement',start)
  block=f[start:end]
  inner=block[len('    If s < dailyPopulation\n'):];assert inner.endswith('    EndIf\n')
  inner=inner[:-len('    EndIf\n')];inner='\n'.join(line[4:] if line.startswith('    ') else line for line in inner.rstrip().splitlines())+'\n'
  shared='''Function TryPendingArrival(Int s, Int cycle)
'''+inner+'''EndFunction
'''
  extras.append(shared)
  return f[:start]+'''    If s < dailyPopulation
        Int owner = workEpoch
        TryPendingArrival(s, cycle)
        If owner != workEpoch
            Return
        EndIf
    EndIf
'''+f[end:]
 extras=[];t=change(t,'ProcessArrival',process)
 # Only exact source changes above; old donor RNG remains intact before filtering.
 helpers='''
; Cosmetic identity, derived from the immutable 200-index mapping.
Int Function DonorKey(Int variant)
    If variant < 0 || variant >= 200
        Return -1
    EndIf
    If variant >= 40
        Return 8 + (variant - 40) / 5
    EndIf
    Int local = variant % 10
    Int gender = 0
    If (local >= 3 && local < 6) || local >= 8
        gender = 1
    EndIf
    Return (variant / 10) * 2 + gender
EndFunction

Int Function VariantClothing(Int variant)
    If variant >= 40
        Return (variant - 40) % 5
    EndIf
    Int local = variant % 10
    If local < 6
        Return local % 3
    EndIf
    Return 3 + (local - 6) % 2
EndFunction

Int Function VariantForDonor(Int key, Int clothing)
    If key >= 8
        Return 40 + (key - 8) * 5 + clothing
    EndIf
    Int gender = key % 2
    If clothing < 3
        Return (key / 2) * 10 + gender * 3 + clothing
    EndIf
    Return (key / 2) * 10 + 6 + gender * 2 + clothing - 3
EndFunction

Int Function DonorGroup(Int key)
    If key < 8
        Return key
    ElseIf key < 23
        Return 0
    ElseIf key < 35
        Return 1
    ElseIf key == 35
        Return 2
    ElseIf key == 36
        Return 3
    ElseIf key == 37
        Return 4
    ElseIf key == 38
        Return 6
    EndIf
    Return 7
EndFunction

Int Function AvailableDonors(Int slot, Int group, Int clothing, Bool[] used)
    Int count = 0
    Int key = 0
    While key < 40
        If DonorGroup(key) == group && !used[key]
            If PoolActor(PoolIndex(slot, VariantForDonor(key, clothing))) != None
                count += 1
            EndIf
        EndIf
        key += 1
    EndWhile
    Return count
EndFunction

Int Function UniqueVariant(Int slot, Int preferred, Bool[] used)
    Int key = DonorKey(preferred)
    If key < 0
        Return -1
    EndIf
    If !used[key] && PoolActor(PoolIndex(slot, preferred)) != None
        Return preferred
    EndIf
    Int clothing = VariantClothing(preferred)
    Int group = DonorGroup(key)
    Int count = AvailableDonors(slot, group, clothing, used)
    If count == 0
        ; A category can contain only one donor. Keep the ordinary rolls unless
        ; uniqueness exhausts it; then choose uniformly among available groups.
        Int groups = 0
        Int g = 0
        While g < 8
            If AvailableDonors(slot, g, clothing, used) > 0
                groups += 1
            EndIf
            g += 1
        EndWhile
        If groups == 0
            Return -1
        EndIf
        Int pick = Utility.RandomInt(0, groups - 1)
        g = 0
        While g < 8
            Int size = AvailableDonors(slot, g, clothing, used)
            If size > 0
                If pick == 0
                    group = g
                    count = size
                    g = 8
                Else
                    pick -= 1
                EndIf
            EndIf
            g += 1
        EndWhile
    EndIf
    Int choice = Utility.RandomInt(0, count - 1)
    key = 0
    While key < 40
        If DonorGroup(key) == group && !used[key]
            Int v = VariantForDonor(key, clothing)
            If PoolActor(PoolIndex(slot, v)) != None
                If choice == 0
                    Return v
                EndIf
                choice -= 1
            EndIf
        EndIf
        key += 1
    EndWhile
    Return -1
EndFunction

Int Function VariantForActor(Actor child)
    If child == None
        Return -1
    EndIf
    Int id = child.GetFormID() % 0x1000000
    ; Vanilla FormIDs are signed Papyrus Ints for load indices80..FD.
    If id < 0
        id += 0x1000000
    EndIf
    Int index = -1
    Int appended = 0x100000 + BASE * 16 + 0x2000
    Int races = 0x20000 + BASE + 0x100
    If id >= appended && id < appended + CAP * 160
        index = CAP * 40 + id - appended
    ElseIf id >= races && id < races + CAP * 30
        index = CAP * 10 + id - races
    EndIf
OLD_NORD
    If index < 0 || index >= AppearancePoolSize() || PoolActor(index) != child
        Return -1
    EndIf
    If index >= CAP * 40
        Return 40 + (index - CAP * 40) / CAP
    EndIf
OLD_VARIANT
EndFunction

Int Function StreetArrivalIndex()
    ; Exact same pre-existing street whitelist used by v1.1.0. No door query,
    ; new coordinates, player-distance gate or appearance-pool scan.
    diagArrivalDoor = None
    diagDoorFallback = True
    Int count = roads.Length
    Int offset = Utility.RandomInt(0, count - 1)
    Int probe = 0
    Int fallback = -1
    While probe < count
        Int index = (offset + probe) % count
        If RoadValid(roads[index])
            If fallback < 0
                fallback = index
            EndIf
            Bool occupied = False
            Int peer = 0
            While peer < CAP && !occupied
                occupied = residents[peer] != None && arrivalIndex[peer] == index
                peer += 1
            EndWhile
            If !occupied
                Return index
            EndIf
        EndIf
        probe += 1
    EndWhile
    Return fallback
EndFunction

Function FillInteriorOpportunity(Int cycle)
    Int ticket = workEpoch
    Int s = 0
    ; Share the existing target, residents, reservation and worker lease. Never
    ; roll another population or create references. Bound work by the same cap.
    While s < dailyPopulation && ticket == workEpoch
        If repairRequested || orphanPresent || !Daylight(HourAt(Utility.GetCurrentGameTime())) || CycleAt(Utility.GetCurrentGameTime()) != cycle || !ArrivalRelevant()
            s = dailyPopulation
        Else
            If residents[s] == None && ResidentCount() < dailyPopulation
                TryPendingArrival(s, cycle)
            EndIf
            s += 1
        EndIf
    EndWhile
    If ticket == workEpoch
        interiorArrivalPending = False
        If HasPendingArrivals()
            nextArrivalAt = Utility.GetCurrentGameTime() + Utility.RandomFloat(3.0, 7.0) / 1440.0
        Else
            nextArrivalAt = 0.0
        EndIf
    EndIf
EndFunction
'''
 nord='''    If index < 0
        If id >= 0x809 && id <= 0x813 && (id - 0x809) % 2 == 0
            index = (id - 0x809) / 2
        ElseIf id >= 0x818 && id < 0x836
            index = 6 + id - 0x818
        ElseIf id >= 0x890 && id < 0x8A8
            index = 36 + id - 0x890
        EndIf
    EndIf'''
 if not white:nord='''    If index < 0 && id >= ConfigBase + 0x100 && id < ConfigBase + 0x100 + MaxPopulation * 10
        index = id - ConfigBase - 0x100
    EndIf'''
 inverse='''    If index < 36
        Return index % 6
    ElseIf index < 60
        Return 6 + (index - 36) % 4
    EndIf
    Return (index / 60) * 10 + index % 10'''
 if not white:inverse='    Return (index / (MaxPopulation * 10)) * 10 + index % 10'
 helpers=helpers.replace('OLD_NORD',nord).replace('OLD_VARIANT',inverse).replace('BASE',base).replace('CAP',cap)
 t+='\n'+''.join(extras)+helpers
 t=change(t,'ShowStatus',lambda f:f.replace('    message += "\\nLast arrival: due="','''    message += "\\nInterior preparation pending=" + interiorArrivalPending + "; cycle=" + interiorArrivalCycle
    message += "\\nDonor reasons: 45=no unused bound donor; 46=unknown resident identity"
    message += "\\nLast arrival: due="''',1))
 (OUT/p.name).write_text(t)
 patch.extend(difflib.unified_diff(p.read_text().splitlines(True),t.splitlines(True),fromfile='v1.2.6/'+p.name,tofile='v1.2.7/'+p.name))
(B/'SOURCE-CHANGES.patch').write_text(''.join(patch))
for name in ['API','Config']:shutil.copytree(W/'release_v126'/name,R/name,dirs_exist_ok=True)
for name in ['PluginBuilder','PluginAudit']:
 (R/name).mkdir(exist_ok=True)
 for p in (W/'release_v126'/name).glob('*'):
  if p.suffix in ['.cs','.csproj']:shutil.copyfile(p,R/name/p.name)
p=R/'PluginBuilder/Program.cs';t=p.read_text().replace('build/v1.2.5/runtime','build/v1.2.6/runtime').replace('build/v1.2.6/runtime";Directory','build/v1.2.7/runtime";Directory').replace('v1.2.5 is the complete','v1.2.6 is the complete').replace('v1.2.6 development. Lower arrival latency; appearances, AI and departures retained.','v1.2.7 development. Unique local appearance donors and shared-limit interior street arrivals.').replace('g.RawFloat=1206','g.RawFloat=1207');p.write_text(t)
p=R/'build.py';p.write_text((W/'release_v126/build.py').read_text().replace('v1.2.6 playtest candidate directly from complete v1.2.5','v1.2.7 playtest candidate directly from complete v1.2.6').replace('build/v1.2.6/runtime','build/v1.2.7/runtime').replace("WORK/'v1.2.6/src'","WORK/'v1.2.7/src'").replace("WORK/'build/v1.2.5/runtime/Scripts'","WORK/'build/v1.2.6/runtime/Scripts'"))
shutil.copyfile(W/'build/v1.2.6/settlements.json',B/'settlements.json')
print('Prepared v127 on v126: four controllers; no NPC/AI/ref changes; five helper sources unchanged.')
