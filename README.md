# More Brats v1.2.7 — source archive

**Author: Tsoxer** · [Nexus Mods release](https://www.nexusmods.com/skyrimspecialedition/mods/199428) · [GitHub repository](https://github.com/Tsoxer/MoreBrats)

More Brats adds randomized generic children to 19 Skyrim settlements. v1.2.7 supports 40 vanilla child appearance donors, four human races, both genders and five clothing colors: 200 appearance/outfit combinations. Children roam independently, use their settlement's evening building and disappear safely overnight.

The accepted v1.2.7 implementation combines gradual outdoor door-area arrivals every **3–7 in-game minutes** with interior-triggered preparation at the original street markers. Both paths share the same daily population target and tracking. Newly selected donors cannot repeat within one settlement's active population; outfits can repeat, and other settlements can independently use the same donors. Existing older-save duplicates finish their normal lifecycle.

This package preserves the **actual original v1.2.7 sources**, not decompiled PEX or reconstructed gameplay. All nine current `Papyrus/*.psc` files are byte-identical to the retained release inputs. Original C# generators and release utilities are retained with documented path/privacy edits. Creating this export did not modify the working mod, its sources or the installation ZIP.

## Project structure

```text
Papyrus/                    Nine original v1.2.7 gameplay sources
PluginBuilder/              Actual final C# generator and locked dependency graph
PluginAudit/                Actual Mutagen record/link checker
Config/                     Original settlement, donor and door-type configuration
Config/fixtures/            Original settlement data for simulated tests
Baseline/v1.0.0/Runtime/     Owned More Brats ESP/SEQ starting inputs
Baseline/v1.0.0/Papyrus/     Preserved earlier source fixture
Baseline/v1.1.0/ ...         Original earlier Papyrus and per-stage configuration
Compiler/                   Preserved patched Caprica sources, shims and patches
ThirdParty/                 Dependency sources and license notices
Tools/build.py              Portable source-export build driver
Tools/verify_build.py       Source and released-script parity verification
Tools/original/release_*/   Original generator chain and development utilities
Tools/support/              Original PEX/VMAD readers and fault-aware interpreter
Verification/               Source provenance, expected hashes and data inventories
Docs/                       Exact retained player documentation for build fixtures
CHANGELOG.txt               Complete cumulative history through v1.2.7
```

The current controller logic is in `Papyrus/MB_Controller.psc`, `MB_CityController.psc`, `MB_TownController.psc` and `MB_VillageController.psc`. Their original aliases and recovery helper complete the nine-script implementation. Appearance filtering and interior preparation are part of those existing controllers; no additional manager or external framework was introduced.

`Config/appearance-roster.json` contains the original donor metadata and category mappings. `Config/arrival-door-types.json` contains the original door-type list. The actual appearance-adding generator is preserved under `Tools/original/release_v120/PluginBuilder/Program.cs`; the later door-list addition is under `release_v124`. The root generator is the actual v1.2.7 stage, which consumes the preceding stage and updates release metadata.

`Verification/appearance-mapping.json` and `settlement-bindings.json` are derived inventories from the accepted plugin, clearly separated from original build source. Historical configuration files retain their original version labels where they are unchanged inputs.

## Build prerequisites

The preserved toolchain was verified on Linux x86-64 with SSE4.2:

- .NET SDK **8.0.428**, targeting .NET 8.
- `Mutagen.Bethesda.Skyrim` **0.49.0**, with resolved NuGet dependencies locked.
- Python **3.12** in the verification environment.
- GCC **14.2** with C++23 support, CMake **3.20+** and Ninja for a compiler rebuild.
- Boost **1.83.0** headers and the `filesystem` and `program_options` libraries.
- NuGet access on first restore, unless the locked packages are cached.

The modified Caprica sources, Linux compatibility shims, pugixml **1.14** sources and esplib **0.2.0** Python sources are included. Boost, the SDK and the system toolchain are external prerequisites. The original compiler patches are already applied to the included compiler tree; do not apply them twice. See `Verification/dependencies.json` and `THIRD_PARTY_NOTICES.md`.

No Skyrim installation, Creation Kit, Bethesda master file or BSA is needed for the build. The game still needs the official assets associated with `Skyrim.esm`, `HearthFires.esm` and `Dragonborn.esm`. None of those proprietary masters or assets is included. The `API` files are small project-authored compile-only interfaces, not game-script replacements; never install them into Skyrim.

## Building

From the extracted source directory, with the prerequisites on `PATH`:

```sh
python3 Tools/build.py --build-compiler
```

If Boost headers are outside the compiler's normal include paths, add `--boost-root` with their installation/source prefix. To use an existing preserved patched Caprica executable, pass `--compiler` instead of `--build-compiler`. `--dotnet` selects a particular SDK launcher.

The driver creates an isolated `.build` workspace and runs the **original incremental C# generators in order, from v1.1.0 through v1.2.7**, starting with the included owned v1.0.0 ESP/SEQ. It then compiles the nine original current scripts, copies the retained runtime documentation and compares the result with the accepted v1.2.7 implementation.

Outputs:

- `.build/work/build/v1.2.7/runtime/`: Data-root mod files.
- `.build/MoreBrats-v1.2.7-rebuilt.zip`: rebuilt installation archive.
- `.build/rebuild-verification.json`: source and runtime parity report.

To run the original v1.2.7 compiled-code simulation suite:

```sh
python3 Tools/build.py --tests
```

This uses the compiler from the first command. With an existing patched compiler, include `--compiler` on the test command too. The driver compiles the supplied historical source fixtures, creates isolated earlier-version inputs, and runs the original final suite. The five frozen helpers are copied from the rebuilt v1.1.0 fixture into later fixture runtimes, matching the release's reuse strategy without distributing reference PEX files.

The driver respects existing `DOTNET_CLI_HOME` and `XDG_DATA_HOME`. Otherwise it uses isolated caches. `MB_NUGET_PACKAGES` selects an existing NuGet cache. SDK/toolchain installation remains an environment prerequisite; the driver does not install them.

## Verification

This export was checked against the retained, author-accepted `MoreBrats-v1.2.7.zip`:

```text
f560011f67ceac5e3d3738ae5f78a03a984abe1f987fe677fafac2d27a735b71
```

- All nine current gameplay sources match their original build-input hashes.
- The original generator chain reproduces the ESP and startup SEQ byte-for-byte.
- Recompiled PEX script objects match the released variables, properties, functions, instructions and constants.
- Compilation timestamps, source filenames and debug/header metadata can differ. A rebuilt ZIP is **not** claimed to have the original release ZIP's hash.
- The preserved compiler source is unchanged from the compiler exported and rebuilt for v1.1.0. This export's compilation used that previously source-built executable; it does not claim a second fresh compiler build.
- The final v1.2.7 suite covers all 19 settlements, 15,200 reference/variant mappings, 40 actual donor identities, all 200 appearances, shared arrival caps, quick entry/exit, overlapping callbacks, signed FormIDs and typed earlier-state upgrades.

Tsoxer confirmed v1.2.7 successful in Skyrim. The source-export checks are separate: the cloud verification does not run Skyrim or load actual ESS files. Native calls, event delivery, loading, geometry and AI/pathfinding in the simulation suite are controlled models.

`SHA256SUMS.txt` inventories every distributed file except the checksum file itself. Run `sha256sum -c SHA256SUMS.txt` from this directory to check the extracted archive. `Verification/original-source-manifest.json` records original/export hash pairs and identifies portability edits.

## Scope and limits

This remains an **incremental build from an owned v1.0.0 baseline**, as in the v1.1.0 source archive. The source chain from v1.1.0 through v1.2.7 is supplied; bootstrap generators for versions before v1.0.0 are outside this export. It does not claim a from-empty reconstruction of the full development history.

The original script preparers and date/document/package utilities are preserved for reference. Some relied on historical release-status reports or compiler metadata that are intentionally not exported. They are archival utilities; the supported build uses the supplied exact source/configuration and the portable driver. Private deployment automation, credentials, Git state, caches, temporary investigations, reference PEX files and Bethesda assets are excluded.

The source-export README and cumulative changelog identify v1.2.7 as the working release. Exact runtime documentation remains under `Docs` so the rebuild can reproduce the retained installation files without silently editing the mod archive.

## Runtime requirements

More Brats uses vanilla Skyrim Papyrus and native AI. **SKSE, Address Library, SPID and other external gameplay frameworks are not required.** The development dependencies above are build tools, not requirements for playing the mod.

## Credits

**Author:** Tsoxer

**Development assistance:** Codex (OpenAI) (code generation and debugging).

**Design, direction, and in-game testing:** Tsoxer.

## Licensing

Tsoxer's original More Brats material remains **source available, all rights reserved**, as specified in the supplied [`LICENSE.md`](LICENSE.md). This export does not change that notice or grant a new license. Separately licensed tools, libraries and applicable derivatives remain governed by their own terms; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
