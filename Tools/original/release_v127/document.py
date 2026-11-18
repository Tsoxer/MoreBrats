from pathlib import Path
import re,datetime
W=Path('work');R=W/'build/v1.2.7';RT=R/'runtime'
date="11-18-2026"
(R/'publication-date.txt').write_text(date+'\n')
t=(W/'build/v1.2.6/runtime/README.txt').read_text().replace('v1.2.6','v1.2.7').replace('1206','1207')
t=t.replace('''- Independent race, gender and outfit rolls, followed by an appearance donor
  from the selected race/gender group. Races have an equal 25% chance, genders
  50% each and outfit colors 20% each. Repeats are normal.''','''- Race, gender and outfit start with the existing independent rolls: 25% per
  race, 50% per gender and 20% per clothing color. Each active settlement avoids
  duplicate vanilla appearance donors, even when outfits differ. Outfit repeats
  are allowed. If a race/gender group runs out of unused donors, another available
  group is chosen. The same donor remains eligible in other settlements.''')
t=t.replace('''- Gradual outdoor arrivals at randomized 3–7 in-game-minute intervals, usually
  near ordinary building entrances, with suitable public streets as fallback.''','''- Gradual outdoor arrivals at randomized 3–7 in-game-minute intervals, usually
  near ordinary building entrances, with suitable public streets as fallback.
- Entering a settlement interior also prepares the day's remaining children at
  the original street markers. Both methods share one daily target and cap.''')
