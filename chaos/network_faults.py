"""
Chaos Fault Injection: Network & Distributed RPC / MCP Layer.

Simulates network degradation between agents and tools, Model Context Protocol (MCP)
servers, vector stores, and external microservices.
"""

import time
from typing import Optional, Dict, Any
from chaos.base import BaseFaultInjector, ChaosConfig


class NetworkConnectionException(ConnectionError):
    """Raised when an RPC/HTTP connection is reset or dropped."""
    pass


class MCPServerUnavailableException(ConnectionRefusedError):
    """Raised when an MCP tool provider server becomes suddenly unreachable."""
    pass


class NetworkFaultInjector(BaseFaultInjector):
    """Fault injector simulating distributed transport failure modes."""

    def intercept(self, endpoint: str) -> None:
        """
        Intercept network communication to an external endpoint or MCP server.
        """
        if not self.config.should_inject("network"):
            return

        fault = self.config.network_fault

        if fault == "LATENCY":
            self.record_injection(f"network:{endpoint}", "LATENCY_JITTER", {"delay_sec": self.config.latency_delay_sec})
            time.sleep(self.config.latency_delay_sec)

        elif fault == "CONNECTION_RESET":
            self.record_injection(f"network:{endpoint}", "ECONNRESET", {})
            raise NetworkConnectionException(f"Connection reset by peer at endpoint '{endpoint}'")

        elif fault == "REQUEST_LOSS":
            self.record_injection(f"network:{endpoint}", "PACKET_DROP", {})
            raise TimeoutError(f"Request dropped in flight to '{endpoint}'")

        elif fault == "SERVICE_UNAVAILABLE":
            self.record_injection(f"network:{endpoint}", "MCP_SERVER_DOWN", {})
            raise MCPServerUnavailableException(f"MCP Server at '{endpoint}' is unreachable (503 Service Unavailable)")
