# Chaos Engineering for Agentic AI — Laboratory Platform

Welcome to the companion codebase and hands-on laboratory for **Chaos Engineering for Agentic AI**.

> *"An Agentic AI system is not production-ready because it can complete tasks reliably. It is production-ready when it can fail predictably, contain failures, recover safely, remain observable, and prevent unsafe actions under failure."*

---

## 🏗️ Architecture Overview

The lab is designed as a single, progressive local-first repository that implements:
1. **Fault Injection Layer (`chaos/`)**: Injects deterministic and stochastic failures into LLM APIs, Agent Loops, Tool Executions, RAG Retrieval, Network connections, and Workflow states.
2. **Resilience Engine (`resilience/`)**: Provides engineering controls including exponential retry policies, strict timeouts, circuit breakers, multi-tier model fallbacks, execution budget controllers, kill switches, and human escalation policies.
3. **Observability Stack (`observability/`)**: OpenTelemetry-compatible tracing, Prometheus metrics collection, and contextual event logging.
4. **LangGraph Agent Runtimes (`graphs/` & `agents/`)**: Production-grade ReAct, RAG, Workflow, and Multi-Agent topologies with explicit failure boundaries.
5. **Evaluation Engine (`evaluation/`)**: Automates the 10-step Chaos Experiment Lifecycle and computes the standardized 6-pillar **Resilience Score** (0–100).
6. **Streamlit Control Dashboard (`app/`)**: Interactive 5-tab control plane for live fault injection, telemetry visualization, and experiment execution.

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- (Optional for live LLMs) [Ollama](https://ollama.com/) with:
  ```bash
  ollama pull qwen2.5:3b
  ollama pull qwen3:1.7b
  ollama pull llama3.2:1b
  ollama pull nomic-embed-text
  ```

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```

### 4. Run Chapter Experiments
```bash
# Run a specific chapter experiment:
python3 experiments/chapter01/experiment.py
python3 experiments/chapter04/experiment.py
python3 experiments/chapter08/experiment.py

# Run all 15 experiments sequentially:
make run-experiments
```

### 5. Run Automated Tests
```bash
make test
```

---

## 📚 15 Chapter Lab Directory

| Chapter | Focus Area | Key Lab Deliverable |
|---|---|---|
| **01** | Foundations | First Chaos-Ready Agent + Latency Instrumentation |
| **02** | Failure Taxonomy | Agent Failure Map & Node Fault Injection Panel |
| **03** | LLM Chaos | Chaos LLM Gateway & 3-Tier Model Failover Cascade |
| **04** | Loop Chaos | Execution Budget Controller (Iterations, Tools, Time) |
| **05** | Tool Chaos | Idempotent Tool Execution Framework & Duplicate Prevention |
| **06** | MCP Chaos | MCP Dynamic Tool Unavailability & Fallback Test Suite |
| **07** | RAG Chaos | RAG Resilience Evaluation (Stale, Conflicting & Poisoned Context) |
| **08** | State Chaos | Kill-and-Resume Durable Workflow with LangGraph Checkpointing |
| **09** | Multi-Agent Chaos | Supervisor & Worker Team Failure Recovery Controller |
| **10** | Infra Chaos | Network Jitter, Timeout & Connection Reset Simulator |
| **11** | Security Chaos | Security Chaos Regression Suite (Prompt & Tool Injection) |
| **12** | Guardrails | Fail-Closed vs Fail-Open Controller & Human Approval Timeouts |
| **13** | Observability | OpenTelemetry Tracing, Prometheus Metrics & Root Cause Analyzer |
| **14** | Resilience | Unified Resilience Controller Benchmark (100 Scenarios) |
| **15** | Production Capstone | Agent Chaos Engineering Platform & 6-Pillar Score Calculator |
# chaos-engineering-agentic-ai
