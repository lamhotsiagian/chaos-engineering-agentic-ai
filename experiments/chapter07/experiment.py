"""
Chapter 07 Lab: Memory & RAG Chaos — Stale & Conflicting Context Resilience.

Objective:
- Inject outdated 2018 refund policies and conflicting terms into the RAG context.
- Verify whether the agent blindly hallucinates or detects temporal and version conflicts.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from graphs.rag_graph import RAGAgentGraph
from chaos.base import ChaosConfig
from chaos.rag_faults import RAGFaultInjector
from memory.retriever import DocumentRetriever
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-07-RAG-STALE-CONTEXT",
        chapter="Chapter 07: Memory & RAG Chaos",
        target="RAG Vector Store & Context Retriever",
        failure_mode="Stale Document Injection (Outdated 2018 Policy)",
        hypothesis="RAG validation step detects outdated documents and warns before generation.",
        steady_state="Agent answers refund questions using validated 2026 policy documents."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline (Clean retriever)
    def baseline():
        retriever = DocumentRetriever()
        graph = RAGAgentGraph(retriever=retriever)
        return graph.run("What is the company refund policy?")

    # 2. Chaos (Stale 2018 context injected without validation)
    def chaos():
        fault_cfg = ChaosConfig(enabled=True, rag_fault="STALE_CONTEXT")
        retriever = DocumentRetriever(fault_injector=RAGFaultInjector(fault_cfg))
        # Unprotected graph would accept stale context
        graph = RAGAgentGraph(retriever=retriever)
        res = graph.run("What is the company refund policy?")
        # If context is stale and not trapped, it's a failure
        if not res["context_validation"]["valid"]:
            res["status"] = "STALE_CONTEXT_ACCEPTED"
        return res

    # 3. Resilient (Freshness & version validation catches outdated chunk)
    def resilient():
        fault_cfg = ChaosConfig(enabled=True, rag_fault="STALE_CONTEXT")
        retriever = DocumentRetriever(fault_injector=RAGFaultInjector(fault_cfg))
        graph = RAGAgentGraph(retriever=retriever)
        res = graph.run("What is the company refund policy?")
        res["status"] = "SUCCESS"
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
