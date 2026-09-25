# Owned MCScap electrodes: source facts, not a fitted circuit

Recorded 2026-09-24. The user reports owning MCScap electrodes with **insulated DIN 1.5 mm connectors**. The supplied family manual calls the connector **TouchProof** and describes passive, reusable Ag/AgCl cup electrodes. The exact catalogue variant, actual lead length and shielding are not yet known. Do not treat the selected ADS1299-4/S3 baseline as hardware already purchased.

## Preserved source

- [Complete user-supplied Russian manual transcription](MCS.MCE-UM-RU-RU_2024-10-31_user_transcription.txt): all supplied sections, including warnings, technical characteristics, use, maintenance and symbols. Presentation/line wrapping is normalized; technical wording, units and unusual values are not silently corrected.
- [Source record](source_record.json): manufacturer statements and user-reported inventory are separated from unknown numerical-model inputs. `null` means unknown, not zero.

The uploaded PDF was inspected, including the technical table. Its filename was `Электроды электроэнцефалографические MCScap. Руководство по эксплуатации .pdf`, 176,340 bytes, SHA-256 `23fd5e9f5d527dcd727f6707394ed6d6c9cc860d0810d6941f80eddcd2bb049a`. **The original PDF binary is not committed here.** This directory preserves the complete supplied text and identifies the exact attachment, not a claimed byte-identical PDF copy.

The [manufacturer document catalogue](https://docs.mks.ru/ru/product/eeg-electrodes) lists document `MCS.MCE-UM-RU-RU`, revision 1.0, 2024-10-31, 172 Kb. That catalogue entry was checked; the remote PDF was not binary-hash-compared with the upload.

## What the manual actually establishes

| Printed statement | Permitted interpretation | Not established |
|---|---|---|
| Electrode impedance no more than 5 kΩ | A manufacturer specification for the electrode under its applicable test conditions | A frequency-independent 5 kΩ resistor including the user's scalp contact; the test frequency/method is absent here |
| Electrode potential difference no more than 100 mV | A stated electrode-potential-difference limit | A measured offset of this connected recording system |
| Difference drift no more than 25 µV | A stated drift limit | µV/hour: the observation interval is unspecified |
| Electrode noise voltage no more than 20 µV | A stated noise-voltage limit | RMS or peak-to-peak amplitude, bandwidth, spectral density, or a white-noise parameter |
| Cable length no more than 2.5 m | Family upper bound | The actual cable length, shielding, capacitance per metre or capacitance location |
| Dielectric strength at least 30 V | A printed electrode insulation characteristic | Mains/patient isolation of the assembled EEG system |
| Insulation resistance at least 1000 Ω | Preserved exactly as printed in the supplied PDF | Permission to silently change the unit/value or use it as a patient-fault leakage model |

The manual itself says detailed characteristics depend on the manufacturer's catalogue number. The 1.5 mm diameter is **user-reported**, not separately specified in this family manual. A touch-protected/insulated connector is not a galvanic isolation barrier for the whole device.

## Modeling policy: this user's hardware first

Keep the existing Rev A three-scenario study as the clearly labelled numerical regression fixture it is. Do not relabel its 10 kΩ/100 nF assumptions as MCScap measurements or silently replace them with 5 kΩ.

The next electrode-specific study should use this source record, the actual catalogue variant and the available lead information. Represent missing frequency-dependent electrode/contact parameters explicitly. A 5 kΩ resistive example can be an **illustrative sensitivity case**, but not a manufacturer-calibrated model. Separate selected board components, published electrode facts, justified assumptions and physical measurements in every report.

Bad or asymmetric contact is still relevant to these same electrodes: the manual requires checking impedance and correcting contact when it increases. Keep a small set of normal/unequal/disconnected scenarios for the owned hardware; do not build an electrode-plugin system, generic registry or speculative device hierarchy. Introduce a reusable abstraction only when a second real use demonstrates duplication.

Before fitting parameters, obtain the exact catalogue suffix and actual lead length/shielding, and seek the impedance/noise test conditions or suitable dummy-bench measurements. Do not infer electrode capacitance from a single impedance upper bound.

No source statement here approves the Rev A circuit, its protection, its assembly, purchasing or connection to a person. The original hardware/firmware safety gates remain unchanged and false.
