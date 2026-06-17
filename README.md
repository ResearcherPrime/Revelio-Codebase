# Revelio —  A Global Study of VoIP Blocking

## Overview

Revelio-AE is an end-to-end network measurement framework focused on active measurements of STUN servers for censorship and network-security research.

The pipeline supports:

1. Scraping BGP / ASN / prefix information
2. Preparing and merging prefix datasets
3. Large-scale STUN probing using replayed VoIP traffic
4. Behavioral deviation analysis
5. Traceroute-based middlebox inference

The framework emphasizes:

* reproducible experiments
* high-throughput probing
* modular orchestration
* large-scale post-processing

---

# High-Level Workflow

```text
scraping
    ↓
zstun_probing
    ↓
zstun_probing_analysis
    ↓
stun_trace
```

---

# Modules

## 1. Scraping (`scraping/`)

Responsible for:

* country scraping
* ASN scraping
* prefix scraping

Outputs:

* `scraping/asns/`
* `scraping/prefixes/`

These datasets are later reused across all downstream modules.

---

## 2. ZSTUN Probing (`zstun_probing/`)

Performs:

* vanilla STUN probing
* replayed VoIP STUN probing
* modified STUN packet probing

Supported applications:

* WhatsApp
* Telegram
* Signal
* Messenger

Outputs:

* `zstun_probing/output/<COUNTRY>/`

The probing framework uses:

* modified ZMap
* replayed STUN packet captures
* grouped workload balancing

---

## 3. ZSTUN Probing Analysis (`zstun_probing_analysis/`)

Analyzes probing outputs to detect:

* UDP deviations
* ICMP deviations
* No-response deviations

Also generates:

* filtered differential IP datasets
* publication graphs
* behavioral classifications

Outputs:

* `zstun_probing_analysis/output/<COUNTRY>/`

These filtered outputs are later used for traceroute-based analysis.

---

## 4. STUN Trace (`stun_trace/`)

Performs:

* STUN-based traceroutes
* differential path analysis
* middlebox inference
* ASN-level filtering inference

Traceroutes compare:

* vanilla STUN paths
* replayed VoIP STUN paths

Outputs:

* `stun_trace/trace_output/`
* `stun_trace/middleboxes/`

---

# Fast vs Full Mode

## Fast Mode

Designed for:

* artifact evaluation
* quick sanity checks
* runtime verification

Characteristics:

* UAE only
* WhatsApp only
* UDP deviation only
* 10 random traceroutes

Run:

```bash
bash run_fast.sh
```

---

## Full Mode

Designed for:

* complete measurements
* paper-scale experiments
* full middlebox analysis

Characteristics:

* all configured countries
* all applications
* all deviation categories
* full traceroute evaluation

Run:

```bash
bash run_full.sh
```

---

# Repository Structure

```text
.
├── scraping/
├── zstun_probing/
├── zstun_probing_analysis/
├── stun_trace/
├── setup_scripts/
├── external/
├── run_fast.sh
├── run_full.sh
└── README.md
```

---

# Data and Outputs

## Scraping Outputs

```text
scraping/asns/
scraping/prefixes/
```

---

## Probing Outputs

```text
zstun_probing/output/<COUNTRY>/
```

---

## Analysis Outputs

```text
zstun_probing_analysis/output/<COUNTRY>/
```

---

## Traceroute Outputs

```text
stun_trace/trace_output/
```

---

## Middlebox Outputs

```text
stun_trace/middleboxes/
```

---

# Logging

Execution logs are stored under:

```text
logs/exec/
logs/time/
```

These include:

* runtime statistics
* execution diagnostics
* group balancing information
* probing failures
* timing summaries

---

# Installation Notes

## Installation Steps

The repository provides a helper setup script for installing the required dependencies and preparing the environment. Simply run:

```
bash setup.sh
```

The setup script installs:

* Python dependencies
* Scapy and plotting libraries
* modified ZMap dependencies
* required system packages
* virtual environment setup components

Some stages of the framework may require elevated privileges depending on the probing configuration.

---

## Python Dependencies

Typical dependencies include:

* pandas
* scapy
* matplotlib
* beautifulsoup4
* requests
* numpy

---

## Zstun

The framework uses a modified ZMap build for:

* large-scale probing
* STUN replay support
* high-throughput packet generation

See: `zstun_probing/README.md`

---

# Artifact Evaluation Notes

Fast mode is intended for:

* artifact evaluators
* reproducibility checks
* CI validation

Full mode is intended for:

* large-scale measurements
* complete reproduction of experiments

---

# Safety and Ethics

* Respect probing blocklists and local policies
* Perform experiments only from controlled infrastructure
* Rate-limit probing responsibly
* Validate system capacity before high-rate scans
* Some probing stages may require elevated privileges

---

# Notes

* Large-scale probing may take several hours
* ICMP behavior varies significantly across providers
* Traceroute visibility may differ across networks
* The framework uses heuristic-based middlebox inference
* Publication plotting scripts and datasets are included separately inside the plotting directory
