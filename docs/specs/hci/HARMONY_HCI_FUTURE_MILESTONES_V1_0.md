# HARMONY — Harmonic Cell Initiative
## Future Milestones, Technology Horizon & Market Intelligence
**Document Type:** Living Strategy Document
**Status:** Active — update each major programme session
**Owner:** Dr. Kofi Boateng, CGO
**Last Updated:** April 2026
**Version:** 1.0

---

## Purpose

This document tracks the long-horizon technological dependencies of the Harmonic Cell Initiative alongside market intelligence on the rate at which those dependencies are being resolved by the broader technology ecosystem. It exists to ensure Harmony is positioned to move immediately when enabling technologies mature — not to discover the opportunity after competitors do.

The core thesis: the four physical limitations blocking full autonomous Harmonic Cell sensing (energy, transduction, transmission, interpretation) are all active areas of global investment and research. The probability of sufficient maturity in each within the next decade is high. Harmony's job is to design the substrate correctly now so that integration, when the enabling technology arrives, is an upgrade rather than a rebuild.

---

## The Four Physical Limitations — Tracking Table

| Limitation | Current State | Probability of Resolution by 2030 | Probability of Resolution by 2035 | Key Indicators to Watch |
|---|---|---|---|---|
| **Energy** — ambient harvesting at milliwatt scale sufficient for continuous edge compute | Research-grade. Piezoelectric, thermoelectric, photovoltaic harvesting demonstrated at mW scale in controlled conditions. Not yet deployable at the density and reliability required for per-cell autonomous sensing. | Medium (40%) | High (80%) | EnOcean, Wiliot, Everactive commercial deployment scale; IEEE Energy Harvesting Society annual roadmap; indoor photovoltaic efficiency milestones |
| **Transduction** — self-calibrating multi-field sensor arrays at sub-$10 per node deployable cost | Acoustic: MEMS microphone arrays at $2-5 per unit, but not calibrated for harmonic decomposition. Thermal: FLIR Lepton at $50-100. Electromagnetic: software-defined radio at $20-50. Each field individually approaching cost threshold; multi-field integration and auto-calibration not yet solved. | Low-Medium (30%) | Medium-High (65%) | MEMS sensor cost curve (track annually); multi-modal sensor fusion chip announcements from STMicroelectronics, Bosch Sensortec; auto-calibration papers from ICASSP, ICCV |
| **Transmission** — event-driven harmonic delta transmission protocols at scale | 5G NR supports low-latency IoT; NB-IoT and LTE-M cover low-bandwidth sensor networks. The harmonic delta transmission protocol (transmit only meaningful coefficient changes, not raw streams) does not yet exist as a standard. The mathematical framework for it is well-understood. | Medium-High (60%) | High (85%) | 3GPP Release 18/19 IoT specifications; O-RAN Alliance open interfaces; IETF CoAP (Constrained Application Protocol) extensions; 6G research programme outputs from NTT, Ericsson, Nokia |
| **Interpretation** — neuromorphic edge processors at sub-100mW operating on continuous multi-field harmonic signals | Intel Loihi 2 (2022): 1 million neurons, ~1W. IBM NorthPole (2023): inference at 22nm, 25x energy efficiency over GPU. Neither yet at the integration density or cost for per-cell deployment. Trajectory is toward milliwatt-scale edge intelligence by 2030-2032. | Low-Medium (35%) | Medium-High (70%) | Intel Neuromorphic Research Community annual benchmarks; IBM Research NorthPole commercialisation timeline; SpiNNaker 2 (TU Dresden) deployment announcements; DARPA JUMP 2.0 programme outputs |

---

## Technology Horizon Map

