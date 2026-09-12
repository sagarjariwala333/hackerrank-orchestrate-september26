"""
token_tracker.py - Tracks LLM token usage, call counts, costs, and logs I/O.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

PRICING_PER_1M = {"gemini-3.6-flash": {"input": 0.075, "output": 0.30}}


class TokenTracker:
    def __init__(self):
        self.calls: List[Dict] = []
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def record_call(self, model: str, in_tok: int, out_tok: int, task: str, result: str, raw_in: str = "", raw_out: str = ""):
        """Records token usage and writes raw LLM input/output to evaluation/llm_logs.txt."""
        self.total_input_tokens += in_tok
        self.total_output_tokens += out_tok
        cost = (in_tok / 1e6 * 0.075) + (out_tok / 1e6 * 0.30)
        self.calls.append({"model": model, "in": in_tok, "out": out_tok, "tot": in_tok + out_tok, "cost": cost, "task": task, "res": result})

        log_dir = Path(__file__).resolve().parent / "evaluation"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_entry = (
            f"=== [{datetime.now().isoformat()}] LLM CALL #{len(self.calls)} ({model}) ===\n"
            f"TASK: {task}\nTOKENS: {in_tok} in / {out_tok} out (Cost: ${cost:.6f})\n"
            f"--- RAW INPUT PROMPT ---\n{raw_in}\n--- RAW OUTPUT RESPONSE ---\n{raw_out}\n{'='*60}\n\n"
        )
        with open(log_dir / "llm_logs.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

    def get_total_cost(self) -> float:
        return sum(c["cost"] for c in self.calls)

    def write_usage_report(self, filepath: Path):
        """Writes evaluation/usage_report.md complying with §6.5 hackathon contract."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        n = len(self.calls)
        tot_tok = self.total_input_tokens + self.total_output_tokens
        tot_cost = self.get_total_cost()

        content = (
            "# LLM Token Usage & Cost Analysis Report\n\n"
            "## Summary Statistics\n"
            f"- **Model Providers & Names**: Google Gemini (`gemini-3.6-flash`)\n"
            f"- **Total LLM / VLM API Calls**: {n}\n"
            f"- **Total Input Tokens**: {self.total_input_tokens:,}\n"
            f"- **Total Output Tokens**: {self.total_output_tokens:,}\n"
            f"- **Total Tokens Used**: {tot_tok:,}\n"
            f"- **Estimated Total Cost (USD)**: ${tot_cost:.6f}\n\n"
            "## Detailed Call Log\n"
            "| Call # | Model | Input Tokens | Output Tokens | Total Tokens | Cost (USD) | Task | Result |\n"
            "|---|---|---|---|---|---|---|---|\n"
        )
        for i, c in enumerate(self.calls, 1):
            content += f"| {i} | {c['model']} | {c['in']} | {c['out']} | {c['tot']} | ${c['cost']:.6f} | {c['task']} | {c['res']} |\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


tracker = TokenTracker()
