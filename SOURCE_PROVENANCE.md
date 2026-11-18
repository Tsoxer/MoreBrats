# Source provenance — More Brats v1.2.7

The authoritative implementation is the retained `MoreBrats-v1.2.7.zip` installation archive accepted by Tsoxer. This export is source preservation and GitHub publication preparation, not a gameplay update. It did not change that archive, its runtime files or its original source snapshots.

`Verification/original-source-manifest.json` records original/export SHA-256 pairs and export-only edits:

- The nine current `Papyrus/*.psc` files are copied byte-for-byte from the actual v1.2.7 development sources. They are not decompiled PEX or reconstructed approximations.
- Historical Papyrus fixtures, original settlement/appearance/door configuration, handwritten API interfaces, readers/interpreter, compiler source/patches and compatibility headers are retained as original inputs.
- The root C# generator/auditor is the actual final v1.2.7 stage. The original preceding generators through v1.1.0 are retained under `Tools/original/release_*`. Machine-root prefixes were made relative without changing record-generation logic.
- Original release utilities have the same documented path normalization. Environment-specific publication metadata/checks were removed or replaced by recorded dates where necessary for privacy. These edits do not change gameplay source or plugin-generation behavior.
- The source-export cumulative changelog preserves every historical entry, updates the current-release header and appends the subsequent author confirmation. The exact retained runtime README/changelog are separately preserved under `Docs/v1.2.7` for parity.
- The user-supplied `.gitattributes`, `.gitignore`, `global.json`, `LICENSE.md` and `THIRD_PARTY_NOTICES.md` are retained unchanged. Source checksums are regenerated for this version.

New or updated source-export support consists of the GitHub README, this document, `Tools/build.py`, `Tools/verify_build.py`, NuGet lock copies, verification inventories/reports and `SHA256SUMS.txt`. These are labelled export/build support, not passed off as original gameplay development files.

`Verification/released-runtime.json` contains expected raw runtime hashes and canonical decoded-PEX hashes from the accepted archive. Decoded hashes omit file-header metadata but retain the complete script object and function instructions. Derived appearance and settlement inventories are reading aids, not substitutes for original source.

The included More Brats v1.0.0 ESP/SEQ is the project's own preserved baseline input, not a Bethesda master. The supported build applies the original generator chain from v1.1.0 to v1.2.7. Earlier bootstrap generation is not claimed to be reproduced.

Historical PEX fixtures and a v1.1.0 ZIP are generated only inside `.build` when tests are requested. They are rebuilt fixture data, not claimed to be byte-identical historical release archives. Frozen helper relationships are preserved in those fixtures. No reference PEX or generated test ZIP is included in this source archive.

Compiler and third-party source/license notices are retained. The included patched compiler sources match the development compiler sources. Verification for this export used the unchanged executable previously built from this preserved compiler tree, rather than claiming another fresh compiler build.

No private delivery automation, private site URL, credentials, local machine-root paths, compiled build caches or Bethesda assets are distributed. No automated GitHub push or Nexus publication is part of this export.
