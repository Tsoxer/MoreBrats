"""v125 private playtest documentation; prior changelog bytes remain untouched."""
from pathlib import Path
import datetime,re,json
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.5';RT=R/'runtime';BASE=W/'build/v1.2.4/runtime'
date="11-18-2026"
t=(BASE/'README.txt').read_text().replace('v1.2.4','v1.2.5').replace('1204','1205').replace('15–30','7–14')
t=re.sub(r'Private playtest date: [0-9-]+','Private playtest date: '+date,t)
t=t.replace('the stable public release; this candidate is built directly from v1.2.3 and\nretains the ongoing v1.2.5 activation/callback repairs.','the stable public release; this candidate is built directly from released v1.2.4.\nIt retains the existing door placement, appearance and activation fixes.')
t=t.replace('All existing FormIDs, NPC/reference identities, 200 variant meanings, serialized\nfield/property names and types, quest/AI records, population ranges and schemas\nare preserved. A single new door-type FormList is appended. Its cached binding\nand a few private scalar diagnostics initialize without a quest reset. Existing\nresidents retain their appearances; future arrivals use the unchanged donor RNG.','All existing FormIDs, NPC/reference identities, 200 variant meanings, serialized\nfield/property names, types and defaults, quest/AI records, population ranges and\nschemas are preserved. No records, script properties or serialized fields are\nadded in v1.2.5. Existing residents retain their identities and appearances;\nfuture arrivals use the unchanged donor RNG.')
t=t.replace('Typed-state tests cover upgrades from v1.1.0 through v1.2.3; actual ESS loading','Typed-state tests cover upgrades from v1.1.0 through v1.2.4; actual ESS loading')
a=t.index('The existing game-time arrival timer retains');b=t.index('Outdoor trips retain',a)
t=t[:a]+'''Native game-time updates retain their real-time counterpart. Local daytime
roaming now also gets a real-time counterpart for its EXISTING planned AI
deadline, even when the daily population is full. The last child should no
longer lose its outdoor travel updates merely because arrivals are finished.
This mirrors existing deadlines; it introduces no faster polling frequency.
Nighttime timing, interior travel and safe removal criteria are unchanged.

Long cache/recovery loops renew the existing worker lease only at bounded
progress checkpoints. A progressing worker is not treated as stuck solely
because total initialization exceeds its timeout. A genuinely stalled worker
can still expire. Normal recovery reuses its complete census rather than
reading the entire enabled pool three times; exceptional orphan retirement
continues through the existing safety path.

The first arrival deadline starts before cache/recovery work. A long one-time
old-save initialization can still delay actual enabling; it does not start a
second full arrival delay when that work ends. A saved older long interval is
shortened to the requested range, without resetting the population or actors.
Repeated entry notifications coalesce. Native timer replacements explicitly
unregister an unelapsed timer first, following the documented vanilla contract.

'''+t[b:]
a=t.index('PERFORMANCE\n');b=t.index('OPTIONAL SUPPORT INFORMATION\n',a)
t=t[:a]+'''PERFORMANCE
Papyrus assessment: MODERATE, estimated from code, not measured in Skyrim.
Routine enabled counting is bytecode-identical to v1.2.4: at most76 tracked
native checks across all19 full populations, not15,200 potential appearances.
A normal recovery now uses one complete native enabled-state census instead
of three passes. It still checks the entire pool and adopts untracked actors;
extra orphans retain the existing conservative retirement rules. Initialization
and exceptional recovery remain expensive and may delay heavily loaded games.

Daytime roaming's real-time counterpart matches its existing game-time deadline.
It is selective to relevant settlements and uses the same serialized worker.
It is not a per-frame loop or a new background manager. Door queries still run
only for due arrivals. Active populations and native AI/pathfinding are unchanged.
No FPS, CPU timing, queue-latency, RAM or zero-lag guarantee is made.

TESTING AND RELEASE STATUS
This is an unpublished v1.2.5 candidate. Tsoxer confirmed that v1.2.4 can spawn
in open-world settlements but reported door-area loitering and no visually
observed walled-city children. These are the latest author observations; do
not describe every settlement as independently failed or passed.

Final ESP/PEX structure, stable bindings, all200 variants and typed old-state
upgrades are checked automatically. Native-delay tests execute the released
and final bytecode with progress/timeout callbacks interleaved; previous tests
incorrectly gave every native call instantaneous completion. Tests also check
that the last arrival receives an actual Travel package after the population
is full. Simulated travel and synthetic door locations are not Skyrim pathfinding.

Skyrim has NOT been run for this build. The code-level failure mechanisms are
reproduced in controlled tests; the exact native trigger in the author's game
is not proven. Real save-file loading, door queries, rendering, callbacks and
movement in the author's modlist require manual testing. No in-game benchmark
or universal save-compatibility guarantee is claimed.

'''+t[b:]
a=t.index('FOCUSED v1.2.5 DEVELOPMENT PLAYTEST\n');b=t.index('CREDITS\n',a)
t=t[:a]+'''FOCUSED v1.2.5 DEVELOPMENT PLAYTEST
1. Back up your known-good v1.1.0 save. Replace the earlier test build, keep one
   MoreBrats.esp active and let all included scripts win file conflicts.
2. Visit Whiterun and Solitude between8 AM and7 PM. Walk/run outdoors, without
   entering a building. New arrivals are separated by7–14 IN-GAME MINUTES.
   Initial cache/recovery work can delay the first child; no instant crowd is
   promised. Look around entrance areas and the existing streets.
3. Repeat in Markarth, Riften and Windhelm, then an open-world capital and
   Dragon Bridge. Player position, viewing direction and proximity do not
   reject arrivals. Visible appearance is intentionally allowed.
4. After the target population is reached, remain outdoors at least30 more
   in-game minutes. Pay particular attention to the LAST child: it should
   leave its initial pause and receive the existing wandering/travel routine.
   Normal brief stops, seating and sandbox pauses remain part of that routine.
5. Fast travel between settlements, revisit, wait/sleep, and save/reload during
   a partial population. Check no duplicate actors or population-limit excess.
6. Observe the unchanged7 PM interior routine and watched post3 AM retention,
   followed by safe removal after the relevant cell transition.
7. Appearance donors/outfits, running chance/cap and all19 populations remain
   unchanged. Optional diagnostics show build1205 after the controller runs.
   A popup is not required for normal gameplay; no screenshots are required.

'''+t[b:]
for a,b in [('most76','most 76'),('all19','all 19'),('not15,200','not 15,200'),('all200','all 200'),('between8','between 8'),('and7 PM','and 7 PM'),('by7–14','by 7–14'),('least30','least 30'),('unchanged7','unchanged 7'),('post3','post-3'),('build1205','build 1205')]:t=t.replace(a,b)
(RT/'README.txt').write_text(t)
entry=f'''\n\nMore Brats — v1.2.5 Changelog — {date}
PRIVATE PLAYTEST CANDIDATE; stable public release remains v1.1.0.

LATEST AUTHOR EVIDENCE
- v1.2.4 does activate children in tested open-world settlements. Children were
  reported remaining around their arrival doors; walled-city children were not
  visually observed. This supersedes the initial broad no-spawn report.
- Requested and confirmed arrival interval:7–14 IN-GAME MINUTES, not real seconds.

CODE-LEVEL FINDINGS AND REPAIRS
- Previous tests made native calls complete instantly. With injected native
  delays and an interleaved recovery callback, released v1.2.4 bytecode expires
  a still-progressing120-second initialization worker and starts recovery again.
  Existing long loops now renew the same lease at bounded progress checkpoints.
  No new manager, timer cadence, serialized field or script is added. Stuck
  workers retain timeout recovery; cancelled workers check ownership fences.
- Normal Reconcile previously read every enabled flag in its adoption pass,
  repeated that scan in RecoverOrphans, then ran FullEnabledCount a third time.
  Reuse the complete adoption census; invoke existing orphan retirement only
  when the scan actually finds enabled extras. Preserve adoption, state and
  orphan visibility rules; routine tracked counting stays unchanged.
- Prime the first existing game-time deadline BEFORE expensive setup, rather
  than adding a new interval after initialization. Waiting across a morning
  boundary still admits at most one overdue arrival. Shorten an older excessive
  pending interval conservatively; keep existing actors, indices and population.
- Use7–14-minute randomized intervals for subsequent individual arrivals.
- A full population previously disabled ArrivalFallbackDelay's real-time wake.
  If game-time updates were delayed or absent, the last actor could remain in
  its initial pause indefinitely. Mirror the EXISTING local daytime roaming
  deadline with a real-time wake too. No faster polling cadence, extra script,
  changed destination or forced movement. Scheduled timestamps still gate work.
- Shared walled-city PlayerInCity had an outdoor early return when the world
  query did not match, while ArrivalRelevant separately accepted the location.
  Use the same existing location fallback for roaming as for arrival relevance.
  No expansion of settlement boundaries or spawn territories.
- Explicitly unregister an unelapsed real-time timer before replacing it, per
  the vanilla registration contract. Earlier mocks always assumed replacement.

PRESERVATION
- All19,942 FormIDs and record identities remain. Only58 build-display globals
  and plugin description change. NPC, actor reference, quest, VMAD, faction,
  package, door list, master list, population and appearance payloads are intact.
- No new serialized fields or properties. Existing variable names/types/defaults,
  schemas6/7, pool order and200 appearance indices stay unchanged.
- Four controller PEX rebuilt; five helper PEX and startup SEQ remain identical.
  Forty donors, five outfits each, independent race/gender/outfit RNG, door-area
  placement, +33% running behavior,19 settlements and nighttime routines retained.
- Native APIs are vanilla Skyrim. No SKSE, Address Library, SPID or new dependency.

VALIDATION AND LIMITS
- Independent ESP/PEX checks; compiled-code scenarios for all settlements,
  outdoor motion, due arrivals, full-target roaming, location seams, slow-native
  initialization, interrupted workers, timer replacement and existing saves.
- Additional typed-state tests combine genuine v1.1.0 properties with the final
  expanded plugin data, retaining old actors and enabling appended appearances.
- Tested native delays/door geometry/events are synthetic inputs, not measured
  Skyrim performance. Actual ESS migration, rendered actors, pathfinding and the
  precise engine cause in the reported playtest remain unverified.
- Papyrus estimate: MODERATE. Routine count remains at most76 native enabled
  checks across all settlements. Normal initialization/recovery removes two
  redundant full-pool passes; occasional heavy work and native latency remain.

PLAYTEST
Use a backed-up existing save. Walk/run outdoors in the five walled cities and
open-world settlements between8 AM and7 PM. Allow7–14 game-minute intervals;
then observe the last child after the target is full. Repeat visits/reloads
and recheck unchanged7 PM interiors and safe post3 AM removal. See README.
'''
for a,b in [('interval:7','interval: 7'),('progressing120','progressing 120'),('Use7','Use 7'),('All19,942','All 19,942'),('Only58','Only 58'),('schemas6/7','schemas 6/7'),('and200','and 200'),('behavior,19','behavior, 19'),('most76','most 76'),('between8','between 8'),('and7 PM','and 7 PM'),('Allow7','Allow 7'),('unchanged7','unchanged 7'),('post3','post-3')]:entry=entry.replace(a,b)
history=(BASE/'CHANGELOG.txt').read_bytes();(RT/'CHANGELOG.txt').write_bytes(history+entry.encode())
for p in [RT/'README.txt',RT/'CHANGELOG.txt']:
(R/'documentation.json').write_text(json.dumps({'date':date,'prior_changelog_bytes_preserved':len(history)},indent=2)+'\n')
# Same-version timing revision. Keep the original v125 entry as history and
# append the new authoritative timing; remove format instructions, not dates.
original=W/'baselines/v1.2.5-7-14min/runtime'
text=(RT/'README.txt').read_text().replace('7–14','3–7').replace('MoreBrats-v1.2.5-Review.zip','MoreBrats-v1.2.5-Review-3-7min.zip')
text=text.replace('Review and in-game testing only; not a public release.','Review and in-game testing only; not a public release.\nTiming revision: 3–7 in-game minutes across all19 settlements.')
text=text.replace('all19 settlements','all 19 settlements')
text+='\nRECENT AUTHOR PLAYTEST\nTsoxer confirmed the preceding v1.2.5 build works in Riverwood and Whiterun.\nThis timing-only revision still needs the planned all19-settlement playtest.\nNo exhaustive runtime stability or save-compatibility certification is claimed.\n'
text=text.replace('all19-settlement','all 19-settlement')
(RT/'README.txt').write_text(text)
history=(original/'CHANGELOG.txt').read_text()
history=history.replace(' Dates use MM-DD-YYYY.','').replace('Dates use MM/DD/YYYY.','')
revision=f'''\n\nMore Brats — v1.2.5 Timing Revision — {date}
- Same version and build1205. Arrival delays reduced from7–14 to3–7 IN-GAME
  MINUTES across all19 settlements. This section is authoritative for this ZIP.
- Updated the initial, subsequent and retry delay draws, plus the older saved
  pending-delay bound. Population limits and all other gameplay remain unchanged.
- Tsoxer confirmed the preceding v1.2.5 build in Riverwood and Whiterun. This
  revised timing still requires the planned thorough19-settlement playtest.
- ESP, startup SEQ, five helper PEX, FormIDs, serialized fields, appearance data,
  AI packages, wandering, running and nighttime rules remain unchanged. Only
  arrival-timing constants differ in the four controller PEX script objects.
- Removed date-format instructions from the documents; retained actual dates.
- Prior v1.2.5 ZIP remains separately downloadable. New archive:
  MoreBrats-v1.2.5-Review-3-7min.zip.
- Automated structural, compiled-script, old-state, timing-boundary and lifecycle
  checks were repeated. Synthetic tests are not Skyrim execution or real ESS
  loading. Code-based Papyrus classification remains MODERATE.
'''
for a,b in [('build1205','build 1205'),('from7–14','from 7–14'),('to3–7','to 3–7'),('all19','all 19'),('thorough19','thorough 19')]:revision=revision.replace(a,b)
(RT/'CHANGELOG.txt').write_text(history+revision)
assert not re.search(r'(?i)mm[-/]dd[-/]yyyy',(RT/'README.txt').read_text()+(RT/'CHANGELOG.txt').read_text())

print('Updated v1.2.5 playtest documentation; historical changelog preserved; date='+date)
