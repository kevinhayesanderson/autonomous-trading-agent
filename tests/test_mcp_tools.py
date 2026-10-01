"""
Unit Test Suite for Institutional MCP 2.x Server Tools & Fiduciary Annotations
Verifies all 9 Model Context Protocol (MCP) tools for M8ven Trust Index conformance:
1. trading_get_portfolio_status
2. trading_run_screener
3. trading_deliberate_ticker
4. trading_preview_rebalance
5. trading_execute_rebalance
6. trading_drain_wallet
7. trading_get_memory_state
8. trading_run_system_test
9. trading_run_agent_evals

Validates:
- Explicit presence and correctness of all 4 security & idempotency hints:
  readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
- Complete execution of tool handlers and tool functions.
- Official FastMCP / MCP 2.x SDK tool registration.
"""

import os
import sys
import json
import asyncio
import unittest
from unittest.mock import patch, MagicMock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import server.mcp_server as mcp_mod
from server.mcp_server import (
    TOOL_METADATA,
    make_annotations,
    handle_get_portfolio_status,
    handle_run_screener,
    handle_deliberate_ticker,
    handle_preview_rebalance,
    handle_execute_rebalance,
    handle_drain_wallet,
    handle_get_memory_state,
    handle_run_system_test,
    handle_run_agent_evals,
    trading_get_portfolio_status,
    trading_run_screener,
    trading_deliberate_ticker,
    trading_preview_rebalance,
    trading_execute_rebalance,
    trading_drain_wallet,
    trading_get_memory_state,
    trading_run_system_test,
    trading_run_agent_evals,
    USE_OFFICIAL_MCP,
    mcp_app,
)