```
2026    2027    2028    2029    2030    2031    2032    2033    2034    2035    2040    2050
  |       |       |       |       |       |       |       |       |       |       |       |

ENERGY
  [Research]----[Early commercial IoT harvesting]----[Multi-field harvesting nodes]----[Per-cell autonomous]

TRANSDUCTION  
  [MEMS cost falling]----[Multi-field integration chips]----[Auto-calibrating arrays]----[Per-cell sensor nodes]

TRANSMISSION
  [5G IoT mature]----[Harmonic delta protocol research]----[Standard emerges]----[Globe-scale deployment]

INTERPRETATION
  [Loihi 2 / NorthPole]----[DARPA programmes]----[Sub-100mW edge intelligence]----[Per-cell inference]----[Full autonomous sensing]

HARMONY CELL SUBSTRATE
  [Pillar 1 complete]
          [Pillar 2-3 build]
                  [Pillar 4-5 build]
                          [HCI Phase 1-2]
                                  [HCI Phase 3: multi-field]
                                          [Autonomous sensing pilot]
                                                  [Autonomous sensing at scale]
                                                                  [Quantum-compatible ops]
```

---

## Programme Milestones

### Phase 0 — Foundation (2026, Active Now)
**Objective:** Schema is ready to receive harmonic field data when sensing infrastructure arrives. No autonomous sensing. Human-operated capture only.

| Milestone | Target | Description | Status |
|---|---|---|---|
| HCI-0.1 | Q2 2026 | `field_descriptors` reserved field added to cell schema | Pending — Dr. Voss validation |
| HCI-0.2 | Q2 2026 | Harmonic Cell mathematical specification published (working paper) | In progress |
| HCI-0.3 | Q2 2026 | Literature review completed across 7 research domains | Pending — research prompt ready |
| HCI-0.4 | Q3 2026 | Three HCI research agents deployed (Nakamura, Osei, Vasquez) | Pending |
| HCI-0.5 | Q3 2026 | Cesium partnership approach completed — Go/No-Go decision | Pending |
| HCI-0.6 | Q3 2026 | Provisional patent filed: multi-field Harmonic Cell concept | Pending |

### Phase 1 — Acoustic Field Prototype (2026 Q3 – 2027 Q1)
**Objective:** First novel Harmonic Cell implementation. Human-operated acoustic capture of three Central Coast pilot sites. Prove the harmonic encoding pipeline works. Generate first training data.

| Milestone | Target | Description | Status |
|---|---|---|---|
| HCI-1.1 | Q3 2026 | Three pilot sites selected and access agreements signed | Not started |
| HCI-1.2 | Q3 2026 | Acoustic capture protocol finalised (Dr. Osei) | Not started |
| HCI-1.3 | Q3 2026 | Eigenmike em32 procurement and calibration | Not started |
| HCI-1.4 | Q4 2026 | Acoustic field capture completed at all three sites | Not started |
| HCI-1.5 | Q4 2026 | Harmonic decomposition pipeline implemented and validated | Not started |
| HCI-1.6 | Q4 2026 | Acoustic field coefficients stored in pilot cells via `field_descriptors` | Not started |
| HCI-1.7 | Q1 2027 | Commercial validation: acoustic data enables a real estate due diligence decision | Not started |
| HCI-1.8 | Q1 2027 | Phase 1 research paper submitted for publication | Not started |

### Phase 2 — Gaussian-to-Knowledge Extraction (2026 Q4 – 2027 Q2)
**Objective:** Treat Gaussian splat coefficients as physical measurements. Extract material properties, change signatures, structural geometry from splat data. Build the first field extraction training dataset.

| Milestone | Target | Description | Status |
|---|---|---|---|
| HCI-2.1 | Q4 2026 | Splat compression research sprint complete — Yes/No on 60-75% compression viability | Not started |
| HCI-2.2 | Q4 2026 | Material classification prototype: concrete/glass/metal/vegetation from SH coefficients | Not started |
| HCI-2.3 | Q1 2027 | Temporal change detection prototype: detect physical changes from harmonic coefficient deltas | Not started |
| HCI-2.4 | Q1 2027 | Procedural inference prototype: facade and interior from open-source imagery | Not started |
| HCI-2.5 | Q2 2027 | IP assessment completed — patent filing decisions made for all extraction methodologies | Not started |

### Phase 3 — Multi-Field Integration (2027 – 2028)
**Objective:** Visual and acoustic fields coexist in the same cell. Demonstrate unified multi-field query. Begin thermal field work.

