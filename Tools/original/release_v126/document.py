from pathlib import Path
import json,re
W=Path('work');R=W/'build/v1.2.6';RT=R/'runtime';date=(R/'publication-date.txt').read_text().strip()
readme=Path('outputs/MoreBrats-v1.2.5-Release-Docs/README.txt').read_text().replace('MORE BRATS v1.2.5','MORE BRATS v1.2.6').replace('Release date: 11-17-2026','Playtest build date: '+date).replace('Free public release','Unpublished development build — stable public release: v1.1.0')
readme=readme.replace('UPDATING AND SAVES\n','''v1.2.6 ARRIVAL REPAIR
This build retains the 3–7 IN-GAME MINUTE arrival design. It removes a redundant
200-reference check from healthy arrivals and avoids requesting another complete
pool census simply because a healthy saved controller loaded. Empty remote
settlements defer setup until relevant. Full initialization, explicit recovery,
invalid-state recovery and periodic consistency checks remain available.

An arrival deadline and successful activation are different events. Skyrim's
callbacks and native operations can finish late. First-time initialization or
repair of an old/incomplete save can still take longer; this build does not
promise an exact real-time deadline. No new polling loop or dependency is added.

UPDATING AND SAVES
''')
readme=readme.replace('CREDITS\n','''PLAYTEST AND OPTIONAL DIAGNOSTICS
Back up your save and replace the preceding test build. Test all five walled
cities and several open-world settlements between 8 AM and 7 PM. Stay outdoors
and move normally. Look for one child per 3–7-minute scheduled interval until
the daily target fills; record unusually late actual appearances. Hop between
cities and revisit them. Confirm the unchanged 7 PM routines and safe post-3 AM
removal. Real Skyrim validation of v1.2.6 is still required.

Optional console status requests: set MB_Debug to 2 for Whiterun; for other
settlements use their prefix, for example set MB_Riften_Debug to 2 or
set MB_DragonBridge_Debug to 2. These are not required for normal play. Status
shows build 1206 and the last arrival's due, attempted and confirmed-enabled
game-day timestamps. A value of zero means that event has not been recorded.
A selected/tracked reference alone is not proof of successful activation.

Compiled-code and structural tests use controlled native calls; they do not
verify real Skyrim callback latency, save loading, rendering or pathfinding.
Papyrus classification remains Moderate as a code-based estimate.

CREDITS
''')
(RT/'README.txt').write_text(readme)
old=(W/'build/v1.2.5/runtime/CHANGELOG.txt').read_text()
entry=f'''\n\nMore Brats — v1.2.6 Changelog — {date}
Unpublished development build; stable public Nexus release remains v1.1.0.

ARRIVAL LATENCY FINDINGS
- Author testing found delayed but eventually successful arrivals. The delay
  was first narrowed to walled cities; subsequent testing also found inconsistent
  timing in unwalled settlements. No appearance-pool failure was established.
- In the final v1.2.5 compiled code, a normal warm first arrival performed 210
  IsDisabled checks, including a redundant 200-appearance slot scan before Enable.
  A controlled load of 19 initialized, empty controllers performed 15,210 such
  checks. These are native-call counts, not measured Skyrim execution times.
- Same-cycle daytime departure from a settlement does not itself request actor
  deletion. The existing retirement rules depend on the cycle/time and safety.
- Native callback delivery is not an exact clock; game-time events can arrive
  after waits or fast travel. The code costs are confirmed, but their precise
  share of the author's 30–60-minute delay has not been measured in Skyrim.

CORRECTIONS
- For fully bound, audited pools, use existing tracked state and the serialized
  worker instead of scanning all 200 unused appearances before every arrival.
  The chosen actor must still be disabled and untracked before placement/enable.
- On healthy save loads, validate tracked residents without unconditionally
  rebinding and auditing the complete appearance pool. Missing storage, invalid
  membership, disabled/pending reservations, unfinished workers, orphan flags and
  explicit repair retain full reconciliation. No quest or actor reset is used.
- Defer expensive setup in empty, irrelevant settlements. Saved repair requests
  remain pending and are honored before their next relevant arrival.
- Defer an overdue routine census until a pending arrival sequence finishes.
  Explicit/incomplete-state recovery still runs before arrivals; full consistency
  checks remain. Refresh the game clock after a yielding census.
- Record the saved deadline, attempt start and confirmed enabled time separately.
  The successful time is written only after native Enable returns and IsDisabled
  confirms activation. Normal play has no additional notifications.

PRESERVATION
- All 19,942 existing FormIDs and record identities, NPCs, references, quests,
  aliases, packages, factions, masters, appearance mappings and population ranges
  remain. Only 58 build globals and the plugin description identify v1.2.6/1206.
- Four controller PEX files changed; five helper PEX and startup SEQ are identical.
  All old serialized names/types/defaults and schemas 6/7 remain. Added only one
  load-check flag and three diagnostic timestamps. Existing residents are retained.
- Forty donors, 200 variants, race/gender/outfit RNG, door-area placement, enhanced
  running, roaming, evening travel and nighttime retirement rules are unchanged.
- The arrival interval remains 3–7 IN-GAME MINUTES, not real-world seconds.
  No new script, manager, polling cadence, custom asset or dependency was added.

VALIDATION AND REMAINING TESTS
- Independent plugin/PEX inspection; actual final bytecode exercised with final
  ESP bindings for outdoor arrivals in all 19 settlements, moving players,
  real-time fallback events, repeat city visits, save-state upgrades, failed native
  enabling, recovery/adoption, caps, appearances and the existing night lifecycle.
- Routine enabled counting remains at most 76 native checks across all maximum
  populations. In the comparable warm first-arrival test, checks fell from 210
  to 11. Initialization and exceptional recovery still do more work.
- Papyrus estimate remains Moderate. Injected native delays and typed-state
  transfers are simulations, not benchmarks or actual ESS/Skyrim execution.
- Test v1.2.6 in Skyrim before any public release. In particular, compare scheduled
  and actual arrivals while hopping between Whiterun, Riften and Windhelm, then
  test Solitude, Markarth and open-world settlements without interior triggers.
'''
(RT/'CHANGELOG.txt').write_text(old+entry)
for p in [RT/'README.txt',RT/'CHANGELOG.txt']:
(R/'research-sources.json').write_text(json.dumps({'sources':[{'title':'Creation Kit OnUpdateGameTime documentation, attributed Papyrus Index mirror','url':'https://papyrus.bellcube.dev/skyrimse/script/form/event/onupdategametime/','finding':'Game-time callbacks may be delivered late after sleep/wait/fast travel and collapse missed intervals.'},{'title':'Creation Kit single-update registration contract, attributed Papyrus Index mirror','url':'https://papyrus.bellcube.dev/skyrimse/script/form/function/registerforsingleupdate/','finding':'Unregister an unelapsed real-time timer before changing its registration; existing v125 safeguard preserved.'},{'title':'Papyrus Tweaks NG author documentation','url':'https://www.nexusmods.com/skyrimspecialedition/mods/77779','finding':'Documents synchronization overhead of vanilla native calls. No dependency on this mod is introduced.'}], 'limits':'Direct CK host returned403. Documentation read through attributed API reference mirror; mod-author discussion used for native-call synchronization. No frame timing or queue latency measured in Skyrim.'},indent=2)+'\n')
print('One README and complete unchanged historical changelog with appended v126 entry prepared.')
