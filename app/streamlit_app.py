"""
Agentic AI Chaos Engineering Platform — Streamlit Control Dashboard.

Interactive control plane supporting:
1. Comprehensive Lab Sandbox: Dedicated interactive UI panels for all 15 Chapter Labs.
2. Live Execution Graph Visualizer (Node-by-Node state transitions).
3. Real-Time Observability & OpenTelemetry Tracing Spans.
4. Empirical 6-Pillar Resilience Scorecard (0–100).
5. Automated 15-Chapter Chaos Experiment Runner with Live Report Generation.
"""

import streamlit as st
import time
import sys
import os
import json
import random

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chaos.base import ChaosConfig
from chaos.llm_faults import LLMFaultInjector
from chaos.tool_faults import ToolFaultInjector
from chaos.rag_faults import RAGFaultInjector
from chaos.state_faults import StateFaultInjector
from chaos.network_faults import NetworkFaultInjector, NetworkConnectionException
from chaos.agent_faults import AgentFaultInjector
from chaos.security_faults import SecurityFaultInjector, SecurityPolicyViolation

from resilience.resilience_controller import ResilienceController
from resilience.retry import RetryPolicy, global_idempotency_registry
from resilience.timeout import TimeoutPolicy, ExecutionTimeoutException
from resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from resilience.fallback import FallbackCascade
from resilience.budget import BudgetController, BudgetConfig, BudgetExhaustedException
from resilience.kill_switch import KillSwitch, global_kill_switch
from resilience.escalation import HumanEscalationController, SafetyPolicyMode

from models.llm import get_llm, MockLLMClient, OllamaLLMClient
from models.fallback import ModelFailoverController
from tools.calculator import calculate
from tools.database import global_db_tool
from tools.search import search
from tools.notification import global_notification_service

from memory.short_term import ShortTermMemory
from memory.long_term import CheckpointStore, global_checkpoint_store
from memory.retriever import DocumentRetriever, global_retriever

from graphs.basic_graph import BasicAgentGraph
from graphs.react_graph import ReActAgentGraph
from graphs.rag_graph import RAGAgentGraph
from graphs.workflow_graph import DurableWorkflowGraph
from graphs.multi_agent_graph import MultiAgentGraph

from observability.tracing import global_tracer
from observability.metrics import global_metrics
from evaluation.resilience_score import ResilienceScoreCalculator
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata


st.set_page_config(
    page_title="Agentic AI Chaos Engineering Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Agentic AI Chaos Engineering Platform")
st.caption("A Complete Build-and-Break Laboratory for Agentic AI Reliability, Resilience & Safety")

# -------------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Platform Controls")
    
    use_mock_engine = st.checkbox(
        "Offline / Mock Engine Mode",
        value=True,
        help="Use deterministic offline simulation engine. Uncheck to connect to live local Ollama (http://localhost:11434)."
    )
    
    selected_model = st.selectbox(
        "Primary Model",
        ["qwen2.5:3b", "qwen3:1.7b", "llama3.2:1b", "qwen2.5vl:3b"],
        index=0
    )

    st.divider()
    st.subheader("🔥 Global Fault Toggles")
    global_chaos = st.toggle("Enable Global Chaos", value=False)
    blast_radius = st.slider("Blast Radius", min_value=0.1, max_value=1.0, value=1.0, step=0.1)

    st.divider()
    st.subheader("🛑 Emergency Kill Switch")
    kill_switch_state = st.toggle("Engage Kill Switch", value=global_kill_switch.is_engaged)
    if kill_switch_state and not global_kill_switch.is_engaged:
        global_kill_switch.trip("Operator engaged via UI control panel")
        st.error("🚨 EMERGENCY KILL SWITCH ENGAGED!")
    elif not kill_switch_state and global_kill_switch.is_engaged:
        global_kill_switch.reset()
        st.success("✅ Kill switch reset.")

    st.divider()
    if st.button("🧹 Reset All Metrics & Logs", use_container_width=True):
        global_metrics.reset()
        global_tracer.start_trace()
        global_idempotency_registry.clear()
        global_notification_service.clear()
        st.rerun()


