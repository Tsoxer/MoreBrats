"""Narrow README updates and an append-only historical changelog section."""
from pathlib import Path
from datetime import datetime
import json,re,hashlib
R=Path('work/build/v1.1.0');RT=R/'runtime';O=R/'deliverables';O.mkdir(exist_ok=True)
date="11-18-2026"
(R/'release-date-internal.json').write_text(json.dumps({'release_date':date,'checked_at':'recorded historical release'},indent=2)+'\n')
old=Path('work/v1.0.0/runtime/README.txt').read_text();readme=old
def change(a,b):
 global readme
 assert readme.count(a)==1,(a,readme.count(a));readme=readme.replace(a,b)
change('MORE BRATS v1.0.0','MORE BRATS v1.1.0')
change('Release date: 11-16-2026','Release date: '+date)
change('Nord children explore 19 settlements during the day, head indoors in the',
       'human children explore 19 settlements during the day, head indoors in the')
change('- Each child independently receives a male or female vanilla Nord-child\n  appearance and one of five vanilla outfits: red, blue, green, grey, or yellow.\n  Repeated appearances and outfits are normal.',
       '- Each child independently selects a genuine vanilla child race: Nord,\n  Imperial, Breton, or Redguard (25% each); male or female (50% each); and one\n  of five vanilla outfits: red, blue, green, grey, or yellow (20% each).\n  All 40 combinations are eligible in every settlement. Repeats are normal.')
change('MoreBrats-v1.0.0.zip','MoreBrats-v1.1.0.zip')
change('Upgrading from v0.5.1 retains the same FormIDs, properties, saved-state types,\npopulation data, and gameplay logic. No new game, quest reset, or save cleaning',
       'Upgrading from v1.0.0 retains all previous FormIDs, properties, saved-state\ntypes, population data, and More Brats gameplay logic. Existing children keep\ntheir identities and appearances; new races join future daily selections.\nNew appearance bindings use stable-ID recovery on existing saves.\nNo new game, quest reset, or save cleaning')
change('for modded games, but no FPS, latency, memory, or 500-mod benchmark is claimed.',
       'for modded games, but no FPS, latency, memory, or 500-mod benchmark is claimed.\n\nv1.1.0 adds 2,280 disabled reusable references for appearance choices, for 3,040\ntotal. The active population limits and AI packages are unchanged. Pool scans\nnow cover four times as many references, with additional fixed appearance\nstorage. This adds script work and persistent state; it is not a zero-cost\nchange. No controllers, timers, polling frequency, or native AI population were\nadded. Exact performance and save-size differences remain unmeasured.')
change('v1.0.0 preserves that gameplay and updates public documentation and version\nlabels only. Independent checks cover the ESP, script/property bindings, PEX\nbytecode, startup data, and package layout. Compiled logic tests use mocked\nengine calls; they do not prove native pathfinding, door traversal, or performance.\nThe final v1.0.0 archive has not been separately run in Skyrim in the cloud.',
       'Tsoxer subsequently confirmed v1.0.0 as the working release. v1.1.0 extends\nits appearance pools while preserving More Brats spawning safety, roaming,\nschedules, destinations, AI packages, population limits, and controller timing.\nIndependent checks cover the ESP, script/property bindings, PEX bytecode,\nstartup data, and package layout. Compiled logic tests use mocked engine calls;\nthey do not prove native pathfinding, door traversal, appearance rendering, or\nperformance. The final v1.1.0 archive has not been run in Skyrim in the cloud.')
change('Live status messages and traces identify v1.0.0. After a controller runs, its\nScriptBuild, Build, and DiagAIRevision values are 1000.',
       'Live status messages and traces identify v1.1.0. After a controller runs, its\nScriptBuild, Build, and DiagAIRevision values are 1100.')
extra='''
VANILLA APPEARANCE TEMPLATES
Nord appearances retain Lars Battle-Born / Dorthe. The added Imperial templates
are Francois Beaufort / Mila Valentia; Breton, Blaise / Erith; Redguard,
Alesan / Braith. These are appearance/default donors, not new named residents:
the displayed name stays Child. The new variants use their corresponding real
vanilla child races and inherit the donors' normal child stats/template defaults.
They keep More Brats' own packages, factions, inventory/access keys, schedules,
and controller logic; donor quest scripts and daily routines are not inherited.

All five torso outfits and child shoes have verified male/female model entries
and support all four child races in public Bethesda-record metadata. The existing
Traits inheritance approach reuses vanilla appearances; no FaceGen or other art
files are added. Actual heads, skin tones, clothing rendering, and interactions
with appearance replacers still need an in-game check.

FOCUSED v1.1.0 PLAYTEST
1. Replace v1.0.0 while Skyrim is closed, retaining a backup save. Keep one ESP.
2. Verify existing children remain functional. Allow a new morning cycle to
   encounter the new appearances; existing actors are not forcibly replaced.
3. Over several mornings, check both genders of all four races and five outfit
   colors. Random repeats are expected; every combination need not appear daily.
4. Check heads/skin/clothes/shoes for correct rendering and no missing head or
   unexpected face tint. All NPCs should still be named Child.
5. Check normal roaming, 7 PM building entry, safe post-3 AM removal, daily
   rerolls, save/reload, and at least one existing-save upgrade in each region.
6. Optional: getglobalvalue MB_ScriptBuild should show 1100 after Whiterun's
   controller runs; use the settlement prefix elsewhere. No command is needed
   for normal play. Report the full status if bindings or activation fail.

'''
change('CREDITS\n',extra+'CREDITS\n')
# Required instructions, tables, schedule prose and requirements stay verbatim.
for start,end in [('SUPPORTED SETTLEMENTS','DAILY ROUTINE'),('DAILY ROUTINE','REQUIREMENTS'),('REQUIREMENTS','INSTALLATION'),('COMPATIBILITY AND LIMITATIONS','PERFORMANCE')]:
 assert old[old.index(start):old.index(end)]==readme[readme.index(start):readme.index(end)]
