import json
import os
from datetime import datetime

SESSION_FILE = "memory/session.json"
MEMORY_BANK_FILE = "memory/memory_bank.json"

# Ensure folders exist
os.makedirs("memory", exist_ok=True)


class MemoryManager:
    """Handles persistent session logs + long-term memory."""

    def __init__(self):
        # Load session OR default structure
        self.session = self._load(SESSION_FILE)

        # Ensure required keys exist
        if self.session is None or not isinstance(self.session, dict):
            self.session = {}

        if "runs" not in self.session:
            self.session["runs"] = []

        # Save it immediately to guarantee structure on disk
        self._save(SESSION_FILE, self.session)

    # ---------- FILE HELPERS ----------
    def _load(self, path):
        if not os.path.exists(path):
            return None
        try:
            return json.load(open(path, "r"))
        except:
            return None

    def _save(self, path, data):
        json.dump(data, open(path, "w"), indent=2)

    # ---------- SESSION MEMORY ----------
    def add_run(self, run_dict):
        """
        Stores:
        - full result of that run (extracted, market, financials, memo, deck path)
        """

        run_entry = {
            "timestamp": str(datetime.now()),
            "data": run_dict
        }

        # GUARANTEE "runs" exists
        if "runs" not in self.session:
            self.session["runs"] = []

        self.session["runs"].append(run_entry)
        self._save(SESSION_FILE, self.session)

    def get_runs(self):
        """Returns list of all past executions."""
        return self.session.get("runs", [])

    def get_run(self, index: int):
        runs = self.get_runs()
        if 0 <= index < len(runs):
            return runs[index]
        return None

    # ---------- MEMORY BANK ----------
    def append_to_memory_bank(self, summary: dict):
        """
        Writes a compact summary into long-term memory.
        """

        bank = self._load(MEMORY_BANK_FILE)

        # ensure proper list
        if bank is None or not isinstance(bank, list):
            bank = []

        bank.append(summary)
        self._save(MEMORY_BANK_FILE, bank)

    def get_memory_bank(self):
        """Returns all long-term memory entries."""
        bank = self._load(MEMORY_BANK_FILE)
        return bank if isinstance(bank, list) else []


# Global instance
memory = MemoryManager()
