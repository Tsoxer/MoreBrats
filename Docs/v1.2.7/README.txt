MORE BRATS v1.2.7
Playtest build date: 11-18-2026
Author: Tsoxer
Skyrim Special Edition / Anniversary Edition — target: 1.6.1170
Build — stable public release: v1.2.7

ABOUT MORE BRATS
More Brats brings a little more everyday life to Skyrim's streets. Generic
children explore 19 settlements during the day, head indoors in the evening,
and make way for a newly randomized population the following morning.

Every added NPC is named Child. They are ordinary background residents, with
no added quests, personal stories, follower system or custom dialogue.

FEATURES
- Independently randomized daily populations for each supported settlement.
- Genuine Nord, Imperial, Breton and Redguard children, with male and female
  appearances available in every settlement.
- Forty vanilla appearance templates and five clothing colors: red, blue,
  green, grey and yellow. All 200 appearance/outfit combinations are eligible.
- Race, gender and outfit start with the existing independent rolls: 25% per
  race, 50% per gender and 20% per clothing color. Each active settlement avoids
  duplicate vanilla appearance donors, even when outfits differ. Outfit repeats
  are allowed. If a race/gender group runs out of unused donors, another available
  group is chosen. The same donor remains eligible in other settlements.
- Gradual outdoor arrivals at randomized 3–7 in-game-minute intervals, usually
  near ordinary building entrances, with suitable public streets as fallback.
- Entering a settlement interior also prepares the day's remaining children at
  the original street markers. Both methods share one daily target and cap.
- Independent wandering, walking, occasional running, brief pauses, sitting
  and other activities supported by Skyrim's native AI.
- Evening visits to an inn, house or communal hall, followed by safe overnight
  removal and a new daily population.
- Vanilla assets throughout; no custom meshes, textures, animations or voices.

SUPPORTED SETTLEMENTS
These ranges are daily targets. Children arrive gradually and move around;
not every child will necessarily be visible when you first enter a settlement.

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
Kynesgrove              1–2         Braidwood Inn
Darkwater Crossing      1–2         Verner and Annekke's House
Stonehills              1–2         Sorli's House
Skaal Village           1–3         Skaal Village Greathall

Skaal Village participates after its liberation during The Fate of the Skaal.
Raven Rock and Tel Mithryn are not included.

DAILY ROUTINE
8 AM: The settlement's daily population becomes eligible to arrive.

8 AM–7 PM: Children arrive individually at randomized 3–7 in-game-minute
intervals until the daily target is reached or the arrival window closes.
They independently wander through the settlement's public areas. You can
remain outdoors, walk, run or stand still; no interior transition is required.
Arrivals can be visible, including when you are looking at an entrance.

Entering a settlement interior provides a second arrival opportunity: the
remaining population is prepared at the same street markers used by v1.1.0,
without waiting for each gradual-arrival interval. For example, a target of
five with three children already present permits only two more. Exiting and
re-entering cannot add another full population or reroll that day's target.
A very quick entry/exit can leave this preparation queued for the next update.
Street arrivals choose existing public markers without preferring a door.

Around 7 PM: Children begin traveling to their assigned evening building.
Once inside, they use normal sandbox activities and available furniture.
Sitting, eating and other idles depend on compatible vanilla activities.

After 3 AM: Children become eligible for safe removal. A nearby or watched
child can remain longer. Leaving the relevant cell provides an opportunity
for removal without an obvious disappearance in front of the player.

The next daily cycle rerolls population and appearances. Children carried
over from the previous day still count toward the population limit.

All schedule times use in-game time. Arrival intervals are scheduling targets;
cell loading, initialization, waiting, fast travel or a busy script queue can
make an arrival occur later. No immediate full population or exact on-screen
arrival time is promised. A late-afternoon visit may not reach the full target
before 7 PM. No console command is required for ordinary play.

REQUIREMENTS
- Skyrim Special Edition / Anniversary Edition and the official master files
  Skyrim.esm, HearthFires.esm and Dragonborn.esm, with their normal game assets.
  Hearthfire and Dragonborn are included with Skyrim SE/AE.
- Developed for executable 1.6.1170. Other executable versions and VR have not
  been verified for this release.
- No SKSE, Address Library, SPID or other external framework is required.

INSTALLATION
Close Skyrim before installing or updating. Keep a backup of your save.

Mod Organizer 2: install the downloaded More Brats archive, enable the mod,
and enable MoreBrats.esp in the Plugins pane. Launch through MO2 as usual.

Vortex: install the archive, enable it, deploy, and enable MoreBrats.esp.

Manual: extract the archive directly into Skyrim's Data directory. Its runtime
paths are MoreBrats.esp, Scripts/*.pex and Seq/MoreBrats.seq. Do not create an
extra nested Data directory. README.txt and CHANGELOG.txt are documentation.

v1.2.7 LOCAL APPEARANCE VARIETY
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

UPDATING AND SAVES
Replace the earlier installation. Keep only one enabled MoreBrats.esp and make
sure this version's nine compiled scripts win conflicts with older copies.

The update preserves existing FormIDs, resident identities, appearance indices
and compatible saved state. Existing children retain their appearances; new
appearance choices join future selections. Existing-save installation and
upgrades are supported without a new game, quest reset or save cleaning.
Keep a backup before updating.

UNINSTALLATION
Removing an active scripted mod mid-playthrough is not guaranteed to be safe.
The safest rollback is to restore the matching earlier mod version and a save
made before updating, or a save from before More Brats was installed.

To remove the files, close Skyrim and uninstall through your mod manager.
For a manual installation, remove only MoreBrats.esp, the nine included MB_*.pex
files and Seq/MoreBrats.seq. Do not delete other mods' files. Removing the files
does not erase script instances or actor state already stored in a save.

COMPATIBILITY
More Brats is an ordinary ESP, not an ESL-flagged plugin. It adds its own records
and does not override vanilla NPCs, navmeshes, doors, ownership or city layouts.
Movement, door access and furniture use rely on Skyrim's native AI.

Routes and destinations use the vanilla settlement layouts. Open Cities is
not supported. Settlement, interior and navmesh overhauls should be checked
in your load order, particularly around arrival points and evening buildings.

Vanilla child appearances and assets are reused through NPC templates. Mods
that alter the donor children may also affect these appearances; compatibility
with individual replacers depends on their implementation. No custom FaceGen
files or runtime outfit-swapping framework are supplied or required.

PERFORMANCE
Assessment: moderate Papyrus overhead, based on the implementation rather than
an in-game benchmark. Scheduled events and fixed reusable references manage
the populations, with routine checks focused on tracked children. There is no
per-frame script loop or unlimited creation of new actor references. Donor
filtering inspects the small tracked population when an arrival is attempted.
Interior preparation can produce a bounded burst of up to the remaining daily
slots; it creates no additional scheduled worker or full-pool routine scan.

The combined daily target is 42–76 children across all 19 settlements. Nearby
children add native AI, pathfinding and furniture demand. Initialization and
recovery can require additional script work, and busy queues can delay updates.
Actual impact depends on loaded actors and the rest of the modlist; no specific
FPS, latency, memory or large-load-order performance guarantee is made.

PLAYTEST AND OPTIONAL DIAGNOSTICS
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

CREDITS
Author: Tsoxer.
Skyrim and its vanilla assets: Bethesda Game Studios.
Development tools include Mutagen, Caprica and independent plugin/PEX readers.
No Bethesda game files or third-party mod assets are redistributed. This free
fan-made mod is not officially endorsed by Bethesda or Nexus Mods.