| Milestone | Target | Description | Status |
|---|---|---|---|
| HCI-3.1 | Q1 2027 | Multi-field cell query API: single endpoint returns visual + acoustic projections | Not started |
| HCI-3.2 | Q2 2027 | Thermal field capture protocol (drone-mounted thermal imaging) | Not started |
| HCI-3.3 | Q3 2027 | Thermal field harmonic decomposition and storage | Not started |
| HCI-3.4 | Q4 2027 | Three-field cell demonstration: visual + acoustic + thermal in single cell | Not started |
| HCI-3.5 | Q1 2028 | Navigation query validation: structural geometry derived from multi-field data serves Class II Navigation Agent | Not started |

### Phase 4 — Autonomous Sensing Pilot (2029 – 2032, Technology-Dependent)
**Objective:** First cells that sense their own state without human-operated capture. Dependent on energy, transduction, and interpretation technology milestones.

| Milestone | Target (Conditional) | Trigger Condition | Description |
|---|---|---|---|
| HCI-4.1 | 2029 (if energy milestone met) | Ambient harvesting nodes at <$50, >5mW sustained | Deploy 10 self-powered sensor nodes across Central Coast pilot cells |
| HCI-4.2 | 2030 | HCI-4.1 complete + multi-field sensor integration chip available | First multi-field autonomous cell: visual + acoustic + thermal without human operation |
| HCI-4.3 | 2031 | HCI-4.2 + neuromorphic edge chip at <100mW | Edge interpretation pilot: cells that generate semantic events from field changes without centralised processing |
| HCI-4.4 | 2032 | HCI-4.3 validated + harmonic delta transmission protocol standardised | Scale autonomous sensing to 1,000 cells in Central Coast region |

### Phase 5 — Quantum Integration (2035+, Long Horizon)
**Objective:** Quantum-accelerated Harmonic Cell operations. Coupled field simulation at regional scale. Global field state optimisation.

| Milestone | Target (Aspirational) | Description |
|---|---|---|
| HCI-5.1 | 2035 | Quantum algorithm benchmarks completed for core Harmonic Cell operations |
| HCI-5.2 | 2037 | First quantum-accelerated field simulation on Harmony substrate |
| HCI-5.3 | 2040 | Quantum-compatible cell schema deployed at production scale |
| HCI-5.4 | 2050 | Continuous physical world model: planetary-scale harmonic field substrate, autonomous sensing, quantum-accelerated intelligence |

---

## Market Intelligence

### Autonomous Sensing Market

| Company / Programme | What They're Building | Relevance to HCI | Watch Signal |
|---|---|---|---|
| EnOcean (Siemens subsidiary) | Self-powered wireless sensors for building automation. Energy harvesting from light, temperature, vibration. | Most mature commercial deployment of ambient energy harvesting. Technology basis for HCI energy milestone. | EnOcean Alliance membership growth; new sensor form factors |
| Wiliot | Ambient IoT — Bluetooth-enabled tags powered by ambient RF energy. | Demonstrates RF energy harvesting at scale. Relevant to electromagnetic field sensing track. | Retail and logistics deployment scale |
| Everactive | Always-on wireless sensors powered by light and heat. Industrial IoT. | Most directly relevant to HCI transduction milestone — multi-source ambient harvesting. | Customer deployment announcements |
| Sintef / NTNU | Academic research on distributed acoustic sensing using ambient energy. | Directly relevant to HCI-1: acoustic sensing without external power. | Publications in Sensors, JASA |
| Google Project Soli | Radar-based gesture sensing using miniaturised radar on-chip. | Demonstrates miniaturised EM field sensing. Relevant to electromagnetic field track. | Integration into consumer devices |

### Neural Scene Representation Market

| Company / Programme | What They're Building | Relevance to HCI | Watch Signal |
|---|---|---|---|
| Polycam | Consumer Gaussian splat capture via mobile devices. | Primary tooling for HCI-2 visual field capture. Monitor for API access and data format evolution. | API programme announcements; enterprise tier |
| Luma AI | Neural scene capture and streaming platform. | Alternative to Polycam; watch for streaming protocol standardisation. | Streaming API maturity |
| Cesium | 3D Tiles standard; Cesium ion streaming. Evaluating splat support. | Strategic partnership target (WS-A). Their streaming standard will shape HCI visual field delivery. | 3D Tiles Next specification; splat integration announcements |
| NVIDIA Instant NGP | Research: fast NeRF training; hashgrid encoding. | Compression research relevant to HCI-2. | Open-source release updates |
| Google DeepMind (Genie 2, etc.) | World models; 3D scene understanding from video. | If Google builds world models that include physical field understanding, competitive landscape shifts significantly. | Research publications; product integrations |