# -------------------------------------------------------------
# NAVIGATION TABS
# -------------------------------------------------------------
tabs = st.tabs([
    "🔬 15 Chapter Labs Sandbox",
    "🎯 Agent Playground",
    "📈 Observability & Tracing",
    "🛡️ Resilience Scorecard",
    "🧪 Batch Experiment Suite"
])


# =============================================================
# TAB 1: 15 CHAPTER LABS SANDBOX
# =============================================================
with tabs[0]:
    st.subheader("Interactive Chapter Labs (Chapters 01 – 15)")
    st.markdown("Select a specific chapter lab to configure parameters, inject faults, and test resilience mechanisms live.")

    selected_chapter = st.selectbox(
        "Select Chapter Lab to Test",
        [
            "Chapter 01: Chaos Engineering Foundations (Baseline vs Delay/Crash)",
            "Chapter 02: Agentic AI Failure Model (Node-by-Node Failure Map)",
            "Chapter 03: LLM Chaos Engineering (3-Tier Model Failover Cascade)",
            "Chapter 04: Agent Loop Chaos (Infinite Loop & Execution Budget Controller)",
            "Chapter 05: Tool & API Chaos (Idempotent Tool Execution & Duplicate Prevention)",
            "Chapter 06: MCP Chaos Engineering (Dynamic Tool Unavailability & Fallback)",
            "Chapter 07: Memory & RAG Chaos (Stale, Conflicting & Poisoned Context)",
            "Chapter 08: Agent State & Workflow Chaos (Kill-and-Resume Durable Execution)",
            "Chapter 09: Multi-Agent Chaos (Supervisor & Worker Team Failover)",
            "Chapter 10: Infrastructure & Distributed Chaos (Network Jitter & ECONNRESET)",
            "Chapter 11: Security Chaos (Prompt Injection & Restricted Tool Defense)",
            "Chapter 12: Guardrail & Human Chaos (Fail-Closed vs Fail-Open Policies)",
            "Chapter 13: Agent Observability (Distributed Spans & Root-Cause Diagnosis)",
            "Chapter 14: Resilience & Recovery Patterns (100-Task Stochastic Chaos Benchmark)",
            "Chapter 15: Production Capstone Platform (Full Multi-Domain Resilience Test)"
        ]
    )

    ch_num = int(selected_chapter.split(":")[0].replace("Chapter ", ""))

    st.markdown("---")

    # ---------------------------------------------------------
    # LAB 01
    # ---------------------------------------------------------
    if ch_num == 1:
        st.markdown("### 🧪 Lab 01: First Chaos-Ready Agent")
        st.info("Test baseline steady state vs injected model delay, runtime exception, or empty response.")

        c1, c2 = st.columns(2)
        with c1:
            l1_prompt = st.text_input("User Prompt", value="Explain chaos engineering in one paragraph.")
            l1_mode = st.radio("Chaos Injection Mode", ["NORMAL (Steady State)", "DELAY (Latency Spike)", "EXCEPTION (Crash)", "EMPTY (Blank Response)"])
        with c2:
            st.markdown("**Expected Behavior:**")
            st.markdown("- **Normal**: Success in < 100ms.")
            st.markdown("- **Delay**: Latency measured at > 2.0s without crashing.")
            st.markdown("- **Exception**: Injected runtime error trapped with error containment.")
            st.markdown("- **Empty**: Blank response detected by client.")

        if st.button("▶️ Execute Lab 01 Test", type="primary"):
            agent = BasicAgentGraph(llm_client=get_llm(model_name=selected_model, use_mock=use_mock_engine))
            fail_mode = None
            chaos_on = False
            if "DELAY" in l1_mode:
                chaos_on, fail_mode = True, "DELAY"
            elif "EXCEPTION" in l1_mode:
                chaos_on, fail_mode = True, "EXCEPTION"
            elif "EMPTY" in l1_mode:
                chaos_on, fail_mode = True, "EMPTY"

            res = agent.run(l1_prompt, chaos_enabled=chaos_on, fail_mode=fail_mode)
            st.json(res)

    # ---------------------------------------------------------
    # LAB 02
    # ---------------------------------------------------------
    elif ch_num == 2:
        st.markdown("### 🧪 Lab 02: Agentic AI Failure Model (Failure Map)")
        st.info("Inject failures into individual cognitive nodes to observe error propagation and blast radius.")

        col1, col2, col3, col4 = st.columns(4)
        fail_planner = col1.checkbox("💥 Fail Planner Node", value=False)
        fail_router = col2.checkbox("💥 Fail Router Node", value=False)
        fail_tool = col3.checkbox("💥 Fail Tool Node", value=False)
        fail_evaluator = col4.checkbox("💥 Fail Evaluator Node", value=False)

        l2_objective = st.text_input("Objective", value="Calculate 25 * 4 and query database for user:101")

        if st.button("▶️ Execute Lab 02 Failure Map Test", type="primary"):
            cfg = ChaosConfig(
                enabled=(fail_planner or fail_router or fail_tool or fail_evaluator),
                agent_fault=(
                    "PLANNER_FAILURE" if fail_planner else
                    "ROUTER_FAILURE" if fail_router else
                    "EVALUATOR_FAILURE" if fail_evaluator else None
                ),
                tool_fault="500" if fail_tool else None
            )
            graph = ReActAgentGraph(llm_client=get_llm(selected_model, use_mock=use_mock_engine), chaos_config=cfg)
            res = graph.run(l2_objective)
            st.json(res)

    # ---------------------------------------------------------
    # LAB 03
    # ---------------------------------------------------------
    elif ch_num == 3:
        st.markdown("### 🧪 Lab 03: LLM Chaos Gateway & 3-Tier Model Failover")
        st.info("Break the primary model dependency and observe automatic cascading: Qwen 3B ➔ Qwen 1.7B ➔ Llama 1B ➔ Safe Degraded Mode.")

        fault_choice = st.selectbox("Primary Model Injected Fault", ["NONE (Healthy)", "ERROR (HTTP 500 Outage)", "TIMEOUT (Request Dropped)", "RATE_LIMIT (HTTP 429)"])
        l3_prompt = st.text_input("Prompt", value="Summarize agent reliability principles.")

        if st.button("▶️ Execute Lab 03 Failover Test", type="primary"):
            cfg = ChaosConfig(
                enabled=(fault_choice != "NONE (Healthy)"),
                llm_fault=fault_choice.split(" ")[0],
                target_model="qwen2.5:3b"
            )
            injector = LLMFaultInjector(cfg)
            controller = ModelFailoverController(use_mock=use_mock_engine, fault_injector=injector)
            provider, output = controller.generate_with_fallback(l3_prompt)
            
            st.success(f"Execution Handled by Model Tier: **{provider}**")
            st.write(output)

    # ---------------------------------------------------------
    # LAB 04
    # ---------------------------------------------------------
    elif ch_num == 4:
        st.markdown("### 🧪 Lab 04: Agent Loop Chaos & Execution Budget Controller")
        st.info("Simulate a runaway autonomous agent loop and test budget containment.")

        b1, b2, b3 = st.columns(3)
        max_iter = b1.slider("Max Allowed Iterations", min_value=1, max_value=10, value=3)
        max_tools = b2.slider("Max Allowed Tool Calls", min_value=1, max_value=10, value=5)
        force_loop = b3.toggle("Force Infinite Reasoning Loop", value=True)

        if st.button("▶️ Execute Lab 04 Budget Test", type="primary"):
            cfg = ChaosConfig(enabled=force_loop, agent_fault="INFINITE_LOOP" if force_loop else None)
            budget_cfg = BudgetConfig(max_iterations=max_iter, max_tool_calls=max_tools)
            graph = ReActAgentGraph(
                llm_client=get_llm(selected_model, use_mock=use_mock_engine),
                chaos_config=cfg,
                budget_config=budget_cfg
            )
            res = graph.run("Calculate 10 + 10")
            if res.get("status") == "FAILED" and "budget exhausted" in res.get("error", "").lower():
                st.warning(f"🛡️ Budget Guard Activated: {res.get('error')}")
            st.json(res)

    # ---------------------------------------------------------
    # LAB 05
    # ---------------------------------------------------------
    elif ch_num == 5:
        st.markdown("### 🧪 Lab 05: Tool & API Chaos — Idempotent Execution")
        st.info("Demonstrate how retries on side-effecting tools cause duplicate transactions without idempotency keys.")

        enable_idempotency = st.toggle("Enable Idempotency Key Protection", value=True)
        idempotency_key = "order_confirm_tx_909" if enable_idempotency else None

        if st.button("▶️ Execute Lab 05 Duplicate Test", type="primary"):
            global_notification_service.clear()
            controller = ResilienceController()

            st.write("Executing tool call attempt 1...")
            r1 = controller.execute_guarded(
                global_notification_service.send_notification,
                "customer@example.com",
                "Your order #909 is confirmed",
                idempotency_key=idempotency_key
            )

            st.write("Executing duplicate tool retry attempt 2...")
            r2 = controller.execute_guarded(
                global_notification_service.send_notification,
                "customer@example.com",
                "Your order #909 is confirmed",
                idempotency_key=idempotency_key
            )

            sent_count = len(global_notification_service.sent_notifications)
            if sent_count == 1:
                st.success(f"✅ Idempotency Verified: Exactly 1 notification sent despite duplicate retries!")
            else:
                st.error(f"❌ Duplicate Side-Effect Detected: {sent_count} notifications dispatched!")
            st.json({"sent_notifications_log": global_notification_service.sent_notifications})

    # ---------------------------------------------------------
    # LAB 06
    # ---------------------------------------------------------
    elif ch_num == 6:
        st.markdown("### 🧪 Lab 06: MCP Chaos — Dynamic Tool Unavailability")
        st.info("Simulate Model Context Protocol (MCP) tool provider outage during reasoning.")

        mcp_fault = st.selectbox("MCP Server Status", ["HEALTHY", "SERVICE_UNAVAILABLE (503)", "CONNECTION_RESET"])
        if st.button("▶️ Execute Lab 06 MCP Test", type="primary"):
            cfg = ChaosConfig(
                enabled=(mcp_fault != "HEALTHY"),
                network_fault="SERVICE_UNAVAILABLE" if "503" in mcp_fault else "CONNECTION_RESET"
            )
            injector = NetworkFaultInjector(cfg)
            try:
                injector.intercept("mcp://tools.production.internal:9000")
                st.success("✅ MCP Server reachable. Tools successfully loaded.")
            except Exception as exc:
                st.warning(f"⚠️ MCP Server Outage Detected ({exc}). Falling back to local calculator.")
                local_res = calculate("50 * 2")
                st.success(f"✅ Local Fallback Executed: {local_res}")

    # ---------------------------------------------------------
    # LAB 07
    # ---------------------------------------------------------
    elif ch_num == 7:
        st.markdown("### 🧪 Lab 07: Memory & RAG Chaos — Knowledge Corruption")
        st.info("Inject stale 2018 documents or conflicting terms into the RAG vector retriever.")

        rag_mode = st.selectbox("RAG Fault Mode", ["CLEAN (2026 Documents)", "STALE_CONTEXT (2018 Policy)", "CONFLICTING_CONTEXT", "VECTOR_DB_FAILURE"])
        rag_query = st.text_input("RAG Query", value="What is the refund policy?")

        if st.button("▶️ Execute Lab 07 RAG Test", type="primary"):
            cfg = ChaosConfig(
                enabled=(rag_mode != "CLEAN (2026 Documents)"),
                rag_fault=None if "CLEAN" in rag_mode else rag_mode
            )
            retriever = DocumentRetriever(fault_injector=RAGFaultInjector(cfg))
            agent = RAGAgentGraph(llm_client=get_llm(selected_model, use_mock=use_mock_engine), retriever=retriever)
            res = agent.run(rag_query)
            st.json(res)

    # ---------------------------------------------------------
    # LAB 08
    # ---------------------------------------------------------
    elif ch_num == 8:
        st.markdown("### 🧪 Lab 08: State Chaos — Kill-and-Resume Workflow")
        st.info("Simulate abrupt process termination mid-pipeline and resume from durable state checkpoints.")

        thread_id = st.text_input("Workflow Thread ID", value="thread_risk_eval_42")
        kill_stage = st.selectbox("Simulate Process Kill at Stage", ["NONE (Complete Run)", "STAGE 2 (Analyze)", "STAGE 3 (Validate)"])

        c_run, c_resume = st.columns(2)
        with c_run:
            if st.button("▶️ Run Workflow (with simulated crash)"):
                global_checkpoint_store.clear(thread_id)
                cfg = ChaosConfig(
                    enabled=(kill_stage != "NONE (Complete Run)"),
                    state_fault="PROCESS_KILL"
                )
                graph = DurableWorkflowGraph(checkpoint_store=global_checkpoint_store, state_faults=StateFaultInjector(cfg))
                res = graph.run(thread_id=thread_id, topic="Financial Risk 2026")
                st.json(res)

        with c_resume:
            if st.button("🔄 Resume Workflow from Last Checkpoint"):
                graph = DurableWorkflowGraph(checkpoint_store=global_checkpoint_store)
                res = graph.run(thread_id=thread_id, topic="Financial Risk 2026", resume=True)
                st.success(f"✅ Workflow Resumed & Completed! Total Steps: {res.get('completed_steps')}")
                st.json(res)

    # ---------------------------------------------------------
    # LAB 09
    # ---------------------------------------------------------
    elif ch_num == 9:
        st.markdown("### 🧪 Lab 09: Multi-Agent Chaos — Worker Failover")
        st.info("Test supervisor orchestration when a specialized worker (Researcher) crashes.")

        kill_worker = st.selectbox("Worker Failure Injection", ["NONE (All Healthy)", "RESEARCHER_FAILURE", "ANALYST_FAILURE"])
        mission = st.text_input("Team Mission", value="Analyze quantum computing market forecast")

        if st.button("▶️ Execute Lab 09 Multi-Agent Test", type="primary"):
            cfg = ChaosConfig(enabled=(kill_worker != "NONE (All Healthy)"), agent_fault=kill_worker if kill_worker != "NONE (All Healthy)" else None)
            team = MultiAgentGraph(
                supervisor_llm=get_llm("qwen2.5:3b", use_mock=use_mock_engine),
                worker_llm=get_llm("qwen3:1.7b", use_mock=use_mock_engine),
                chaos_config=cfg
            )
            res = team.run(mission)
            st.json(res)

    # ---------------------------------------------------------
    # LAB 10
    # ---------------------------------------------------------
    elif ch_num == 10:
        st.markdown("### 🧪 Lab 10: Infrastructure Chaos — Network Jitter & Drops")
        st.info("Simulate transient network connection drops and verify exponential backoff with jitter.")

        net_fault = st.selectbox("Transport Fault", ["CONNECTION_RESET (ECONNRESET)", "LATENCY (2.0s Delay)", "REQUEST_LOSS (Packet Drop)"])
        max_retries = st.slider("Client Max Retries", min_value=1, max_value=5, value=3)

        if st.button("▶️ Execute Lab 10 Network Test", type="primary"):
            attempt = 0
            def flaky_rpc():
                nonlocal attempt
                attempt += 1
                if attempt < 2:
                    raise NetworkConnectionException("ECONNRESET: Connection reset by peer")
                return {"status": "SUCCESS", "attempts_needed": attempt}

            controller = ResilienceController(max_retries=max_retries)
            res = controller.execute_guarded(flaky_rpc)
            st.success(f"✅ Recovered via Retry! Attempts: {res.get('attempts_needed')}")
            st.json(res)

    # ---------------------------------------------------------
    # LAB 11
    # ---------------------------------------------------------
    elif ch_num == 11:
        st.markdown("### 🧪 Lab 11: Security Chaos — Prompt & Tool Injection Defense")
        st.info("Simulate direct/indirect prompt injection and test security authorization guardrails.")

        sec_attack = st.selectbox("Attack Mode", ["DIRECT_PROMPT_INJECTION", "RESTRICTED_TOOL_ATTEMPT"])
        if st.button("▶️ Execute Lab 11 Security Test", type="primary"):
            injector = SecurityFaultInjector(ChaosConfig(enabled=True, security_fault="RESTRICTED_TOOL" if "TOOL" in sec_attack else "PROMPT_INJECTION"))
            if "TOOL" in sec_attack:
                try:
                    injector.check_tool_authorization("delete_customer_records", ["calculator", "search"])
                    st.error("❌ Attack Succeeded: Unauthorized tool was not blocked!")
                except SecurityPolicyViolation as exc:
                    st.success(f"🛡️ Security Guardrail Blocked Attack: {exc}")
            else:
                hijacked = injector.mutate_user_prompt("Calculate 100 * 2")
                st.warning("Adversarial Mutated Prompt:")
                st.code(hijacked)

    # ---------------------------------------------------------
    # LAB 12
    # ---------------------------------------------------------
    elif ch_num == 12:
        st.markdown("### 🧪 Lab 12: Guardrail Chaos — Fail-Closed vs Fail-Open Policies")
        st.info("Demonstrate what happens when the safety guardrail itself crashes.")

        policy_choice = st.radio("Safety Policy", ["FAIL_CLOSED (High Safety: Block Action)", "FAIL_OPEN (High Availability: Allow Action)"])
        mode = SafetyPolicyMode.FAIL_CLOSED if "FAIL_CLOSED" in policy_choice else SafetyPolicyMode.FAIL_OPEN

        if st.button("▶️ Execute Lab 12 Guardrail Test", type="primary"):
            controller = HumanEscalationController(policy_mode=mode)
            sim_err = RuntimeError("Safety classification model unavailable (500)")
            allowed = controller.evaluate_guardrail_failure("wire_transfer_$10,000", sim_err)

            if not allowed:
                st.success("🛡️ Action BLOCKED safely under Fail-Closed policy and escalated to human supervisor.")
            else:
                st.error("⚠️ Action ALLOWED dangerously under Fail-Open policy.")

    # ---------------------------------------------------------
    # LAB 13
    # ---------------------------------------------------------
    elif ch_num == 13:
        st.markdown("### 🧪 Lab 13: Agent Observability — Distributed Spans & Tracing")
        st.info("Generate nested execution spans and diagnose error root cause in real time.")

        if st.button("▶️ Generate Multi-Span Execution Trace", type="primary"):
            global_tracer.start_trace()
            with global_tracer.span("root:transaction_pipeline"):
                with global_tracer.span("node:planner", {"model": selected_model}):
                    time.sleep(0.01)
                with global_tracer.span("node:tool:database_query", {"key": "user:101"}):
                    time.sleep(0.02)
                with global_tracer.span("node:evaluator") as s:
                    s.set_attribute("evaluation_score", 0.98)

            spans = global_tracer.get_traces_summary()
            st.dataframe(spans, use_container_width=True)

    # ---------------------------------------------------------
    # LAB 14
    # ---------------------------------------------------------
    elif ch_num == 14:
        st.markdown("### 🧪 Lab 14: Resilience Benchmark (100 Tasks Stochastic Test)")
        st.info("Run 100 tasks under stochastic fault injection and compare Without vs With Resilience.")

        fault_pct = st.slider("Random Fault Injection Probability", min_value=0.1, max_value=0.8, value=0.3, step=0.1)

        if st.button("▶️ Run 100-Task Benchmark", type="primary"):
            with st.spinner("Executing 100 tasks under chaos..."):
                controller = ResilienceController(max_retries=3)
                
                # Run without resilience
                unprot_success = sum(1 for _ in range(100) if random.random() >= fault_pct)
                
                # Run with resilience
                prot_success = 0
                for i in range(100):
                    try:
                        def _work():
                            if random.random() < fault_pct:
                                raise RuntimeError("Intermittent glitch")
                            return True
                        controller.execute_guarded(_work)
                        prot_success += 1
                    except Exception:
                        pass

                c_u, c_p = st.columns(2)
                c_u.metric("Without Resilience (Success Rate)", f"{unprot_success}%")
                c_p.metric("WITH Resilience Controller (Success Rate)", f"{prot_success}%", delta=f"+{prot_success - unprot_success}%")

    # ---------------------------------------------------------
    # LAB 15
    # ---------------------------------------------------------
    elif ch_num == 15:
        st.markdown("### 🧪 Lab 15: Final Capstone — Complete Platform Resilience Test")
        st.info("Execute end-to-end multi-layer chaos test and compute official Resilience Scorecard.")

        if st.button("▶️ Execute Capstone Platform Test", type="primary"):
            with st.spinner("Running full chaos evaluation engine..."):
                calc = ResilienceScoreCalculator()
                graph = ReActAgentGraph(llm_client=get_llm(selected_model, use_mock=use_mock_engine))
                res = graph.run("Calculate 25 * 4 and query database for user:101")
                
                scorecard = calc.compute(snapshot=global_metrics.get_snapshot())
                st.markdown(f"## **Platform Resilience Score: {scorecard.total_score:.1f} / 100**")
                st.text(scorecard.render_ascii_card())


