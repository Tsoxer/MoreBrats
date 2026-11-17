# Source provenance

The authoritative implementation is the released More Brats v1.1.0 installation archive. This source export was prepared separately and did not modify that archive or its runtime/source snapshots.

`Verification/original-source-manifest.json` records original/export SHA-256 pairs for preserved files. In particular:

- The nine `Papyrus/*.psc` files are original, human-written/generated development sources, copied byte-for-byte. They are not decompiled PEX.
- `Config/settlements.json`, the original mock-test configuration JSON files, handwritten API declarations, baseline sources, reader/interpreter utilities, compiler patches and compatibility headers are preserved as original inputs.
- The C# generator/auditor and original Python release tools are the original sources. Embedded machine-root path prefixes were removed, leaving the same project-relative workspace layout. No generator record logic or gameplay code was rewritten.
- Private date-region configuration was removed from the archival document/package utilities and replaced with the recorded v1.1.0 release date. Corresponding privacy-check literals were removed. These edits concern publication metadata only.
- Original third-party compiler/library source files are included with their licenses. Git directories and compiled build products are excluded.

New files prepared for this export are the GitHub README, this document, `.gitignore`, the portable `Compiler/CMakeLists.txt`, `Tools/build.py`, `Tools/verify_build.py`, dependency-lock/verification reports and archive inventory. They are labelled export support, not passed off as original development files.

`Verification/released-runtime.json` contains expected runtime hashes and canonical decoded-PEX hashes computed directly from the released files. Decoded hashes omit file-header metadata but retain the full script object, including functions and instructions. Derived appearance/settlement inventories are documentation only; the actual input/code remains separately present.

No source from prior abandoned candidate builds, private delivery automation, game assets or credentials is included. The owned v1.0.0 baseline ESP/SEQ is deliberately included because the actual v1.1.0 generator depends on it. The export does not claim to replace that dependency with a reconstructed approximation.