t=t.replace('''Arrivals can be visible, including when you are looking at an entrance.''','''Arrivals can be visible, including when you are looking at an entrance.

Entering a settlement interior provides a second arrival opportunity: the
remaining population is prepared at the same street markers used by v1.1.0,
without waiting for each gradual-arrival interval. For example, a target of
five with three children already present permits only two more. Exiting and
re-entering cannot add another full population or reroll that day's target.
A very quick entry/exit can leave this preparation queued for the next update.
Street arrivals choose existing public markers without preferring a door.''')
a=t.index('v1.2.7 ARRIVAL REPAIR\n');z=t.index('UPDATING AND SAVES\n',a)
t=t[:a]+'''v1.2.7 LOCAL APPEARANCE VARIETY
Donor uniqueness is local to each settlement's active population. Whiterun may
have Blaise, Braith and Lars while Riften independently has the same three.
Within either settlement, two active children cannot newly select Braith's
FormID, even if one wears red and the other yellow. Different vanilla donors
may still look similar, especially without appearance replacers.

Existing residents are preserved on upgrade. Duplicates already active in an
older save are not removed or changed mid-day; future arrivals avoid their
occupied donors, and the normal daily lifecycle clears those legacy duplicates.

The v1.2.6 arrival-latency repairs are retained. Normal outdoor arrivals remain
3–7 IN-GAME MINUTES apart. Interior preparation is a bounded alternative using
the same controller, references and tracking. No extra population manager,
background loop, dependency, NPC or AI-package record is introduced.

'''+t[z:]
a=t.index('PLAYTEST AND OPTIONAL DIAGNOSTICS\n');z=t.index('CREDITS\n',a)
t=t[:a]+'''PLAYTEST AND OPTIONAL DIAGNOSTICS
Back up your save and replace the previous build, allowing all included scripts
to win file conflicts. Test between 8 AM and 7 PM:
1. Stay outdoors and confirm the existing gradual door-area arrivals.
2. With a partly filled population, enter a shop or inn and return outdoors.
   Only the remaining slots should fill at the original public street markers.
3. Repeat entry/exit several times. The same daily target must remain in effect.
4. Check donor identities with More Informative Console if available; different
   outfit colors do not make the same donor eligible twice in one settlement.
5. Visit another settlement. A donor used elsewhere may still appear there.
6. Confirm the unchanged 7 PM indoor routine and safe post-3 AM disappearance.

Optional console status: set MB_Debug to 2 for Whiterun; use named settlement
prefixes elsewhere, for example set MB_Riften_Debug to 2. Build 1207 reports
interior preparation state alongside existing arrival timestamps. Reason 45
means no unused bound donor; 46 means an existing resident could not be identified.
Status commands and More Informative Console are not required for normal play.

Automated checks cover final ESP/PEX, all 19 populations, original street
bindings, 200 appearance mappings, shared caps, transitions and typed old state.
They do not test actual Skyrim rendering, native paths, callbacks or ESS loading.
This unpublished v1.2.7 build requires Skyrim playtesting.

'''+t[z:]
t=t.replace('''There is no
per-frame script loop or unlimited creation of new actor references.''','''There is no
per-frame script loop or unlimited creation of new actor references. Donor
filtering inspects the small tracked population when an arrival is attempted.
Interior preparation can produce a bounded burst of up to the remaining daily
slots; it creates no additional scheduled worker or full-pool routine scan.''')
(RT/'README.txt').write_text(t)
history=(W/'build/v1.2.6/runtime/CHANGELOG.txt').read_text()
entry=f'''\n\nMore Brats — v1.2.7 Changelog — {date}
Unpublished development build; stable public release remains v1.1.0.

TWO REQUESTED ADDITIONS
- Prevent newly generated children from sharing a vanilla appearance-donor
  FormID within the same settlement's active population. Five outfits belonging
  to one donor count as one identity. Duplicate clothing colors remain allowed.
  The same donor can be present in different settlements at the same time.
- Restore interior-entry population preparation alongside v1.2.6's gradual
  outdoor door arrivals. Prepare remaining slots at the unchanged v1.1.0 street
  markers, without a door preference or an additional per-child interval.
- Both paths use the SAME dailyPopulation, residents, fixed actor references,
  reservations, worker lease and activation checks. An interior opportunity
  fills only the shortfall; it never rolls a second population or exceeds the
  day's selected target. Repeated entry/exit and queued callbacks share that cap.
- Capture a quick interior visit for the existing deferred worker. Loading or
  waiting inside a relevant interior can also prepare the current daytime roll.
  Unrelated interiors, the 7 PM cutoff and the Skaal quest gate remain respected.

APPEARANCE AND SAVE DETAILS
- Resolve donor identity from immutable actor-reference IDs and existing pool
  bindings, rather than trusting selectedVariant after a daily reset or adoption.
  Handle signed Papyrus FormIDs at high load-order indices. All 15,200 reference
  mappings are verified against the actual NPC TPLT donor FormIDs.
- Preserve the existing race/gender/outfit rolls and all 40 donors/200 variants.
  A duplicate donor is replaced by an unused donor in that race/gender group,
  keeping the outfit. If the group is exhausted, choose another available group.
  Strict donor uniqueness necessarily conditions race/gender availability.
- Retain existing children and all saved fields/properties. Older already-active
  duplicates are not forcibly removed or changed; new arrivals do not add to
  them. They clear through the normal lifecycle. No new game or quest reset.
- Add only an interior-opportunity flag and cycle number to serialized state.
  A temporary 40-entry local donor mask is built only during an arrival attempt.

PRESERVATION AND VALIDATION
- All 19,942 record identities, NPC/reference/AI/quest payloads, populations,
  masters, street/door destinations, running, 8 AM–7 PM arrival window, 7 PM indoor
  routine and post-3 AM retirement rules remain. Only build globals/description
  identify v1.2.7/1207. Four controller PEX rebuilt; five helper PEX and SEQ unchanged.
- v1.2.6 timing and scan reductions remain. Routine enabled counting is still
  bounded by 76 tracked checks at maximum populations; no new polling cadence.
  Interior preparation is bounded by the existing daily target, at most nine.
- Final ESP/PEX checks cover all 19 settlements, donor identities, outfit repeats,
  original street bindings, gradual/interior paths, quick visits, repeated exits,
  failed enabling, save-state transfers, caps and the unchanged night lifecycle.
- Explicit overlapping-callback case: Whiterun target five, three gradual arrivals
  plus two interior arrivals, with a callback during enabling; total remains five.
- Papyrus assessment remains Moderate, based on code. Donor selection adds bounded
  local work and at most eight other resident ID reads per arrival. Interior
  preparation can create a short batch; actual queue latency is not benchmarked.
- Tests execute compiled instructions with controlled native calls and typed
  save states. Actual Skyrim callbacks, rendering, pathfinding, door transitions
  and ESS loading still require the author's v1.2.7 playtest.
'''
(RT/'CHANGELOG.txt').write_text(history+entry)
for p in [RT/'README.txt',RT/'CHANGELOG.txt']:
print('v127 documentation prepared; prior cumulative history retained verbatim; date',date)