class TestMCPToolsCoverage(unittest.TestCase):
    """
    Exhaustive test coverage verifying all 9 MCP tools by name,
    validating security hints, schemas, and execution handlers.
    """

    EXPECTED_TOOL_NAMES = [
        "trading_get_portfolio_status",
        "trading_run_screener",
        "trading_deliberate_ticker",
        "trading_preview_rebalance",
        "trading_execute_rebalance",
        "trading_drain_wallet",
        "trading_get_memory_state",
        "trading_run_system_test",
        "trading_run_agent_evals",
    ]

    def test_all_nine_tools_metadata_and_hints_conformance(self):
        """Verify that exactly 9 tools are declared with all 4 hints as strict booleans."""
        self.assertEqual(len(TOOL_METADATA), 9, "Server must expose exactly 9 MCP tools")
        
        for name in self.EXPECTED_TOOL_NAMES:
            self.assertIn(name, TOOL_METADATA, f"Tool {name} missing from TOOL_METADATA")
            meta = TOOL_METADATA[name]
            
            # Check required string fields
            self.assertTrue(bool(meta.get("title")), f"Tool {name} missing title")
            self.assertTrue(bool(meta.get("description")), f"Tool {name} missing description")
            
            # Check all four hints are non-null booleans
            self.assertIn("readOnlyHint", meta, f"Tool {name} missing readOnlyHint")
            self.assertIn("destructiveHint", meta, f"Tool {name} missing destructiveHint")
            self.assertIn("idempotentHint", meta, f"Tool {name} missing idempotentHint")
            self.assertIn("openWorldHint", meta, f"Tool {name} missing openWorldHint")
            
            self.assertIsInstance(meta["readOnlyHint"], bool, f"Tool {name} readOnlyHint must be bool")
            self.assertIsInstance(meta["destructiveHint"], bool, f"Tool {name} destructiveHint must be bool")
            self.assertIsInstance(meta["idempotentHint"], bool, f"Tool {name} idempotentHint must be bool")
            self.assertIsInstance(meta["openWorldHint"], bool, f"Tool {name} openWorldHint must be bool")
            
            # Mutual exclusion: read-only tools cannot be destructive, and vice-versa
            self.assertNotEqual(
                meta["readOnlyHint"],
                meta["destructiveHint"],
                f"Tool {name} cannot have identical readOnlyHint and destructiveHint"
            )
            
            # Test make_annotations helper
            ann = make_annotations(name)
            self.assertIsNotNone(ann)

    @patch("server.mcp_server.get_tickertape_token", return_value="mock_token_123")
    @patch("server.mcp_server.call_tickertape_mcp")
    @patch("server.mcp_server.audit_lrs_settlement", return_value=[])
    @patch("server.mcp_server.audit_portfolio_health", return_value=([], [{"ticker": "NVDA", "invested": 100.0, "current": 120.0, "pnl_pct": 20.0}]))
    def test_trading_get_portfolio_status(self, mock_health, mock_lrs, mock_mcp, mock_auth):
        """Test tool: trading_get_portfolio_status"""
        def mock_call_impl(token, tool_name, *args, **kwargs):
            if "holding" in tool_name:
                return {"securities": [{"ticker": "NVDA"}]}
            return {"balance": {"availableToInvest": 250.0, "withdrawableBalance": 200.0}}
        mock_mcp.side_effect = mock_call_impl
        
        # Test handler
        result = handle_get_portfolio_status()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["cash_available"], 250.0)
        self.assertEqual(result["holdings_count"], 1)
        self.assertEqual(result["holdings"][0]["ticker"], "NVDA")
        
        # Test tool wrapper returning JSON
        raw_json = trading_get_portfolio_status()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints
        meta = TOOL_METADATA["trading_get_portfolio_status"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertFalse(meta["openWorldHint"])

    @patch("server.mcp_server.get_tickertape_token", return_value="mock_token_123")
    @patch("server.mcp_server.load_factor_weights", return_value={"weights": {"composite_score": 1.0}})
    @patch("trading_agent.core.screener.run_quantitative_screener")
    def test_trading_run_screener(self, mock_screener, mock_weights, mock_auth):
        """Test tool: trading_run_screener"""
        mock_screener.return_value = [
            {"ticker": "NVDA", "composite_score": 9.4, "beta": 1.72, "net_margin": 55.0},
            {"ticker": "ASML", "composite_score": 8.9, "beta": 1.55, "net_margin": 28.0}
        ]
        
        # Test handler
        result = handle_run_screener(count=2)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["candidates_count"], 2)
        self.assertEqual(result["candidates"][0]["ticker"], "NVDA")
        
        # Test tool wrapper returning JSON
        raw_json = trading_run_screener(count=2)
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["candidates_count"], 2)
        
        # Test security hints
        meta = TOOL_METADATA["trading_run_screener"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertTrue(meta["openWorldHint"])

    @patch("server.mcp_server.get_tickertape_token", return_value="mock_token_123")
    @patch("server.mcp_server.deliberate_ticker")
    def test_trading_deliberate_ticker(self, mock_delib, mock_auth):
        """Test tool: trading_deliberate_ticker"""
        mock_obj = MagicMock()
        mock_obj.model_dump.return_value = {
            "ticker": "NVDA",
            "recommendation": "BUY",
            "confidence_score": 0.92,
            "buy_votes": 3,
            "veto_votes": 0
        }
        mock_delib.return_value = mock_obj
        
        # Test handler
        result = handle_deliberate_ticker("NVDA")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deliberation"]["ticker"], "NVDA")
        self.assertEqual(result["deliberation"]["recommendation"], "BUY")
        
        # Test tool wrapper returning JSON
        raw_json = trading_deliberate_ticker("NVDA")
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["deliberation"]["recommendation"], "BUY")
        
        # Test security hints
        meta = TOOL_METADATA["trading_deliberate_ticker"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertTrue(meta["openWorldHint"])

    @patch("server.mcp_server.run_pipeline")
    def test_trading_preview_rebalance(self, mock_pipeline):
        """Test tool: trading_preview_rebalance"""
        mock_pipeline.return_value = {"rebalance_plan": {"actions": []}, "mode": "live"}
        
        # Test handler
        result = handle_preview_rebalance(budget="auto", mode="live", plan="dynamic", ignore_in_flight=False)
        self.assertEqual(result["status"], "success")
        self.assertIn("preview_result", result)
        
        # Test tool wrapper returning JSON
        raw_json = trading_preview_rebalance()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints
        meta = TOOL_METADATA["trading_preview_rebalance"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertTrue(meta["openWorldHint"])

    @patch("server.mcp_server.run_pipeline")
    def test_trading_execute_rebalance(self, mock_pipeline):
        """Test tool: trading_execute_rebalance"""
        mock_pipeline.return_value = {"executed_trades": 2, "zero_limbo_status": "clean"}
        
        # Test handler
        result = handle_execute_rebalance(budget="auto", mode="live", plan="dynamic", ignore_in_flight=False)
        self.assertEqual(result["status"], "success")
        self.assertIn("execution_result", result)
        
        # Test tool wrapper returning JSON
        raw_json = trading_execute_rebalance()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints (MUST be destructive and non-idempotent)
        meta = TOOL_METADATA["trading_execute_rebalance"]
        self.assertFalse(meta["readOnlyHint"])
        self.assertTrue(meta["destructiveHint"])
        self.assertFalse(meta["idempotentHint"])
        self.assertTrue(meta["openWorldHint"])

    @patch("server.mcp_server.drain_wallet_to_asset")
    def test_trading_drain_wallet(self, mock_drain):
        """Test tool: trading_drain_wallet"""
        mock_drain.return_value = {"ticker": "ASML", "drained_usd": 45.0, "status": "executed"}
        
        # Test handler
        result = handle_drain_wallet(ticker="ASML")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["drain_result"]["ticker"], "ASML")
        
        # Test tool wrapper returning JSON
        raw_json = trading_drain_wallet(ticker="ASML")
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints (MUST be destructive and non-idempotent)
        meta = TOOL_METADATA["trading_drain_wallet"]
        self.assertFalse(meta["readOnlyHint"])
        self.assertTrue(meta["destructiveHint"])
        self.assertFalse(meta["idempotentHint"])
        self.assertTrue(meta["openWorldHint"])

    def test_trading_get_memory_state(self):
        """Test tool: trading_get_memory_state"""
        # Test handler directly
        result = handle_get_memory_state()
        self.assertEqual(result["status"], "success")
        self.assertIn("factor_weights", result)
        self.assertIn("historical_trades_count", result)
        self.assertEqual(result["tenure_mandate_days"], 60)
        
        # Test tool wrapper returning JSON
        raw_json = trading_get_memory_state()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        self.assertIn("factor_weights", parsed)
        
        # Test security hints
        meta = TOOL_METADATA["trading_get_memory_state"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertFalse(meta["openWorldHint"])

    @patch("subprocess.run")
    def test_trading_run_system_test(self, mock_sub):
        """Test tool: trading_run_system_test"""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "ALL 7 TESTS PASSED"
        mock_res.stderr = ""
        mock_sub.return_value = mock_res
        
        # Test handler
        result = handle_run_system_test()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["return_code"], 0)
        self.assertIn("ALL 7 TESTS PASSED", result["stdout"])
        
        # Test tool wrapper returning JSON
        raw_json = trading_run_system_test()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints
        meta = TOOL_METADATA["trading_run_system_test"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertFalse(meta["openWorldHint"])

    @patch("subprocess.run")
    def test_trading_run_agent_evals(self, mock_sub):
        """Test tool: trading_run_agent_evals"""
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "ALL 7 AGENTIC BENCHMARKS PASSED"
        mock_res.stderr = ""
        mock_sub.return_value = mock_res
        
        # Test handler
        result = handle_run_agent_evals()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["return_code"], 0)
        self.assertIn("ALL 7 AGENTIC BENCHMARKS PASSED", result["stdout"])
        
        # Test tool wrapper returning JSON
        raw_json = trading_run_agent_evals()
        parsed = json.loads(raw_json)
        self.assertEqual(parsed["status"], "success")
        
        # Test security hints
        meta = TOOL_METADATA["trading_run_agent_evals"]
        self.assertTrue(meta["readOnlyHint"])
        self.assertFalse(meta["destructiveHint"])
        self.assertTrue(meta["idempotentHint"])
        self.assertFalse(meta["openWorldHint"])

    def test_official_mcp_server_registration(self):
        """Verify that all 9 tools are properly registered on the FastMCP MCPServer instance."""
        if not USE_OFFICIAL_MCP or mcp_app is None:
            self.skipTest("Official FastMCP SDK is not available in environment")
            
        tools = asyncio.run(mcp_app.list_tools())
        registered_names = {t.name for t in tools}
        for name in self.EXPECTED_TOOL_NAMES:
            self.assertIn(name, registered_names, f"Tool {name} not registered in MCPServer")
            
        for tool in tools:
            self.assertIsNotNone(tool.annotations, f"Tool {tool.name} missing annotations object")
            ann = tool.annotations
            self.assertIsInstance(ann.read_only_hint, bool)
            self.assertIsInstance(ann.destructive_hint, bool)
            self.assertIsInstance(ann.idempotent_hint, bool)
            self.assertIsInstance(ann.open_world_hint, bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
