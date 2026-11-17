# More Brats v1.1.0 — source archive

**Author: Tsoxer** · [Nexus Mods release page](https://www.nexusmods.com/skyrimspecialedition/mods/199428)

More Brats adds randomized generic children to 19 Skyrim settlements. v1.1.0 supports genuine Nord, Imperial, Breton and Redguard children, both genders and five vanilla outfits. Each settlement retains its daily population range, independent roaming, evening interior routine and safe nighttime removal.

This package preserves the **actual human-readable v1.1.0 sources**. The nine gameplay `.psc` files and original generator configuration are byte-identical to the retained release build inputs. They were not decompiled from PEX or recreated from a description. The ESP generator is the original incremental generator, with only machine-root paths made project-relative.

The released mod and its archives were not changed to create this export. This is a source package, not a mod update or an installation ZIP.

## Structure

```text
Papyrus/                    Nine original v1.1.0 gameplay sources
PluginBuilder/              Original C# ESP generator, project and dependency lock
PluginAudit/                Original independent Mutagen plugin/link checker
Config/settlements.json     Exact original v1.1.0 generator input
Config/fixtures/            Original settlement inputs used by mock tests
API/                        Handwritten compile-only vanilla Papyrus interfaces
Baseline/v1.0.0/Runtime/     Owned More Brats ESP/SEQ used by the incremental builder
Baseline/v1.0.0/Papyrus/     Original earlier sources used for upgrade fixtures
Compiler/caprica/           Actual modified Caprica compiler sources and MIT license
Compiler/compat/            Original Linux compatibility headers
Compiler/patches/           Preserved portability/Skyrim allocation patches
ThirdParty/                 esplib/pugixml sources and dependency license texts
Tools/build.py              New portable source-export build driver
Tools/verify_build.py       New source-hash and released-bytecode parity checks
Tools/original/             Original release utilities, with documented privacy edits
Tools/support/              Original PEX/VMAD readers and fault-aware mock support
Verification/               Hashes, original-source provenance and reference inventories
Docs/                       Original player README
CHANGELOG.txt               Complete released cumulative changelog
```

Appearance donor IDs and race constants are defined in `PluginBuilder/Program.cs`. Independent race/gender/outfit selection is in the four controller scripts' `TryArrival` functions. `Verification/appearance-mapping.json` and `settlement-bindings.json` are explicitly labelled derived reading aids, not replacement or reconstructed build source.

## Build prerequisites

The portable compiler build was tested on **Linux x86-64 with SSE4.2**:

- .NET SDK **8.0.428**, targeting .NET 8. The project pins `Mutagen.Bethesda.Skyrim` **0.49.0**, with its resolved NuGet dependency lock included.
- Python **3.12** in the verified environment.
- GCC **14.2** with C++23 support, CMake **3.20+**, and Ninja.
- Boost **1.83.0** headers and the `filesystem` and `program_options` libraries. These are external build dependencies, not bundled.
- NuGet network access on the first restore, unless the locked packages are cached.

The modified Caprica sources, Linux shims, pugixml **1.14** sources, and esplib **0.2.0** Python sources are included. The compiler's upstream commit and dependency details are recorded in `Verification/dependencies.json`. Its preserved patches are already applied to the included compiler tree; do not apply them again.

No Skyrim installation, Creation Kit, Bethesda master file, or BSA is needed to run this generator. The game itself still needs the official assets associated with `Skyrim.esm`, `HearthFires.esm` and `Dragonborn.esm`. This export contains none of those proprietary masters/assets. The `API` files are minimal handwritten declarations used only for compilation; never install them into Skyrim.

## Build

From this directory, with the prerequisites available on `PATH`:

```sh
python3 Tools/build.py --build-compiler
```

If the Boost headers are not installed in the normal compiler search path, supply their installation/source prefix with `--boost-root`. If using the already-built preserved patched compiler, supply its executable with `--compiler` instead of rebuilding it. `--dotnet` can select a particular SDK launcher.

The driver stages an isolated workspace under `.build`, builds the original ESP generator, compiles the nine original Papyrus files, copies the released documentation and runs parity checks. Results:

- `.build/work/build/v1.1.0/runtime/`: Data-root mod files.
- `.build/MoreBrats-v1.1.0-rebuilt.zip`: rebuilt installation archive.
- `.build/rebuild-verification.json`: comparison with the released implementation.

The included minimal API headers and patched compiler are intentional. A different compiler can generate different instructions; the verifier must pass before treating a rebuild as equivalent.

For the original fault-aware compiled-PEX test suite, including earlier-state upgrade fixtures:

```sh
python3 Tools/build.py --tests
```

This uses the compiler built by the first command. It compiles the included baseline Papyrus sources for the fixtures; old reference PEX files are not bundled. Python's standard library and the included esplib reader suffice for this ESP/PEX workflow. esplib's optional upstream LZ4 dependency is used for BSA extraction, which this build does not perform.

The driver respects an existing `DOTNET_CLI_HOME` and `XDG_DATA_HOME`. Otherwise it uses isolated build caches. `MB_NUGET_PACKAGES` can select an existing package cache for CI/offline use. First-time SDK initialization must be permitted by the build environment; this export does not install an SDK or bypass sandbox restrictions.

## Verification and reproducibility limits

The source export was checked against the actual released `MoreBrats-v1.1.0.zip`, SHA-256:

```text
51f77ffdcf7ac75057e170763dacf439583c1233d79a6fa092184ee30b9e08d8
```

- All nine exported v1.1.0 gameplay sources match the original build-input hashes.
- The portable generator rebuilt the ESP and startup SEQ byte-for-byte.
- Recompiled PEX objects match the released declarations, variables, properties, function bodies, instructions and constants.
- PEX source filenames, compilation/debug timestamps and other header metadata may differ. A rebuilt ZIP is therefore **not claimed to have the original release ZIP's hash**.
- The included compiler is rebuilt from preserved modified sources. Its executable hash need not match the historical executable because linking and build paths differ. The portable CMake entry uses bundled pugixml source rather than the historical shared-library path; emitted script parity is checked independently.

The original generator reads the included **v1.0.0 More Brats ESP/SEQ** and appends v1.1.0 records. Those are this project's own build inputs, not Bethesda masters. This is a verified **incremental build from that baseline**, not a claim that every historical version can be regenerated from source alone. Historical bootstrap generators before v1.1.0 are outside this export.

Some original automation remains archival:

- `Tools/original/prepare.py` originally consumed a full v1.0.0 release ZIP and generated the current sources/configuration. That old ZIP is not included because compiled headers contain historical build metadata. The current original source/config files are supplied directly, so the supported build does not need that preparer.
- The original release-date/document/package utilities depended on temporary release-status reports and the historical compiler hash. Those temporary reports are not exported. The supported driver instead packages the exact released README/changelog and verifies the implementation directly.
- Private website/deployment automation, Git configuration, credentials, caches, intermediate investigation files and game assets are intentionally excluded.

See `SOURCE_PROVENANCE.md` for the exact scope of export-only edits. Nothing is labelled byte-identical when it has been adapted for portability/privacy.

## Runtime and tests

The mod uses vanilla Papyrus and native Skyrim AI. It requires **no SKSE, Address Library, SPID, or external gameplay framework**. Build tools listed above are developer dependencies only.

The automated tests use mocked native functions, events, loading and geometry. They do not establish native pathfinding, FaceGen rendering, real-save compatibility or performance inside Skyrim. The author performs the in-game checks. This source export introduces no gameplay changes.

## Licensing

Tsoxer's original More Brats material is **source available, all rights reserved** to the extent protected by copyright and owned by Tsoxer. Public access does not grant permission to reuse, modify, or redistribute that original material. See [`LICENSE.md`](LICENSE.md) for the copyright notice and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for separately licensed build tools and libraries, whose license terms continue to apply.