(RT/'README.txt').write_text(readme);(O/'README-v1.1.0.txt').write_text(readme)
section=f'''
v1.1.0 — {date}
Vanilla human child race variety
- Added genuine Imperial, Breton and Redguard child races alongside the existing
  Nord children. Each race supports male/female appearances and all five existing
  red, blue, green, grey and yellow child outfits: 40 combinations per settlement.
- Race is an independent RandomInt(1,4) draw (25% each), gender an independent
  RandomInt(1,2) draw (50% each), and clothing retains RandomInt(0,4) (20% each).
  All races are eligible in all 19 settlements; no city-specific weighting.
- Retained Nord donors Lars/Dorthe. New donors: Imperial Francois/Mila, Breton
  Blaise/Erith and Redguard Alesan/Braith. Corresponding child RACE records and
  donor gender identities were checked against public game-record/reference data.
- As authorized, new variants inherit their appropriate vanilla donors' normal
  child stats and template defaults. Exact Nord-only non-appearance equivalence
  is not claimed. Donor scripts, factions, inventory and AI package lists are not
  inherited; each new record copies the corresponding settlement's More Brats
  packages, factions, keys, name and outfit unchanged.
- Appended 570 NPC bases and 2,280 initially disabled persistent actor references.
  The complete fixed pool now contains 3,040 references and 760 NPC bases. The
  normal combined active daily target remains 42–76, with all 19 ranges intact.
- Preserved all 1,872 existing FormIDs, 190 original Nord NPC bases, 760 original
  placed actors, all 472 AI packages, roads, inn/cell goals, factions and lists.
  Added three appearance-reference bindings to each of 19 existing quests; alias
  data, startup settings and SEQ bytes are unchanged. Total: 4,722 records.
- Kept the legacy Nord pool/indices and saved variant values 0–9 unchanged.
  Three separate actor-reference arrays and three orphan-observation arrays per
  controller avoid Papyrus's 128-entry array limit. New variant indices 10–39
  map to appended reusable references; no unlimited spawning or new controller.
- Extended only appearance storage validation/binding, lookup/indexing, selection,
  and existing pool bookkeeping/counting to cover the additions. Missing saved
  new properties recover through stable local IDs. Existing valid arrays and
  active actors are retained, with schemas 6/7 and old property/field types intact.
- Spawning safety tests, road selection, native placement/enabling sequence,
  daytime roaming, run/pause timing, pathfinding goals, schedules, retirement
  observations, callbacks, leases and transition handling retain v1.0.0 logic.
  Phase 3's Travel-to-Sandbox packages are byte-identical. No unrelated bug fix.
- Recompiled nine scripts: four require appearance-pool changes; five aliases/
  watchdog change only version strings. Live labels identify v1.1.0 and current
  diagnostic stamps use 1100; historical phase values and schemas are unchanged.
- Independent ESP/VMAD/PEX readers and a strict baseline diff check old records,
  new race/template/outfit pairs, property bindings, internal links and array
  allocation bytecode. All arrays stay at or below 90 entries individually.
- Compiled-PEX mock tests cover 1,900 settlement-days, all population ranges,
  all 3,040 slot/variant mappings, 57 typed old-state upgrade cases, faults,
  missing added references, the Skaal availability gate and independent RNG draws.
  Sampling is approximate; the algorithm's probabilities are not forced quotas.
- The same active NPC counts, AI packages, scripts/instances and timers remain.
  Persistent storage and pool-scan work increase because four appearance pools
  are examined. No claim of unchanged CPU/RAM/save size or measured performance.
- Public metadata confirms male/female models and all four child-race entries
  for the five existing torso outfits and shoes. Traits inheritance reuses
  Bethesda appearances; no custom races, FaceGen, models, textures or voices
  are supplied. Requirements remain the same three official masters; no SKSE,
  Address Library, SPID, external framework or paid Anniversary content.
- Source/API/reference checks are not a Skyrim rendering, native pathfinding,
  real ESS migration or performance test. v1.1.0 still needs Tsoxer's playtest,
  particularly new heads/skin tones/outfits and an upgrade with active children.
  Existing activation delays and earlier known limitations remain unchanged.
- Historical downloads and all v0.1–v1.0.0 changelog entries remain intact.
'''
history=Path('work/v1.0.0/runtime/CHANGELOG.txt').read_text()
# Only the document's current-release metadata changes; historical entries don't.
history=history.replace('Current release: v1.0.0 — 11-16-2026','Current release: v1.1.0 — '+date)
changelog=history.rstrip()+'\n'+section
assert changelog[changelog.index('v0.1 —'):changelog.index('\nv1.1.0 —')].rstrip()==Path('work/v1.0.0/runtime/CHANGELOG.txt').read_text().split('v0.1 —',1)[1].join(['v0.1 —','']).rstrip()
(RT/'CHANGELOG.txt').write_text(changelog);(O/'CHANGELOG-v1.1.0.txt').write_text(changelog)
(O/'CHANGES-v1.1.0.txt').write_text('More Brats v1.1.0 — Tsoxer\n'+section)
for path in [RT/'README.txt',RT/'CHANGELOG.txt']:
print('Rendered updated README and appended changelog; historical entries and protected instruction sections retained.')
