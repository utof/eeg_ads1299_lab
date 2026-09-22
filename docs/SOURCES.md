# Primary references and provenance

Research checked 19 September 2026. Product listings and online library versions can change. The installed/tested library versions are recorded separately in `VALIDATION.json`; they are not asserted to be the newest online releases.

These sources support specifications and external guidance. All numerical demo outputs are **this project's generated results**, not measurements reported by these sources. Component choices, budget allocations, test thresholds and proposed experiments are project design choices unless explicitly identified otherwise.

| ID | Primary source | What was used |
|---|---|---|
| S1 | [TI ADS1299-x datasheet, SBAS499C](https://www.ti.com/lit/ds/symlink/ads1299.pdf) | Recommended supplies; gains/rates; input/common-mode headroom; code scaling; sinc³ filter; SPI/native frames; ID and configuration registers. Relevant sections include 9.3.1.3, 9.3.2.1, SPI/Data Format and Register Maps. Equations/tables were also inspected as PDF page images. |
| S2 | [TI ADS1299EEGFE-PDK user guide, SLAU443B](https://www.ti.com/lit/ug/slau443b/slau443b.pdf) | Evaluation equipment is for laboratory engineering use and not intended as a direct patient interface; reference/bias implementation context. |
| S3 | [ngspice official project](https://ngspice.sourceforge.io/) | Circuit simulation and command-line/netlist workflow. Existence of this software does not mean it executed in this run. |
| S4 | [Espressif Arduino-ESP32 SPI documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/spi.html) | Original-ESP32 SPI example and explicit custom-pin initialization. Other control-pin assignments are project choices. |
| S5 | [SciPy `signal.welch`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) | Welch PSD API and density scaling. |
| S6 | [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | Train/test leakage and using a pipeline for train-only preprocessing. |
| S7 | [MNE overview of artifact detection](https://mne.tools/stable/auto_tutorials/preprocessing/10_preprocessing_overview.html) | Environmental, instrument, eye, muscle and other biological artifacts; detection versus removal. MNE is not a dependency of this starter. |
| S8 | [scikit-learn `LeaveOneGroupOut`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.LeaveOneGroupOut.html) | Holding out entire groups/sessions. |
| S9 | [DigiKey ADS1299IPAGR](https://www.digikey.com/en/products/detail/texas-instruments/ADS1299IPAGR/3536907) | One-piece listed bare-chip price $88.58 and zero immediate stock at research check; not a board quotation or delivery promise. |
| S10 | [DigiKey ADS1299-4PAGR](https://www.digikey.com/en/products/detail/texas-instruments/ADS1299-4PAGR/6590685) | Related four-channel bare-chip listing at $44.99 at check; not total assembled-system cost. |
| S11 | [OpenBCI Cyton specifications](https://docs.openbci.com/Cyton/CytonSpecs/) | Battery-only power instruction for that specific completed design; does not certify a different DIY board. |
| S12 | [OpenBCI EEG setup guide](https://docs.openbci.com/GettingStarted/Biosensing-Setups/EEGSetup/) | Posterior alpha and eyes-open/closed observation as a practical first EEG target. Its board-specific wiring is not transferred to an unidentified ADS1299 module. |
| S13 | [Espressif Arduino-ESP32 Wi-Fi documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html) | Wi-Fi station configuration used by the optional bench transport starter. |

## Uploaded background reports

The user supplied two earlier generated reports, mounted as `Pasted text.txt` and `Pasted text (2).txt`. The first proposed an AD8232/ADS1115 route and reported eight tests passed with ngspice skipped. The second compared ADC alternatives and recommended separating analog and behavioral simulation. Both used different budget assumptions from this request.

This release uses their broad simulation-first motivation, but is a new ADS1299-specific software project. Historical purchase estimates, claims of prior validation and old sandbox artifact links are not treated as current evidence or working dependencies. No licensed manufacturer macro-model, font file or prior unavailable ZIP is redistributed.
