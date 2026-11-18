"""Prepare playtest documentation; append history without rewriting older entries."""
from pathlib import Path
import datetime,json,re
ROOT=Path(__file__).resolve().parent;W=ROOT.parent;R=W/'build/v1.2.4';RT=R/'runtime'
# Internal date calculation only. Published files show date, no location/timezone.
date="11-18-2026"
t=(W/'build/v1.2.3/runtime/README.txt').read_text().replace('v1.2.3','v1.2.4').replace('1203','1204')
t=re.sub(r'Private playtest date: [0-9-]+','Private playtest date: '+date,t)
t=t.replace('- Conservative arrivals and removals intended to avoid visible materialization\n  or disappearance. Existing visible children can delay the next day\'s arrivals.', '- Randomized exterior-building-door arrivals; visible appearance is allowed.\n  Existing conservative nighttime removal rules are retained.')
def section(start,end,body):
 global t
 a=t.index(start);b=t.index(end,a);t=t[:a]+body.rstrip()+'\n\n'+t[b:]
section('DAILY ROUTINE\n','REQUIREMENTS\n','''DAILY ROUTINE
At about 8 AM, the settlement selects its existing randomized daily target.
Children arrive individually after randomized 15–30 IN-GAME MINUTE intervals,
until the target is reached or the 7 PM arrival window closes. A first daytime
visit starts the sequence from the current time. Waiting, sleeping or fast
travel admits at most one overdue child; it does not replay a batch of arrivals.

Each arrival randomizes among the existing outdoor roaming points, then uses
a bounded vanilla local query for an ordinary exterior building door within
512 game units of a point. The child appears on that existing outdoor ground
point reasonably near the selected entrance, then uses the existing wandering
AI. This avoids guessed doorstep offsets and placement inside door meshes.
The last successful door is avoided when another queried door is available.
Selection is randomized; equal probability for every door is not promised.

No player distance, line of sight, door occupancy or unique-door requirement
blocks an arrival. You may walk, run, stand beside the door or look directly
at the child appearing. Visible pop-in is explicitly allowed. Door queries
occur only when an arrival is due, are limited to existing roaming points,
and never search the entire world. If local doors cannot be resolved, the
same settlement's existing valid outdoor ground points provide a randomized
fallback. No new roaming territory or guessed coordinates are introduced.

Children independently roam until about 7 PM, then travel into their assigned
building and sandbox indoors. Sitting, eating and other idles depend on native
AI, compatible activities and available furniture. After 3 AM, each child is
eligible for removal under the UNCHANGED safety rules. A nearby or watched
child may remain longer. Visible carry-overs still consume population capacity.

The existing game-time arrival timer retains its real-time counterpart for the
same saved deadline using the game's current TimeScale. Both callbacks use
the same worker and due-time check. Moving-player transition notifications
are coalesced rather than repeatedly delaying the same deferred wake. There
are no continuous distance checks or new recurring tasks.

Outdoor trips retain a 33.25% running-start chance and a 2.66–7.98 in-game-minute
run cap, both introduced in v1.2.3 as +33% relative changes. Reaching a destination,
native AI or threats can end a run early. Children still walk and pause.

Skyrim can deliver callbacks late after waiting, loading or fast travel.
No exact wall-clock delivery or immediate full population is promised. A late
afternoon first visit may not reach the full target before 7 PM.''')
section('UPDATING AND SAVES\n','COMPATIBILITY AND LIMITATIONS\n','''UPDATING AND SAVES
Replace the earlier installation; keep one enabled MoreBrats.esp and let this
archive's scripts win conflicts. Back up the save before testing. v1.1.0 remains
the stable public release; this candidate is built directly from v1.2.3 and
retains the ongoing v1.2.4 activation/callback repairs.

All existing FormIDs, NPC/reference identities, 200 variant meanings, serialized
field/property names and types, quest/AI records, population ranges and schemas
are preserved. A single new door-type FormList is appended. Its cached binding
and a few private scalar diagnostics initialize without a quest reset. Existing
residents retain their appearances; future arrivals use the unchanged donor RNG.

Shared city/town/village reconciliation already expires impossible saved
real-time deadlines. Whiterun's separate controller lacked that check; add the
same bounded expiry there only, for disabled pending actors.
Existing recovery handles disabled reservations;
children are not deleted, forcibly disabled or reset for this update. The existing
real-time timer also receives one expiry wake when pending activation reservations
fill the tracked array. Actual enabled children retain their saved state.

Typed-state tests cover upgrades from v1.1.0 through v1.2.3; actual ESS loading
and long-running save compatibility still require Skyrim testing. No new game,
quest reset or save cleaning is required by the intended implementation.

Removing an active scripted mod mid-playthrough is not guaranteed to be safe.
For rollback, restore the matching prior mod version and a backup save made
before this test. Removing files does not erase saved script instances or
actor state. Do not delete other mods' files or clean saves as a default fix.''')
section('PERFORMANCE\n','VANILLA APPEARANCE TEMPLATES\n','''PERFORMANCE
Provisional Papyrus assessment: MODERATE, based on code/compiled instructions,
not measured Skyrim timing. Routine enabled counting remains identical to
v1.2.3: at most 76 tracked native enabled checks across all 19 fully populated
controllers, instead of v1.2.1's 15,200 possible references. Empty remote
settlements retain dormant scheduling; only relevant settlements run arrivals.

The complete 200-variant slot audit runs before placement, rather than again
between MoveTo and activation. Full-pool audits/recovery are retained and can
still cause occasional expensive work. Random-door selection makes at most
one local query per existing road point in that due arrival opportunity,
stopping when it finds a different valid door. No door query runs during ordinary
roaming callbacks. Actual CPU load, queue delays, native Enable latency and
AI/pathfinding cost in heavily modded games need in-game profiling.

TESTING AND RELEASE STATUS
This is an unpublished v1.2.4 candidate. Compilation, two independent plugin
readers and an independent PEX decoder validate file structure and preserved
records. Fault-aware tests execute the compiled PEX with real ESP bindings.
Native Enable may be deliberately failed; movement changes simulated player
coordinates. Tests require actual modeled placement and enabled state, not
only tracking-array changes. Synthetic door locations are NOT Bethesda coordinates.

Skyrim has NOT been run for this build. Native timer delivery, real door queries,
rendering, real ESS migration, pathfinding, door traversal and performance remain
manual test requirements. Reservation scheduling gaps and repeated-wake delays were found;
the exact native trigger of the author's v1.2.3 failures is not established.

OPTIONAL SUPPORT INFORMATION
Controller status identifies v1.2.4; ScriptBuild, Build and DiagAIRevision become
1204 when a controller runs. Frozen alias/watchdog helpers may retain historical
labels. Schemas stay6 in Whiterun and7 elsewhere; they are storage versions.

IMPORTANT: MB_Debug reports WHITERUN wherever you are standing.
For Whiterun: set MB_Debug to 2
For Solitude: set MB_Solitude_Debug to 2
For Dragon Bridge: set MB_DragonBridge_Debug to 2
Other settlements: set MB_<Settlement>_Debug to 2, e.g. MB_Morthal_Debug.
Close the console and let normal callbacks run. The unchanged Whiterun watchdog
normally services MB_Debug at its next60-real-second pulse plus the deferred wake;
a busy Papyrus queue may delay it. No interior transition is required by the code.

The popup distinguishes live tracked enabled counts from the previous completed
sample, labels tracked/reserved slots, and shows disabled/enabled state per slot.
It also shows the selected exterior door or ground fallback and confirmed-enable
counter. Tracked/reserved is NOT proof that an actor is enabled or visible.
Reason42 means arrival is not due;44 means Enable returned but actor stayed
disabled. Historical arrival distance/LOS reasons40/41 are no longer used.
Stage16/reason1 is a busy-worker status. One debug request is consumed once;
normal gameplay has no diagnostic notifications.''')
section('FOCUSED v1.2.4 DEVELOPMENT PLAYTEST\n','CREDITS\n','''FOCUSED v1.2.4 DEVELOPMENT PLAYTEST
1. Back up an existing save, install the candidate, enable MoreBrats.esp and
   ensure all included scripts win conflicts. Keep only one version active.
2. In Whiterun and Solitude, walk/run continuously outdoors between8 AM and7 PM
   for at least60 in-game minutes. Expect gradual arrivals, not an instant crowd.
3. Stand beside an ordinary building door and look directly at the entrance.
   Arrival must not depend on your position, movement or viewing direction.
   Repeats are possible; check multiple arrivals for varied entrance areas.
4. Repeat in the other walled cities, Dragon Bridge and smaller settlements.
   First arrivals are due after15–30 game minutes, followed by further intervals.
   Solitude's larger target can take several in-game hours to fill.
5. After the daily target is reached, wait longer and revisit: no extra children
   or duplicates should appear. Native door lookup failure may use a street fallback.
6. Fast travel, wait/sleep past deadlines, and save/reload mid-sequence. Confirm
   pending arrivals resume gradually without needing an interior transition.
7. Test existing v1.1.0 and v1.2.x saves, including saved disabled reservations;
   do not reset quests or clean saves. Existing visible residents should remain.
8. Observe the unchanged7 PM native building-entry routine, then watched3 AM
   retention and safe removal after leaving the relevant cell.
9. Check varied donors/outfits and unchanged walking, running and sandboxing.
   If a failure occurs, the named status command is optional; no screenshot is
   required to use the mod.''')
