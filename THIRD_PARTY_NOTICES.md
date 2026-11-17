# Third-party build components

These are **build/test dependencies**, not additional requirements for playing More Brats.

| Component | Preserved version/source | Distribution in this archive |
|---|---|---|
| Caprica | qudix/caprica commit `0b2d329071f81ceecf7ead70d5b4d8b8b564befb`, with the actual local Linux/Skyrim fixes | Modified sources and MIT license in `Compiler/caprica`; patches and compatibility headers included |
| pugixml | v1.14, commit `db78afc2b7d8f043b4bc6b185635d949ea2ed2a8` | Sources and MIT license in `ThirdParty/pugixml` |
| esplib | 0.2.0, BadDogSkyrim/esplib commit `ed8b5c2d0155668b7078875831ea576ffa5e0caa` | Sources, project metadata and MPL-2.0 license text in `ThirdParty/esplib` |
| Mutagen.Bethesda.Skyrim | NuGet 0.49.0, with resolved transitive dependencies locked | Retrieved by NuGet; upstream GPL-3.0 license text included as `ThirdParty/Mutagen-LICENSE.txt` |
| Boost | 1.83.0 | External headers and filesystem/program_options libraries; obtain under the Boost Software License |
| .NET SDK | 8.0.428 verified | External SDK, not redistributed here |
| Python, GCC, CMake, Ninja | Versions/prerequisites described in README | External build environment, not redistributed here |

Upstream source/package locations:

- https://github.com/qudix/caprica
- https://github.com/zeux/pugixml/tree/v1.14
- https://github.com/BadDogSkyrim/esplib
- https://www.nuget.org/packages/Mutagen.Bethesda.Skyrim/0.49.0
- https://www.boost.org/users/history/version_1_83_0.html
- https://dotnet.microsoft.com/en-us/download/dotnet/8.0

Retain the upstream copyright/license notices with redistributed third-party source. The More Brats API headers are minimal project-authored compilation interfaces; no Bethesda master, game-script source archive, BSA, mesh, texture or voice file is redistributed.
