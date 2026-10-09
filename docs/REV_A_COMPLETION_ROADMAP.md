# Rev A roadmap - native SPI fault source and AFE split coverage added

Continue draft PR98 from live head; main was c2f93ee3 (PR97). The failed cc9 turn
published its DNP/preservation repairs; do not repeat them. The eleven-file
hardware candidate remains preserved, NOT applied. Read AGENTS,
REPOSITORY_PUBLICATION, REV_A_BENCH_FIRST and LLM_HANDOFF before continuing.

| Category | Remaining substantial turns | Done/status | Next slice or blocker |
|---|---:|---|---|
| SPI provision decision | 0 | Five accessible positions chosen; no trace-surgery fallback | No fitted resistance or first-power approval |
| DNP/inventory and preservation | 0 for source repair; native confirmation pending | Closed named inventories and exact 21/41 delta; original snapshots retained | Applied native/export confirmation and review |
| Native pad-fault source | 0 to author; execution pending | Ten cuts and five bridges now specified with fault-specific DRC witnesses | Execute on both applied/refilled boards; not unit doubles |
| Split-output coverage | 0 for source repair | AUX clock selector and AFE output/reference/mutation probes cover both segments | Whole-channel limits unchanged; native geometry confirmation |
| Five-position hardware integration | 1-2 with working pinned CAD and complete-file publication | Saved candidate still unapplied | Fresh exports/count consumers, refill/parity/ERC/DRC, new fault cases and access review |
| Other digital-channel disposition | 1 bounded decision plus evidence | MCU launches and DRDY/control paths separate | Actual source-end/channel evidence or limited-pilot disposition |
| Analog pilot choice | 0 for proposal | Six upstream pairs retained for internal-test-only pilot | Accept restricted purpose/revision risk at release; E1 unchanged |
| Components/manufacturing | 1-2 plus required evidence | Existing parts/process proposals and frozen Q1 retained | Accepted stack/component/assembly decisions |
| B1-B3 startup setup | Assembly/equipment-dependent | Existing plans and B2 run card retained | Actual contacts, insulation, restraints, instruments and limits |
| Fabrication release | 1 after prerequisites | Not released | One consistent reviewed revision and restricted-purpose acceptance |
| First internal capture | Approved physical-work dependent | Firmware gate false; no acquisition | Inspected assembly and separately approved commissioning |
| External-input characterization | Later, measurement-dependent | Unqualified; further revision possible | Existing external-source/noise/coupling/uncertainty requirements |
| Prices/RFQ | Paused | Sole frozen unsent Q1 | No duplicate packet, detailed lookup or outreach |

Estimates overlap and exclude supplier responses, fabrication, shipping and
measurements. The 57 focused local passes are source/API-double checks. Fifteen
native cases were deselected there; an actual native attempt stopped at missing
KiCad before mutation. No native cut/short or hardware pass is claimed. Exact
before/after source identities and commands are in LLM_HANDOFF. Previous cc9 CI
stopped at formatting; inspect current-head results rather than borrowing a pass.

MISO and MISO_DRV share existing total via/length/reference budgets; own-contact
exclusions stay net-specific. No limit was reset per segment. Format-only fixes
leave existing population/preservation behavior intact. Gate orchestration,
450 s CAD budget, 71% floor, dependencies, firmware and Q1 remain unchanged.

Next integrate the preserved candidate in PR98 with working KiCad/source transfer;
run new native fault cases, fresh exports/refill/parity/DRC and independent review.
Do not recreate geometry, another archive or a new measurement plan. The prior
blocked runtime workflow must not be retried or bypassed. All #45/#48 and
purchase/fabrication/physical work/mating/power/external-input/body-use gates remain.
