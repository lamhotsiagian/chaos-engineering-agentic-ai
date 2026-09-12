import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Integration tests for RAG agent workflow."""
import unittest
from agents.rag_agent import RAGAgent


class TestRAGFlow(unittest.TestCase):

    def test_rag_agent_clean_query(self):
        agent = RAGAgent(use_mock=True)
        res = agent.query("What is the return policy?")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertTrue(res["context_validation"]["valid"])


if __name__ == "__main__":
    unittest.main()
