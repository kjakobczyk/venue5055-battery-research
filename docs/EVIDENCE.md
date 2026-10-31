# Claim-to-evidence map

The study date is 2026-10-31, with UTC timestamps. Event timestamps identify acquisition starts/snapshots; individual low-level bus events do not all have separate timestamps. Release hashes are in `evidence/manifest.json`.

| ID | Claim | Evidence | Qualification |
|---|---|---|---|
| E01 | Initial sysfs values were inconsistent with the EC battery replies. | `evidence/acpi/initial-reading.json`, `second-reading.json` | EC is another reporting layer, not an external electrical reference. |
| E02 | `_BST` voltage-source correction changed six AML bytes. | `evidence/acpi/patch-proof.json`; manuscript source excerpt | The full vendor DSDT is not redistributed. Local source hashes identify it. |
| E03 | Patched table was active and voltage matched after reboot. | `evidence/acpi/post-boot-verification.json` | Reboot also refreshed cached information; `_BIX` refresh causality unresolved. |
| E04 | Five exact direct gauge probes failed. | `evidence/transport/direct-gauge-probes.json` | Negative responses do not uniquely explain the physical topology. |
| E05 | Boardview routes distinguish CPU-facing and gauge-facing EC segments. | `evidence/topology/derived-routing.json` | Derived from owner-supplied CAD; actual component population not inspected. |
| E06 | Official package identities match recorded hashes; decoded EC components are equal. | `evidence/firmware/A04-provenance.json`, `A07-provenance.json`, component manifests, `EC-comparison.json` | Package-component equality is not full live-EC attestation. Re-extract using pinned inputs. |
| E07 | Two embedded scripts have identical sizes/counts but different hashes. | `evidence/firmware/embedded-script-metadata.json` | Scripts were extracted, inspected, and never executed. |
| E08 | Script callers connect to a transaction engine. | Historical trace scripts; expected offsets in manuscript/protocol | Static inference over selected slices, not full-program verification. Regeneration needs locally obtained EC image and `pypcode`. |
| E09 | The host dispatcher reaches that engine. | `evidence/firmware/host-dispatch-map.json`; trace source; live tests E10–E12 | The dynamically validated subset is byte/word requests at the gauge address. |
| E10 | F1/F2/F3 host-register replies had valid CRCs. | `evidence/transport/host-register-probe.json` | No persistent change. |
| E11 | First voltage result was decoded from the wrong register group, then corrected. | `first-voltage-test.json`, `first-voltage-correction.json` | Preserve the failed interpretation; correct F1 bytes gave 4244 mV. |
| E12 | Gauge identity and standard parameters are available through the bridge. | `evidence/gauge/initial-direct-diagnostics.json` | Identification needs Control-response selection; not literally a write-free bus trace. |
| E13 | Three initial extended blocks succeeded before an over-strict bus-state guard stopped acquisition. | `evidence/dataflash/first-session.json` | Error is preserved; both selector-restoration checks passed. |
| E14 | Remaining 22 blocks succeeded with corrected channel/bus-state handling. | `evidence/dataflash/completed-session.json` | Multi-minute, non-atomic acquisition. |
| E15 | 25 accepted blocks total 800 bytes and pass block checksums. | `evidence/dataflash/blocks/*.bin` plus E13/E14 | Selected configuration backup, not full firmware/reserved memory. |
| E16 | Reference Qmax is 8794, learned active Qmax 7720, and model settings are known. | `evidence/dataflash/decoded-readings.json` and raw blocks | Decode can be verified from published offsets; reference data are not a reference-cell measurement. |
| E17 | Immediate pre/post experiment differs in only two State bytes. | `evidence/intervention/before-class-82.bin`, `after-class-82.bin`, `report.json` | Exact at these observations; not continuous observation of all memory. |
| E18 | Only three DataFlash payload/commit writes and one BQ reset occurred in the journal. | `evidence/intervention/report.json` | Counts host-issued operations captured by the tool; does not exclude autonomous gauge activity. |
| E19 | Both profile-0 resistance blocks are byte-identical before/after. | `before-class-91.bin`, `after-class-91.bin`, `before-class-93.bin`, `after-class-93.bin` | Calibration was not targeted, but every calibration block was not re-read after reset. |
| E20 | Reported FCC changed 5973→6827, SOH 78→95, while cycles stayed 49. | `evidence/intervention/report.json` | Combined Qmax-change/reset intervention; no reset-only control or physical-capacity test. |

## Corrections to early interpretations

- The initial operating-system full capacity was stale/inconsistent. The erroneous voltage field has a directly identified AML cause; the stale full-capacity cause does not.
- A third-party SPI reference contains host-side updater code. It was not evidence that the running EC image had been identified.
- The boardview established design connectivity; it did not prove actual link population or bus voltage.
- An embedded programming script is not a safe diagnostic read and was not replayed.
- Searching script **file offsets** missed the actual pointers because of the image's address mapping.
- A successful request plus a zero F2 block did not mean zero voltage: the result was in EC registers 1C/1D inside F1.
- Register 17 readback includes live flags, not just the channel selection.
- The Qmax experiment is not a cycle-count reset, complete learning reset, or demonstrated physical repair.
- The word “only” applies to the verified persistent State-byte edit. The experiment also issued a gauge reset and changed volatile state.

## Omitted material and publication transformations

Vendor executable packages, complete firmware images, embedded programming scripts, complete vendor disassemblies, vendor CAD/photographs, third-party repository clones, and binary tool distributions are not included. The small raw gauge blocks are measurements from the studied device, not an entire firmware image.

JSON paths were normalized to `$STUDY_ROOT`, `$STUDY_HOME`, or `$SYSTEM_BACKUPS`. The sysfs serial-number key was removed even where blank. Each manifest record retains both source and release hashes. No raw bus payload was silently rewritten to make a failed test pass. Early failure transcripts remain failures.

No service tag, personal account credential, ORCID, institutional affiliation, publication acceptance, or DOI was supplied or inferred. The author's supplied name is used exactly as provided.
