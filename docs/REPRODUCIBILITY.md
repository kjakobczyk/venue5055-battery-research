# Reproduction guide

## Two different reproduction goals

**Offline verification** checks whether the released measurements, checksums, transaction scope, figures, and numerical conclusions agree. It needs no device or root privileges.

**Hardware replication** would repeat physical-device operations on a separately verified compatible unit. It requires inputs and precautions not supplied by a checksum test. This release does not claim that simply running the historical scripts on another tablet is a validated workflow.

## 1. Check released evidence

```sh
python3 tools/offline/verify_evidence.py
```

Expected counts are 63 source artifacts, 2376 recorded EC reply frames, and 25 accepted DataFlash blocks. A changed source artifact must not be silently “fixed” by updating its expected hash. Record a new acquisition/version instead.

Source and release hashes differ for JSON records where local paths/serial-key metadata were normalized. Binary gauge blocks are byte-exact exports. The source collector's local operational environment is not required to validate the released copies.

## 2. Acquire the two vendor packages locally

Direct sources used in the study:

- A04: `https://downloads.dell.com/FOLDER03055668M/1/5055A04.EXE`
- A07: `https://downloads.dell.com/FOLDER03494709M/1/5055A07.EXE`

Package hashes:

```text
45cd5b0ca4356a13cb78bc0f0855bc45ac05e56b0d10f70179ba8cb0713caaf6  5055A04.EXE
6626d695b48705a43f63d05ba3f577cdfb14ad99e9118a397b0d029a0001cd6d  5055A07.EXE
```

Obtain the files from Dell into ignored local `work/`. Do not execute them. Download availability can change independently of the study. The package index cited in the paper supplied the A04 path when a driver-details page returned HTTP 403.

## 3. Reproduce UAF extraction

The offline extractor accepts only those two pinned package hashes. It locates a checksum-valid AMI UAF root directly inside the PE data, bounds-checks tagged components, verifies checksums, decompresses EFI payloads, and verifies the EC component hash. It does not invoke the vendor executable, write device nodes, or flash anything.

```sh
python3 -m venv .venv
.venv/bin/pip install uefi_firmware==1.16
.venv/bin/python tools/offline/extract_dell_uaf.py work/5055A04.EXE --output work/A04-images
.venv/bin/python tools/offline/extract_dell_uaf.py work/5055A07.EXE --output work/A07-images
```

Both EC components should have this SHA-256:

```text
21e4efa3f1608539e47e5a8e1511c8f9cd0e3ac4703185555c85363135ab3bd8
```

The two BIOS `R00.bin` components are different. Equality of the EC components must not be generalized to equality of the complete BIOS packages or to a live EC readback.

The historical extraction inspected BIOSUtilities commit `f799425af93264b62a2f3c3cc5bbabf8a2226114`; the standalone extractor is original project code. It is not a redistributed BIOSUtilities module.

## 4. Revisit the static code trace

The study used `pypcode==4.0.1`, `CR16C:LE:16:default`, and inspected the accompanying `CR16C.sinc` definitions. `tools/analysis/` preserves the actual trace scripts rather than presenting them as polished generic CLIs. They expect the study's relative work-file layout next to the scripts; adapt/copy inputs deliberately when reproducing them in a separate workspace.

Key checks include the script pointers at file offsets `0x8410` and `0x842E`, the parser call at `0x8434`, and the host trigger at `0x4A04`. Decode linearly from the documented function boundaries. Do not treat an every-halfword search index as a disassembly of all instructions: tables and text also decode into plausible instructions.

The original boardview cannot be regenerated from released data alone. It is identified by a source hash and represented by a derived connectivity excerpt. If the source is lawfully available, the historical GenCAD parser can be inspected/re-run on it; no proprietary CAD is bundled here.

## 5. Rebuild figures and the PDF

```sh
.venv/bin/pip install 'matplotlib>=3.10.7,<4'
.venv/bin/python tools/offline/make_figures.py
make paper
```

Figures are generated in PDF, SVG, and PNG. PDFs embed TrueType fonts for the matplotlib labels. The paper uses ordinary `article` LaTeX, BibTeX, Latin Modern fonts (`lmodern`), and common packages; there is no proprietary journal class, external font service, network build step, or shell escape. `make paper` requires `pdflatex` and `bibtex` on PATH and uses the already generated figure PDFs.

The arXiv source archive contains the TeX source, bibliography, generated `.bbl`, and figure PDFs. It intentionally excludes vendor binaries, local virtual environments, build logs, and the compiled main PDF. The separate review/GitHub archive includes the compiled paper and the evidence.

## Hardware source snapshots

| File | Historical scope |
|---|---|
| `read_ec_battery_blocks.c` | Aggregate A2/A3 EC reads only; DMI/adapter guards, CRC checks. |
| `read_bq_via_ec.py` | Fixed standard gauge reads and Control-response selectors through volatile EC registers. |
| `backup_bq_extended_readonly.py` | Selected DataFlash acquisition with selector writes, no payload/commit writes. |
| `apply_qmax_test.py` | The separately authorized persistent experiment; requires `--apply-reviewed-qmax-test`. |

These are **historical instrument snapshots**, not hardware-replication entry points in the build. The Python tools derive a working root from their own location and expect local A04/A07 component inputs there; the released archive deliberately lacks those images. The diagnostics snapshot also retains the older stricter channel-readback comparison, while the extended acquisition and intervention include the corrected busy-state handling. This difference is documented, not silently backported into the evidence.

A fixed platform match does not prove that the target battery's fields or security state match the study. Never disable Python assertions with `-O` when evaluating guard-based historical instruments. A study-local lock does not serialize independent ACPI firmware activity. No tool should be aimed at an arbitrary SMBus device merely because its address resembles one in this paper.

## What remains to reproduce experimentally

A physically measured capacity result would require calibrated current/voltage measurement, an appropriate discharge profile, temperature recording, controlled termination, and integration of delivered charge/energy. A causal isolation of the reporting effect additionally needs a reset-only control and preferably repeated or A–B–A measurements. Neither is present in the released study.

## Build reproducibility boundary

Evidence-file hashes and acquisition checksums are exact checks. Regenerated plot/PDF bytes can differ across renderer/font/TeX versions and build timestamps even when the scientific content agrees. The local build environment is recorded in `docs/build-environment.json`; pixel-identical or bit-identical cross-platform typesetting is not claimed.
