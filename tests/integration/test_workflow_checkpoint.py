import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Integration tests for durable checkpointing workflow."""
import unittest
from graphs.workflow_graph import DurableWorkflowGraph
from memory.long_term import CheckpointStore


class TestWorkflowCheckpoint(unittest.TestCase):

    def test_durable_workflow_full_pass(self):
        store = CheckpointStore()
        graph = DurableWorkflowGraph(checkpoint_store=store)
        res = graph.run("thread_test_1", "Test Topic")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(len(res["completed_steps"]), 4)


if __name__ == "__main__":
    unittest.main()