# =============================================================
# TAB 2: AGENT PLAYGROUND
# =============================================================
with tabs[1]:
    st.subheader("Interactive Agent Playground")
    col1, col2 = st.columns([3, 1])
    with col1:
        pg_prompt = st.text_area("User Objective / Command", value="Calculate 25 * 4 and query database for user:101", height=120)
    with col2:
        pg_topology = st.selectbox("Agent Topology", ["ReAct Loop", "RAG Knowledge", "Multi-Agent Team"])
        pg_idempotency = st.text_input("Idempotency Key (Optional)", value="play_tx_101")
        pg_run = st.button("🚀 Run Agent", type="primary", use_container_width=True)

    if pg_run:
        with st.spinner("Agent running..."):
            client = get_llm(selected_model, use_mock=use_mock_engine)
            active_cfg = ChaosConfig(enabled=global_chaos, blast_radius=blast_radius)

            if pg_topology == "ReAct Loop":
                g = ReActAgentGraph(llm_client=client, chaos_config=active_cfg)
                out = g.run(pg_prompt, idempotency_key=pg_idempotency)
            elif pg_topology == "RAG Knowledge":
                g = RAGAgentGraph(llm_client=client)
                out = g.run(pg_prompt)
            else:
                g = MultiAgentGraph(supervisor_llm=client, chaos_config=active_cfg)
                out = g.run(pg_prompt)

            st.session_state["pg_out"] = out

        st.success("Execution Complete!")
        st.json(out)


