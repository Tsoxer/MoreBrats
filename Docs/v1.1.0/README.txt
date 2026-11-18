MORE BRATS v1.1.0
Release date: 11-16-2026
Author: Tsoxer
Skyrim Special Edition / Anniversary Edition — tested target: 1.6.1170
Free public release

ABOUT MORE BRATS
More Brats brings a little more everyday life to Skyrim's streets. Generic
human children explore 19 settlements during the day, head indoors in the
evening, and make way for a newly randomized population the following morning.
They are ordinary background residents named Child, with no added quests,
personal stories, follower system, or custom dialogue.

FEATURES
- Each settlement selects its own daily population within the ranges below.
- Each child independently selects a genuine vanilla child race: Nord,
  Imperial, Breton, or Redguard (25% each); male or female (50% each); and one
  of five vanilla outfits: red, blue, green, grey, or yellow (20% each).
  All 40 combinations are eligible in every settlement. Repeats are normal.
- Independent trips between public streets, occasional running, and short
  pauses for vanilla idles, sitting, and sandbox activities.
- Evening visits to an inn, house, or communal hall, using native Skyrim AI.
- Conservative arrivals and removals intended to avoid visible materialization
  or disappearance. Existing visible children can delay the next day's arrivals.
- Vanilla assets; no custom meshes, textures, animations, or voice files.

SUPPORTED SETTLEMENTS
The ranges are daily targets, not a promise that every child is immediately
visible. Children move around, may already be indoors, and can arrive gradually.

Five walled cities       Children    Evening destination
Whiterun                3–6         The Bannered Mare
Markarth                4–6         Silver-Blood Inn
Riften                  4–7         The Bee and Barb
Windhelm                4–7         Candlehearth Hall
Solitude                6–9         The Winking Skeever

Four unwalled capitals
Dawnstar                3–5         Windpeak Inn
Falkreath               3–5         Dead Man's Drink
Morthal                 2–4         Moorside Inn
Winterhold              1–3         The Frozen Hearth

Ten smaller settlements
Riverwood               1–2         Sleeping Giant Inn
Rorikstead              1–2         Frostfruit Inn
Ivarstead               2–3         Vilemyr Inn
Karthwasten             1–2         Karthwasten Hall
Dragon Bridge           2–4         Four Shields Tavern
Shor's Stone            1–2         Filnjar's House
Kynesgrove               1–2         Braidwood Inn
Darkwater Crossing      1–2         Verner and Annekke's House
Stonehills              1–2         Sorli's House
Skaal Village           1–3         Skaal Village Greathall

Skaal Village begins participating after its liberation during The Fate of the
Skaal (the relevant vanilla quest stage, or quest completion). Raven Rock and
Tel Mithryn are not included.

DAILY ROUTINE
Around 8 AM, the day's children become eligible to appear at public outdoor
destinations. They independently roam until about 7 PM, then travel toward
their assigned building and sandbox indoors. Sitting, eating, and other idles
depend on available furniture and compatible vanilla activities.

After 3 AM, each child becomes eligible for safe removal. A nearby or watched
child can remain longer; a suitable cell transition provides a reliable chance
for removal. The next eligible daily cycle rerolls population and appearances.

These times are approximate and use in-game time. Cell loading, visibility
safeguards, waiting, and Skyrim's script scheduling can delay activation. On a
fresh installation or first visit, children may not be visible immediately.
Delayed arrivals were observed during development and later recovered. Allow
normal gameplay updates to run; an indoor visit can provide a safe opportunity.
No console command is required for ordinary play.

REQUIREMENTS
- Skyrim Special Edition / Anniversary Edition, with official master files
  Skyrim.esm, HearthFires.esm, and Dragonborn.esm and their normal game assets.
  Hearthfire and Dragonborn are included with Skyrim SE/AE.
- Developed and author-tested for executable 1.6.1170. Other versions and VR
  have not been verified for this release.
- No SKSE, Address Library, SPID, or other external framework is required.

INSTALLATION
Close Skyrim before installing or updating. Keep a backup of your save.

Mod Organizer 2: install MoreBrats-v1.1.0.zip as an archive, enable the mod,
and enable MoreBrats.esp in the Plugins pane. Launch through MO2 as usual.

Vortex: install the archive, enable it, deploy, and enable MoreBrats.esp.

