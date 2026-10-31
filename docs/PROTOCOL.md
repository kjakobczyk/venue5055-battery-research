# Observed EC-mediated fuel-gauge protocol

This document specifies the subset observed on the study device. It is not a complete EC specification, and is not a compatibility promise for other devices.

## Namespaces and identity

| Item | Value / interpretation |
|---|---|
| Host adapter | `/dev/i2c-0` on the study boot; ACPI identity `\\_SB_.I2C1` |
| EC | Seven-bit address `0x10`; address bytes `0x20` write, `0x21` read |
| Gauge | Seven-bit address `0x55`; address byte `0xAA` for requests |
| Logical EC mailbox registers | `0x17–0x1D` for the exercised subset |
| EC image offsets | Byte offsets in the verified 131072-byte `EC0.bin` |
| DataFlash class identifiers | Decimal class numbers unless explicitly marked hex |

Select the adapter by verified platform/ACPI identity, not by assuming that Linux adapter numbers are stable. The original study used `I2C_SLAVE`, not `I2C_SLAVE_FORCE`. A Python file lock coordinates only cooperating study tools, not the EC firmware or ACPI AML.

## EC block read

Send a single block-command byte `b`, then read eighteen bytes in a combined I2C transaction:

```text
Host transmit: b
EC reply:      10 <16-byte payload> crc
```

The CRC input is `20 b 21 10 <payload>`. CRC-8 uses polynomial `0x07`, initial state zero, non-reflected processing, and zero final XOR. A valid CRC confirms transmission consistency; interpretation still requires the correct register layout.

Known aggregate battery blocks:

| Block | Payload offsets, little-endian words |
|---|---|
| `0xA2` | 0 status; 2 signed current; 4 remaining charge; 6 voltage |
| `0xA3` | 0 unit/status word; 2 design capacity; 4 full capacity; 6 design voltage; 10 cycle count; 12 serial word |

The observed unit/status word was `0x6000`, with the tested charge values interpreted as mAh. Do not extrapolate this decoder to an untested energy-unit mode.

Block `0xF1` supplies logical EC registers `0x10–0x1F`, so its payload offset `12` is EC register `0x1C`. Block `0xF2` begins at logical register `0x20`; it is not where a two-byte voltage result starts.

## Logical-register write

The exercised block write is:

```text
65 10 r v <14 zero bytes> crc
```

Compute CRC over `20` followed by the packet excluding its final CRC. The packet contains one command byte, one count byte, sixteen payload bytes, and one CRC byte. This is a write to the EC's volatile register interface, not automatically a persistent write to the gauge.

Recorded examples:

```text
r=17, v=00: 65 10 17 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 27
r=1a, v=aa: 65 10 1a aa 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20
r=1b, v=08: 65 10 1b 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 8c
r=18, v=09: 65 10 18 09 00 00 00 00 00 00 00 00 00 00 00 00 00 00 3f
```

## Request registers

| Register | Observed purpose |
|---|---|
| `0x17` | Channel selection in low two bits; readback also includes live controller-state flags |
| `0x18` | Protocol/trigger; cleared on completion |
| `0x19` | Completion status; `0x80` for the validated successful requests |
| `0x1A` | Eight-bit downstream address, here `0xAA` |
| `0x1B` | Downstream command/register |
| `0x1C…` | Request/result bytes |

Protocol codes exercised: `6` write byte, `7` read byte, `8` write word, `9` read word. A general implementation must not assume all other codes are safe, supported, or equivalent to a familiar SMBus controller's numbering.

Register `0x17` was initially checked too strictly. A readback of `0x10` can expose live controller state while the selected channel is still zero. The corrected acquisition checks the low channel bits, waits for the observed bus-state bit to clear, verifies the other request fields, triggers exactly once, and checks completion with a bounded timeout. This does not eliminate all multi-master races.

## Gauge command and DataFlash layout

Documented gauge `Control()` selectors used for diagnostics were `0x0000`, `0x0001`, `0x0002`, `0x0008`, and `0x001F`. These select responses; they are distinct from reset or unseal commands. The single later reset was `0x0041` and was separately authorized.

A DataFlash block is selected through `0x3E` (class) and `0x3F` (block); the study used a word write beginning at `0x3E` to set both bytes. `0x61=0` selects the general DataFlash access mode. Data bytes are exposed at `0x40–0x5F`. The checksum at `0x60` is:

```python
checksum = (255 - sum(block_bytes)) & 0xff
```

Writing that checksum commits a staged block. Therefore a complete read/modify/write must use a fresh complete block and verify bytes before and after commit. Transport CRC and this block checksum protect different layers.

SMBus word replies are little-endian in transfer order. Acquired DataFlash numeric fields here use big-endian storage. Qmax0 at decimal class 82, offsets 2–3, was `1e 28` (7720). The experiment changed it to `22 5a` (8794); blindly sending the numeric word in the wrong endian order would not implement the same edit.

## Readout classes and side effects

1. **Aggregate EC read:** a command-selector write followed by a reply; no gauge configuration write requested.
2. **Bridged standard read:** volatile EC request writes cause a gauge command-selector/read transaction.
3. **Control response selection:** a gauge word write selects an identity/status response; not a persistent parameter update.
4. **DataFlash acquisition:** writes access/class/block selectors but does not write payload or commit checksum.
5. **Persistent experiment:** writes two payload bytes and the checksum, then issues one gauge reset.

Calling all five “read-only” would conceal important differences. The source snapshots preserve the staged escalation and record request fields/results. The default reproduction workflow is offline.

## Selected static landmarks

All following numbers are **file offsets** in the matching A04/A07 EC component:

| Offset | Interpretation |
|---|---|
| `0x43DE` | Logical EC register read dispatcher |
| `0x48FA` | Logical EC register write dispatcher |
| `0x4A04` | Mailbox-protocol trigger path |
| `0x3412` | Request enqueue |
| `0xC058` | Shared transaction builder |
| `0xA5DE` | Downstream engine entry |
| `0x73C8 → 0x4D42` | Host-request completion callback |
| `0x7E6A` | Battery configuration state machine |
| `0x83B6` | Built-in update executor |
| `0x81D4` | Embedded W/C/X parser |

The live test validates a useful path through this mapping, not the correctness of every unexecuted branch. Firmware data-pointer mapping includes `+0x20000` relative to file offsets; those values must not be sent as bus addresses.