# Add spaces around compact timing/version words in new prose.
t=t.replace('Schemas stay6','Schemas stay 6').replace('Whiterun and7','Whiterun and 7').replace('next60-','next 60-').replace('Reason42','Reason 42').replace(';44','; 44').replace('reasons40/41','reasons 40/41').replace('Stage16/reason1','Stage 16/reason 1').replace('between8','between 8').replace('and7 PM','and 7 PM').replace('least60','least 60').replace('after15','after 15').replace('unchanged7','unchanged 7').replace('watched3','watched 3')
(RT/'README.txt').write_text(t)
entry=f'''\n\nMore Brats — v1.2.4 Changelog — {date}
PRIVATE PLAYTEST CANDIDATE; v1.1.0 remains the stable public release.

REQUESTED DOOR-BASED ARRIVALS
- Replaced arrival distance/LOS and peer-spacing vetoes with randomized ordinary
  exterior-building-door selection around the same existing roaming points.
  Player position, walking/running, viewing direction and door occupancy do not
  gate placement. Visible appearance is permitted by the requested design.
- A bounded native local query uses a new17-entry ordinary building-door-type
  FormList. It excludes city gates, dungeon doors and trapdoors. A random existing
  road order and vanilla random-door query choose entrances independently per
  arrival; avoid the last successful door if another is found. Equal weighting
  across every city door is not asserted. No worldwide discovery or new manager.
- Place on the existing outdoor ground point within512 units of that entrance;
  do not guess door offsets or move inside meshes. If no local door resolves,
  use a randomized valid outdoor point in the same settlement instead of stalling.
  No fixed placed door references, new coordinates or door overrides were added.
- Retained15–30 in-game-minute arrival deadlines, one child per opportunity,
  daily caps,19 settlements,40 donors,200 variants and all appearance indices.

TARGETED ACTIVATION/CALLBACK REPAIRS RETAINED
- Tracking arrays can contain disabled activation reservations. The old code
  calls EnableNoWait and returns with a pending reservation (stage11, not a
  confirmed success). Now use vanilla Enable(False), verify IsDisabled after it returns,
  and only then record a confirmed arrival. A failed enable reports reason44,
  releases its reservation and retains a future arrival opportunity.
- Add impossible old-session enable-deadline expiry to Whiterun's separate
  controller. The shared city/town/village controllers ALREADY had this check;
  preserve it there. Expire only disabled pending bookkeeping, not active actors.
  A full array of pending enables receives one expiry wake through the existing
  timer instead of suppressing every arrival wake.
- Coalesce repeated transition notifications so moving-player events cannot
  repeatedly push the same short deferred wake into the future.
- Run the existing full200-variant slot audit before actor/door selection,
  eliminating its second placement-time copy. Keep ownership/capacity/duplicate
  fences. Do not perform roaming updates on still-disabled reservations.
- Live status distinguishes enabled actors, tracked/reserved slots, previous
  completed sample, individual activation states, selected door/fallback and
  confirmed enables. Controller build labels are1204; storage schemas unchanged.

EVIDENCE AND PRESERVATION
- These are demonstrated code-path defects and controlled test failures, not
  proof of the exact native engine cause of the reported v1.2.3 session. The
  reported enabled value was explicitly a last-completed sample and may be stale.
- All19,941 previous FormIDs retained; all old NPC/reference/quest/package/VMAD
  payloads unchanged. Only58 display globals/header identify the candidate.
  Append one FLST at local0x2221E0; no new actors, placed refs or script properties.
- Four controller PEX rebuilt; five helper PEX and startup SEQ byte-identical.
  Existing variable/property names, types/defaults, pool indices and schemas
  retained. Nighttime removal, orphan recovery, appearance RNG, destinations,
  AI packages and v1.2.3's+33% running behavior retained.
- Compiled-bytecode/native-boundary tests cover all19, moving/visible players,
  randomized/reused doors, local-query fallback, timed callbacks, native-enable
  failure, disabled reservations, all200 variants and typed old-save states.
  Real Skyrim door queries, graphics, AI/pathfinding and ESS upgrades are untested.
- Routine counting stays at most76 checks across all settlements. Full recovery
  still scans15,200 potential references occasionally. Papyrus estimate: MODERATE,
  based on code, not runtime benchmarks. No new dependencies or recurring polling.

PLAYTEST: Remain outdoors in Whiterun, Solitude and Dragon Bridge for60+ game
minutes between8 AM and7 PM while walking/running or watching entrance areas.
Allow further intervals to reach the daily target; check no excess arrivals,
repeat visits, existing-save reloads, unchanged7 PM entry and post3 AM removal.
'''
for a,b in [('new17','new 17'),('within512','within 512'),('Retained15','Retained 15'),('caps,19','caps, 19'),('settlements,40','settlements, 40'),('donors,200','donors, 200'),('reason44','reason 44'),('full200','full 200'),('are1204','are 1204'),('All19,941','All 19,941'),('Only58','Only 58'),('local0x','local 0x'),("v1.2.3's+33%","v1.2.3's +33%"),('all19','all 19'),('all200','all 200'),('most76','most 76'),('scans15,200','scans 15,200'),('for60+','for 60+'),('between8','between 8'),('and7 PM','and 7 PM'),('unchanged7','unchanged 7'),('post3','post-3')]:entry=entry.replace(a,b)
history=(W/'build/v1.2.3/runtime/CHANGELOG.txt').read_bytes();(RT/'CHANGELOG.txt').write_bytes(history+entry.encode())
assert (RT/'CHANGELOG.txt').read_bytes().startswith(history)
for p in [RT/'README.txt',RT/'CHANGELOG.txt']:
(R/'documentation.json').write_text(json.dumps({'date':date,'prior_changelog_bytes_preserved':len(history),'historical_release_unchanged':True},indent=2)+'\n')
print('Playtest docs prepared; date='+date+'; cumulative history preserved byte-for-byte.')