Manual: extract the archive directly into Skyrim's Data directory. The archive
already uses Data-root paths: MoreBrats.esp, Scripts/*.pex, and Seq/MoreBrats.seq.
Do not create an extra nested Data directory. The two text files are documents.

UPDATING AND SAVES
Replace the earlier installation; keep only one enabled copy of MoreBrats.esp
and let this release's scripts win any conflicts with an older More Brats copy.
Upgrading from v1.0.0 retains all previous FormIDs, properties, saved-state
types, population data, and More Brats gameplay logic. Existing children keep
their identities and appearances; new races join future daily selections.
New appearance bindings use stable-ID recovery on existing saves.
No new game, quest reset, or save cleaning
is required by this update. Installation into an existing playthrough is supported
by the existing initialization and recovery system; keep a backup regardless.

Removing an active scripted mod mid-playthrough is not guaranteed to be safe.
The cleanest rollback is to restore a save from before installation. If removing
it, close the game, uninstall through your manager, or remove only this mod's
ESP, nine MB_*.pex files, and Seq/MoreBrats.seq. Do not delete other mods' files.
Removing files does not remove script instances or actor state already in a save.
There is no dedicated uninstall procedure or promise of safe save cleaning.

COMPATIBILITY AND LIMITATIONS
This is an ordinary ESP, not an ESL-flagged plugin. It adds its own records and
does not override vanilla NPCs, navmeshes, doors, ownership, or city layouts.
Vanilla templates and assets provide the children's appearances and behavior.
Furniture use, door access, and movement still depend on Skyrim's native AI.

The city routes target the vanilla layouts. Open Cities support is not provided.
Settlement/interior/navmesh overhauls and child appearance replacers need testing
with your load order; no universal compatibility claim or required patch is made.
No runtime outfit-swapping framework is required. Compatibility with every
third-party clothing distributor has not been verified.

PERFORMANCE
Assessment: moderate Papyrus overhead, with additional native NPC AI work where
children are loaded. Scheduled checks and player events manage fixed reusable
pools; there is no per-frame script loop or unlimited actor creation. All 19
settlements have background management, with less frequent checks when distant.
The combined normal daily target is 42–76 children across the world, not all
loaded together. Nearby children and evening gatherings add local pathfinding
and furniture demand. Busy script queues can delay responses. Generally suitable
for modded games, but no FPS, latency, memory, or 500-mod benchmark is claimed.

v1.1.0 adds 2,280 disabled reusable references for appearance choices, for 3,040
total. The active population limits and AI packages are unchanged. Pool scans
now cover four times as many references, with additional fixed appearance
storage. This adds script work and persistent state; it is not a zero-cost
change. No controllers, timers, polling frequency, or native AI population were
added. Exact performance and save-size differences remain unmeasured.

TESTING AND RELEASE STATUS
Tsoxer has accepted v0.5.1 as the working gameplay baseline after actual Skyrim
testing. All ten smaller settlements passed individual daytime spawning checks;
nighttime entry has been observed in multiple cases. This is not a claim of
exhaustive overnight and multi-day verification for every settlement/load order.

Tsoxer subsequently confirmed v1.0.0 as the working release. v1.1.0 extends
its appearance pools while preserving More Brats spawning safety, roaming,
schedules, destinations, AI packages, population limits, and controller timing.
Independent checks cover the ESP, script/property bindings, PEX bytecode,
startup data, and package layout. Compiled logic tests use mocked engine calls;
they do not prove native pathfinding, door traversal, appearance rendering, or
performance. The final v1.1.0 archive has not been run in Skyrim in the cloud.

OPTIONAL SUPPORT INFORMATION
Live status messages and traces identify v1.1.0. After a controller runs, its
ScriptBuild, Build, and DiagAIRevision values are 1100. Schema 6 in Whiterun and
schema 7 elsewhere remain intentionally unchanged; these are storage versions.
Older phase globals or values already stored in a save are not migration signals.

For Whiterun, "set MB_Debug to 2" requests one status popup at the next callback.
Elsewhere use MB_<Settlement>_Debug, e.g. "set MB_Morthal_Debug to 2" or
"set MB_DragonBridge_Debug to 2". Close the console to let updates run. This is
one request, not continuous monitoring. Reason 14 reports deferred exterior
placement into loaded cells; stage 16/reason 1 reports a busy callback. Include
the full status, game time, location, and relevant mods in a bug report. Do not
reset quests as a troubleshooting default.


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

CREDITS
Author and in-game testing: Tsoxer.
Skyrim and its vanilla assets: Bethesda Game Studios.
Development tools include Mutagen, Caprica, and independent plugin/PEX readers.
No Bethesda game files or third-party mod assets are redistributed. This free
fan-made mod is not officially endorsed by Bethesda or Nexus Mods.