### Neuromorphic Computing Market

| Company / Programme | What They're Building | Relevance to HCI | Watch Signal |
|---|---|---|---|
| Intel Neuromorphic Research Community | Loihi 2 chip; research access programme. | HCI-4.3 dependency. Monitor power consumption benchmarks and inference latency on signal processing tasks. | INRC annual report; benchmark publications |
| IBM Research | NorthPole chip; neural inference at 22nm. | Alternative to neuromorphic for edge inference. Very high energy efficiency for inference workloads. | Commercialisation timeline; partner announcements |
| SpiNNaker 2 (TU Dresden / University of Manchester) | Massively parallel neuromorphic processor for spiking neural networks. | Most academically open platform — relevant to research integration. | Release to research community; FPGA deployment |
| BrainChip Akida | Commercial neuromorphic chip for edge inference. Already in production. | First commercially available option. Lower capability than Loihi 2 but available now. Relevant to early HCI-4 pilots. | Customer deployment announcements; SDK maturity |
| DARPA JUMP 2.0 | US government programme funding next-generation computing including neuromorphic. | Indicates US government investment priority. Likely to accelerate commercial deployment timeline. | Programme milestone announcements |

### Quantum Computing Market

| Company / Programme | What They're Building | Relevance to HCI | Watch Signal |
|---|---|---|---|
| IBM Quantum | 1000+ qubit systems; Qiskit SDK; cloud access. | HCI-5 dependency. IBM's roadmap to fault-tolerant quantum is the most credible near-term commercial path. | Qubit count; error rate milestones; Condor/Heron chip generations |
| Google Quantum AI | Sycamore processor; error correction research. | Competing path to fault-tolerant quantum. Their 2023 error correction paper was significant. | Nature/Science publications; supremacy demonstrations |
| PsiQuantum | Photonic quantum computing. Targeting million-qubit scale via photonics. | If photonic approach succeeds, timeline compresses. Harmony should monitor. | Funding rounds; government partnerships (Australian government is an investor) |
| Microsoft Azure Quantum | Topological qubits; Azure integration. | If topological approach works, error rates drop dramatically. Very long horizon but potentially very important. | Research publications on topological qubit milestones |

---

## Decision Gates — Technology Trigger Events

The following events should trigger an immediate Harmony strategic review session when they occur:

| Trigger Event | Likely Year | Strategic Response Required |
|---|---|---|
| Ambient energy harvesting node available at <$20 with >5mW sustained output, commercially, with multi-field sensor integration | 2028-2030 | Launch HCI-4.1 autonomous sensing pilot immediately |
| Neuromorphic edge chip available at <$10, <50mW, with sufficient TOPS for harmonic signal processing | 2030-2032 | Integrate into HCI-4 sensor node design; launch edge interpretation programme |
| Cesium or equivalent publishes an open streaming standard for Gaussian splat globe-scale delivery | 2027-2028 | Adopt standard; contribute HCI visual field protocol as extension |
| A major competitor (Google, Microsoft, Esri) announces a temporal multi-field spatial substrate | Any | Emergency strategic review; accelerate HCI IP filing; evaluate partnership vs. competition |
| Quantum error correction milestone: logical qubit error rate below 10^-6 at commercial scale | 2030-2035 | Commission HCI-5.1 quantum algorithm benchmark programme |
| Australian government (DCCEEW or equivalent) announces a national spatial data sovereignty programme | Any | Position Harmony as the substrate layer; engage immediately |

---

## Living Document Protocol

This document is updated:
- After every major Harmony architecture session that touches HCI
- When a trigger event in the Decision Gates table occurs
- Quarterly: market intelligence section reviewed and updated
- Annually: Technology Horizon Map revised based on actual progress vs. projections

**Next scheduled review:** July 2026

---

*Harmony Spatial Operating System — Harmonic Cell Initiative — Confidential — April 2026*
