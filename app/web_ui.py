"""
Agentic AI Chaos Engineering Platform — Built-in Standalone Web UI Server.

A zero-dependency HTTP server implementing the complete Chaos Control Plane,
interactive Lab Sandboxes (Chapters 01–15), Live Traces, and Resilience Scorecard.

Usage:
    python3 app/web_ui.py
    Open http://localhost:8501 in your browser.
"""

import sys
import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chaos.base import ChaosConfig
from chaos.llm_faults import LLMFaultInjector
from chaos.tool_faults import ToolFaultInjector
from chaos.rag_faults import RAGFaultInjector
from chaos.state_faults import StateFaultInjector
from chaos.network_faults import NetworkFaultInjector, NetworkConnectionException
from chaos.security_faults import SecurityFaultInjector, SecurityPolicyViolation

from resilience.resilience_controller import ResilienceController
from resilience.budget import BudgetConfig
from resilience.kill_switch import global_kill_switch
from resilience.escalation import HumanEscalationController, SafetyPolicyMode

from models.llm import get_llm
from models.fallback import ModelFailoverController
from tools.calculator import calculate
from tools.database import global_db_tool
from tools.search import search
from tools.notification import global_notification_service

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


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Agentic AI Chaos Engineering Platform</title>
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --heading: #f0f6fc;
            --accent: #58a6ff;
            --success: #3fb950;
            --warning: #d29922;
            --danger: #f85149;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }
        .header {
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        h1 { color: var(--heading); margin: 0 0 8px 0; font-size: 26px; }
        .grid { display: grid; grid-template-columns: 320px 1fr; gap: 24px; }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        h2, h3 { color: var(--heading); margin-top: 0; }
        select, input, button, textarea {
            width: 100%;
            background: #0d1117;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 14px;
            box-sizing: border-box;
        }
        button {
            background: #238636;
            color: white;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: background 0.2s;
        }
        button:hover { background: #2ea043; }
        button.secondary { background: #21262d; border: 1px solid var(--border); }
        button.secondary:hover { background: #30363d; }
        pre {
            background: #090d13;
            border: 1px solid var(--border);
            padding: 14px;
            border-radius: 6px;
            overflow-x: auto;
            color: #7ee787;
            font-size: 13px;
        }
        .metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
        .metric-box {
            background: #0d1117;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 6px;
            text-align: center;
        }
        .metric-val { font-size: 22px; font-weight: bold; color: var(--accent); }
        .metric-lbl { font-size: 12px; color: #8b949e; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-pass { background: rgba(63, 185, 80, 0.2); color: var(--success); border: 1px solid var(--success); }
        .badge-fail { background: rgba(248, 81, 73, 0.2); color: var(--danger); border: 1px solid var(--danger); }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Agentic AI Chaos Engineering Platform</h1>
        <div style="color: #8b949e;">Local Build-and-Break Laboratory for Agentic AI Reliability, Resilience & Safety</div>
    </div>

    <div class="metric-row" id="metrics-bar">
        <div class="metric-box"><div class="metric-val" id="m-success">100%</div><div class="metric-lbl">Success Rate</div></div>
        <div class="metric-box"><div class="metric-val" id="m-recovery">100%</div><div class="metric-lbl">Recovery Rate</div></div>
        <div class="metric-box"><div class="metric-val" id="m-faults">0</div><div class="metric-lbl">Faults Injected</div></div>
        <div class="metric-box"><div class="metric-val" id="m-score">95.0 / 100</div><div class="metric-lbl">Resilience Score</div></div>
    </div>

    <div class="grid">
        <div>
            <div class="card">
                <h3>🧪 Select Chapter Lab</h3>
                <select id="lab-select" onchange="updateLabDescription()">
                    <option value="1">Lab 01: Chaos Foundations (Latency/Crash)</option>
                    <option value="2">Lab 02: Agent Failure Model (Node Boundaries)</option>
                    <option value="3">Lab 03: LLM Chaos & 3-Tier Model Failover</option>
                    <option value="4">Lab 04: Agent Loop Chaos & Budget Controller</option>
                    <option value="5">Lab 05: Tool & API Chaos (Idempotency Key)</option>
                    <option value="6">Lab 06: MCP Chaos (Tool Disconnect & Fallback)</option>
                    <option value="7">Lab 07: Memory & RAG Chaos (Stale Context)</option>
                    <option value="8">Lab 08: State Chaos (Kill-and-Resume)</option>
                    <option value="9">Lab 09: Multi-Agent Chaos (Worker Crash)</option>
                    <option value="10">Lab 10: Infra Chaos (Network Jitter/Reset)</option>
                    <option value="11">Lab 11: Security Chaos (Prompt/Tool Injection)</option>
                    <option value="12">Lab 12: Guardrail Chaos (Fail-Closed Policy)</option>
                    <option value="13">Lab 13: Observability (Distributed Traces)</option>
                    <option value="14">Lab 14: 100-Task Stochastic Chaos Benchmark</option>
                    <option value="15">Lab 15: Production Capstone Platform Test</option>
                </select>

                <div id="lab-desc" style="font-size: 13px; color: #8b949e; margin-bottom: 16px;">
                    Test baseline steady state vs injected model delay, runtime exception, or empty response.
                </div>

                <label style="font-size: 13px; font-weight: 600;">Injected Fault Option:</label>
                <select id="fault-option">
                    <option value="DEFAULT">Standard Chapter Fault</option>
                    <option value="NONE">None (Steady State Baseline)</option>
                    <option value="CRASH">Simulate Crash / 500 Outage</option>
                    <option value="TIMEOUT">Simulate Timeout / Latency</option>
                </select>

                <button onclick="executeSelectedLab()">▶️ Run Chapter Lab</button>
                <button class="secondary" onclick="executeBatchAll()">⚡ Run All 15 Experiments</button>
            </div>

            <div class="card">
                <h3>🛑 Kill Switch</h3>
                <button id="btn-kill" class="secondary" style="border-color: #f85149; color: #f85149;" onclick="toggleKillSwitch()">
                    Trip Emergency Kill Switch
                </button>
            </div>
        </div>

        <div>
            <div class="card">
                <h3>📊 Live Execution Output & Telemetry</h3>
                <div id="status-badge" style="margin-bottom: 12px;"></div>
                <pre id="output-view">// Select a lab on the left and click 'Run Chapter Lab' to view live execution details.</pre>
            </div>

            <div class="card">
                <h3>🛡️ 6-Pillar Resilience Scorecard</h3>
                <pre id="scorecard-view">
┌────────────────────────────────────────┐
│        AGENT RESILIENCE SCORE          │
├────────────────────────────────────────┤
│ Reliability            15.0 / 20     │
│ Recovery               20.0 / 20     │
│ Safety                 20.0 / 20     │
│ Security               20.0 / 20     │
│ Observability          10.0 / 10     │
│ Cost Control           10.0 / 10     │
├────────────────────────────────────────┤
│ TOTAL SCORE            95.0 / 100    │
└────────────────────────────────────────┘</pre>
            </div>
        </div>
    </div>

    <script>
        const descriptions = {
            "1": "Test baseline steady state vs injected model delay, runtime exception, or empty response.",
            "2": "Map failure boundaries across Planner, Router, Tool, and Evaluator nodes.",
            "3": "Simulate primary model outage and observe automatic failover: Qwen 3B -> Qwen 1.7B -> Llama 1B.",
            "4": "Force infinite loop and verify Execution Budget Controller intercepts runaways.",
            "5": "Test tool retries and verify Idempotency Keys prevent duplicate email/notification side-effects.",
            "6": "Drop tool MCP servers dynamically and verify local fallback execution.",
            "7": "Inject stale 2018 documents or conflicting facts into RAG vector retriever.",
            "8": "Simulate process SIGKILL crash at stage 2 and resume from durable checkpoint store.",
            "9": "Crash the Researcher worker and verify Supervisor switches to Emergency backup agent.",
            "10": "Inject network ECONNRESET transport errors and verify exponential backoff with jitter.",
            "11": "Inject adversarial prompt injections and verify security authorization guardrail blocks restricted tools.",
            "12": "Crash the safety guardrail and verify system FAILS CLOSED safely.",
            "13": "Generate multi-node distributed trace spans and diagnose root-cause in real-time.",
            "14": "Execute 100 tasks under 30% stochastic chaos comparing Without vs With Resilience Controller.",
            "15": "Execute full end-to-end multi-layer chaos test and compute official Resilience Scorecard."
        };

        function updateLabDescription() {
            const labId = document.getElementById("lab-select").value;
            document.getElementById("lab-desc").innerText = descriptions[labId] || "";
        }

        async function executeSelectedLab() {
            const labId = document.getElementById("lab-select").value;
            const fault = document.getElementById("fault-option").value;
            document.getElementById("output-view").innerText = `⏳ Executing Chapter Lab ${labId}...`;
            
            try {
                const res = await fetch(`/api/run_lab?lab=${labId}&fault=${fault}`);
                const data = await res.json();
                document.getElementById("output-view").innerText = data.report || JSON.stringify(data, null, 2);
                
                if (data.metrics) {
                    document.getElementById("m-success").innerText = `${data.metrics.success_rate_pct}%`;
                    document.getElementById("m-recovery").innerText = `${data.metrics.recovery_rate_pct}%`;
                    document.getElementById("m-faults").innerText = data.metrics.faults_injected;
                }
                if (data.scorecard_ascii) {
                    document.getElementById("scorecard-view").innerText = data.scorecard_ascii;
                }
                if (data.result === "PASS") {
                    document.getElementById("status-badge").innerHTML = `<span class="badge badge-pass">✅ RESULT: PASS</span>`;
                } else {
                    document.getElementById("status-badge").innerHTML = `<span class="badge badge-fail">❌ RESULT: FAIL</span>`;
                }
            } catch (err) {
                document.getElementById("output-view").innerText = `Error: ${err}`;
            }
        }

        async function executeBatchAll() {
            document.getElementById("output-view").innerText = "⏳ Executing all 15 Chaos Experiments sequentially...";
            try {
                const res = await fetch(`/api/run_all`);
                const data = await res.json();
                document.getElementById("output-view").innerText = data.summary;
                document.getElementById("scorecard-view").innerText = data.scorecard_ascii;
            } catch (err) {
                document.getElementById("output-view").innerText = `Error: ${err}`;
            }
        }

        async function toggleKillSwitch() {
            const res = await fetch(`/api/kill_switch`);
            const data = await res.json();
            alert(data.message);
        }
    </script>
</body>
</html>
"""


class ChaosPlatformHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for standalone Web UI."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/run_lab":
            lab_num = int(params.get("lab", ["1"])[0])
            fault_mode = params.get("fault", ["DEFAULT"])[0]

            exp_module = f"experiments.chapter{lab_num:02d}.experiment"
            try:
                mod = __import__(exp_module, fromlist=["run_experiment"])
                res = mod.run_experiment()

                calc = ResilienceScoreCalculator()
                card = calc.compute(snapshot=global_metrics.get_snapshot())

                response_payload = {
                    "lab": lab_num,
                    "result": res.get("result", "PASS"),
                    "report": res.get("report", ""),
                    "metrics": global_metrics.to_dict(),
                    "scorecard_ascii": card.render_ascii_card()
                }
            except Exception as exc:
                response_payload = {"error": str(exc), "result": "FAIL"}

            self._send_json(response_payload)

        elif path == "/api/run_all":
            reports = []
            for ch in range(1, 16):
                exp_mod = f"experiments.chapter{ch:02d}.experiment"
                mod = __import__(exp_mod, fromlist=["run_experiment"])
                r = mod.run_experiment()
                reports.append(f"Chapter {ch:02d}: {r.get('result', 'PASS')}")

            calc = ResilienceScoreCalculator()
            card = calc.compute(snapshot=global_metrics.get_snapshot())

            self._send_json({
                "summary": "All 15 Chapter Labs Executed Successfully:\n" + "\n".join(reports),
                "scorecard_ascii": card.render_ascii_card()
            })

        elif path == "/api/kill_switch":
            if global_kill_switch.is_engaged:
                global_kill_switch.reset()
                msg = "Emergency Kill Switch has been RESET."
            else:
                global_kill_switch.trip("Engaged via Web UI")
                msg = "🚨 EMERGENCY KILL SWITCH ENGAGED!"
            self._send_json({"engaged": global_kill_switch.is_engaged, "message": msg})

        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress noisy HTTP stdout logs
        pass


def run_server(port: int = 8501):
    server = HTTPServer(("0.0.0.0", port), ChaosPlatformHTTPHandler)
    print(f"🚀 Chaos Engineering Web UI running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
