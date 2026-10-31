# Limitations and next experiments

## Claims this study supports

A particular ACPI voltage-source error was identified and corrected for a verified boot. A particular EC firmware component was extracted from two official packages. A specific EC-mediated access path was reconstructed and exercised. Selected model data were acquired with valid checksums. One parameter-edit/reset sequence changed reported quantities while preserving recorded cycle and Ra fields.

## Claims this study does not support

- Physical rejuvenation, increased stored energy, or a measured extension of battery runtime.
- A 95% independently measured physical state of health.
- A demonstrated relationship between changing the cycle counter and changing capacity.
- A causal estimate of the Qmax edit separately from reset and volatile-state changes.
- A universal bypass of sealed mode or recovery of secret keys.
- Applicability to every Venue unit, different BQ families, or all downstream EC protocols.
- A full memory attestation or full reserved-memory/firmware backup.
- Verified recovery from interrupted flash programming.
- The exact cause of the earlier stale `_BIX` full-capacity property.

## Candidate future experiments, not performed

1. **Reset-only control.** Hold the persistent State block constant, standardize load/temperature/rest, reset once, and record the same quantities. This is necessary before attributing all of the FCC delta uniquely to Qmax.
2. **A–B–A model-state study.** With fresh backups and an agreed scope, compare the original and reference Qmax under repeatable conditions, then return to baseline. Natural learning must be tracked rather than overwritten without observation.
3. **Measured discharge capacity.** Integrate current for charge and voltage×current for energy, with calibrated instrumentation and a defined stop condition. The configured model threshold (3420 mV) differs from the SystemDown threshold (3517 mV); do not lower either merely to force an attractive result.
4. **Observe natural relearning.** Monitor Qmax, Ra, RUP_DIS, VOK, QEN, and profile choice over a qualifying cycle. A post-reset instantaneous SOH status is not evidence that a new learning cycle completed.
5. **Repeated hardware replication.** Test additional units and verify their board, firmware, access state, adapter identity, and field maps independently.
6. **EC-aware Linux integration.** Investigate arbitration with ACPI/EC activity, timeouts, platform matching, and table-refresh behavior. The research lock and root-level userspace tools do not solve those driver-engineering questions.

## Broader reset plan versus completed work

A local planning artifact considered resetting learning status and restoring reference resistance curves. **Those operations were not executed.** Only Qmax0 was edited, followed by one BQ reset. The cycle counter was never reset. The paper's conclusions must not incorporate results that such prospective operations might produce.

The device-resident default profiles are useful provenance-backed candidate initial values, not proof that the attached cells still have manufacturing-time characteristics. Higher learned resistance may be real. Removing it from the model can overestimate remaining charge and worsen shutdown predictions.