# =============================================================
# TAB 3: OBSERVABILITY & TRACING
# =============================================================
with tabs[2]:
    st.subheader("Observability & OpenTelemetry Metrics")
    m_dict = global_metrics.to_dict()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Success Rate", f"{m_dict['success_rate_pct']}%")
    m2.metric("Recovery Rate", f"{m_dict['recovery_rate_pct']}%")
    m3.metric("P95 Latency", f"{m_dict['p95_latency_sec']}s")
    m4.metric("Faults Injected", m_dict["faults_injected"])

    st.subheader("Execution Spans")
    spans = global_tracer.get_traces_summary()
    if spans:
        st.dataframe(spans, use_container_width=True)
    else:
        st.info("No active spans recorded yet. Execute a lab or playground command to generate traces.")


# =============================================================
# TAB 4: RESILIENCE SCORECARD
# =============================================================
with tabs[3]:
    st.subheader("Standard 6-Pillar Agent Resilience Scorecard")
    calc = ResilienceScoreCalculator()
    card = calc.compute(snapshot=global_metrics.get_snapshot())

    st.markdown(f"## **Total Resilience Score: {card.total_score:.1f} / 100**")
    st.progress(min(1.0, card.total_score / 100.0))

    r1, r2, r3 = st.columns(3)
    r1.metric("Reliability", f"{card.reliability} / 20")
    r1.metric("Recovery", f"{card.recovery} / 20")
    r2.metric("Safety", f"{card.safety} / 20")
    r2.metric("Security", f"{card.security} / 20")
    r3.metric("Observability", f"{card.observability} / 10")
    r3.metric("Cost Control", f"{card.cost_control} / 10")

    st.text(card.render_ascii_card())


# =============================================================
# TAB 5: BATCH EXPERIMENT SUITE
# =============================================================
with tabs[4]:
    st.subheader("Automated 15-Chapter Experiment Batch Runner")
    
    selected_exp = st.selectbox(
        "Choose Chapter Experiment to Execute",
        [f"Chapter {i:02d}" for i in range(1, 16)]
    )

    if st.button("🧪 Run Selected Experiment Batch", type="primary"):
        ch_idx = int(selected_exp.replace("Chapter ", ""))
        exp_module_name = f"experiments.chapter{ch_idx:02d}.experiment"
        
        with st.spinner(f"Executing {selected_exp} Chaos Experiment..."):
            mod = __import__(exp_module_name, fromlist=["run_experiment"])
            exp_output = mod.run_experiment()

        st.success(f"Experiment Completed: Result = {exp_output['result']}")
        st.text(exp_output["report"])
