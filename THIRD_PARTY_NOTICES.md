# Third-party notices and provenance

The original code is MIT-licensed and the original paper/documentation/data are CC BY 4.0, as selected by the author. Those grants do not relicense third-party works.

| Reference/dependency | Use | Included here? |
|---|---|---|
| Dell A04/A07 updater packages | Offline extraction and identity checks | No; URLs, hashes, and component metadata only |
| Dell/board-vendor GenCAD boardview | Owner-provided connectivity source | No; derived connectivity excerpt and source hash only |
| Third-party SPI reference image | Early exploratory host-updater analysis | No; not a final authoritative firmware source |
| TI technical manuals | Field interpretation and algorithm references | No full manual text or PDFs; bibliographic citations only |
| BIOSUtilities | AMI UAF format reference | No copied module; inspected commit cited |
| uefi_firmware | EFI decompression dependency | No distribution bundled; install separately under its own license |
| Ghidra/pypcode | CR16C decode and semantics reference | No distribution bundled; install separately under their own licenses |
| UEFITool / GNU binutils / ACPICA | Static extraction/disassembly | No binaries bundled |
| SmartBatteryHack / DJI firmware tools | Prior tooling comparison | No repository code bundled |
| matplotlib / TeX packages | Original figure rendering and typesetting | No dependency distribution bundled |

Measured gauge-state blocks and transaction transcripts are study observations, not a full vendor firmware image. The recorded identity strings and manufacturer names identify components and are not endorsement claims.

The historical instruments under `tools/` are project-generated source snapshots. Their original source hashes are retained in the evidence manifest. The polished offline extractor is original project code informed by the cited UAF structure, not a copied BIOSUtilities implementation.
