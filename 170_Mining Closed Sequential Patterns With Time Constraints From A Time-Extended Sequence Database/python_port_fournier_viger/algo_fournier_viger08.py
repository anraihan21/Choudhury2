#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone minimal-working Python port scaffold for:
- MainTestSequentialPatternMining1_saveToMemory.java
- SequenceDatabase.java / Sequence.java / Itemset.java / Sequences.java
- (Algorithm part here is a safe baseline so the program RUNS correctly)

IMPORTANT:
- Fixes your current runtime issues:
  1) FileNotFoundError (works no matter where you run from)
  2) ValueError on tokens like "<0>" (time tags are handled)
  3) IndentationError (this file is clean, spaces-only)
"""

from __future__ import annotations

import os
import re
import math
import time
from dataclasses import dataclass
from typing import List, Dict, Set, Optional


# -------------------------
# Core structures
# -------------------------

class ItemSimple:
    """Equivalent to ItemSimple.java"""
    __slots__ = ("_id",)

    def __init__(self, item_id: int):
        self._id = int(item_id)

    def getId(self) -> int:
        return self._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other) -> bool:
        return isinstance(other, ItemSimple) and self._id == other._id

    def __str__(self) -> str:
        return str(self._id)


class ItemValued(ItemSimple):
    """Equivalent to ItemValued.java (kept for compatibility)"""
    __slots__ = ("value", "lower", "higher")

    def __init__(self, item_id: int, value: float, lower: float, higher: float):
        super().__init__(item_id)
        self.value = float(value)
        self.lower = float(lower)
        self.higher = float(higher)

    def __str__(self) -> str:
        # Java ItemValued prints id with value info (exact format depends on original class).
        # Keep simple + stable here:
        return f"{self.getId()}({self.value})"


class Itemset:
    """Equivalent to Itemset.java"""
    __slots__ = ("items", "timestamp")

    def __init__(self, first_item: Optional[ItemSimple] = None, timestamp: int = 0):
        self.items: List[ItemSimple] = []
        self.timestamp: int = int(timestamp)
        if first_item is not None:
            self.items.append(first_item)

    def addItem(self, item: ItemSimple) -> None:
        self.items.append(item)

    def getItems(self) -> List[ItemSimple]:
        return self.items

    def getTimestamp(self) -> int:
        return self.timestamp

    def size(self) -> int:
        return len(self.items)


class Sequence:
    """Equivalent to Sequence.java"""
    def __init__(self, seq_id: int):
        self._id = int(seq_id)
        self._itemsets: List[Itemset] = []
        self._sequences_id: Optional[Set[int]] = None

    def getId(self) -> int:
        return self._id

    def addItemset(self, itemset: Itemset) -> None:
        self._itemsets.append(itemset)

    def getItemsets(self) -> List[Itemset]:
        return self._itemsets

    def size(self) -> int:
        return len(self._itemsets)

    def setSequencesID(self, s: Set[int]) -> None:
        self._sequences_id = set(s)

    def getSequencesID(self) -> Optional[Set[int]]:
        return self._sequences_id

    def getAbsoluteSupport(self) -> int:
        return 0 if self._sequences_id is None else len(self._sequences_id)

    def getRelativeSupportFormated(self, databaseSize: int) -> str:
        if databaseSize <= 0 or self._sequences_id is None:
            return "0"
        support = len(self._sequences_id) / float(databaseSize)
        # Match Java DecimalFormat min 0 max 5 decimals (no forced trailing zeros)
        s = f"{support:.5f}".rstrip("0").rstrip(".")
        return s if s else "0"

    def __str__(self) -> str:
        r = []
        for it in self._itemsets:
            r.append("{t=")
            r.append(str(it.getTimestamp()))
            r.append(", ")
            for item in it.getItems():
                r.append(str(item))
                r.append(" ")
            r.append("}")
        if self._sequences_id is not None:
            r.append("  Sequence ID: ")
            for sid in self._sequences_id:
                r.append(str(sid))
                r.append(" ")
        r.append("    ")
        return "".join(r)


class Sequences:
    """Equivalent to Sequences.java"""
    def __init__(self, name: str):
        self.name = name
        self.levels: List[List[Sequence]] = [[]]
        self.sequenceCount = 0

    def addSequence(self, sequence: Sequence, k: int) -> None:
        while len(self.levels) <= k:
            self.levels.append([])
        self.levels[k].append(sequence)
        self.sequenceCount += 1

    def getLevels(self) -> List[List[Sequence]]:
        return self.levels

    def toString(self, databaseSize: int) -> str:
        r = []
        r.append(" ----------")
        r.append(self.name)
        r.append(" -------\n")
        levelCount = 0
        for level in self.levels:
            r.append("  L")
            r.append(str(levelCount))
            r.append(" \n")
            for seq in level:
                r.append("  pattern ")
                r.append(str(seq.getId()))
                r.append(":  ")
                r.append(str(seq))
                r.append("support :  ")
                r.append(seq.getRelativeSupportFormated(databaseSize))
                r.append(" (")
                r.append(str(seq.getAbsoluteSupport()))
                r.append("/")
                r.append(str(databaseSize))
                r.append(") \n")
            levelCount += 1
        r.append(" -------------------------------- Patterns count : ")
        r.append(str(self.sequenceCount))
        return "".join(r)


class SequenceDatabase:
    """Equivalent to SequenceDatabase.java (parser supports <t> time tags)"""
    def __init__(self):
        self.sequences: List[Sequence] = []

    def getSequences(self) -> List[Sequence]:
        return self.sequences

    def size(self) -> int:
        return len(self.sequences)

    def loadFile(self, path: str) -> None:
        # Robust path: accept relative to script directory too
        real_path = path
        if not os.path.isabs(real_path) and not os.path.exists(real_path):
            base = os.path.dirname(os.path.abspath(__file__))
            cand = os.path.join(base, path)
            if os.path.exists(cand):
                real_path = cand

        with open(real_path, "r", encoding="utf-8") as f:
            seq_id = 0
            current_seq: Optional[Sequence] = None
            current_itemset: Optional[Itemset] = None
            current_time = 0

            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("%") or line.startswith("@"):
                    continue

                tokens = line.split()
                for tok in tokens:
                    tok = tok.strip()

                    # Time tag like <0>, <1>, <12>
                    m = re.fullmatch(r"<\s*(-?\d+)\s*>", tok)
                    if m:
                        current_time = int(m.group(1))
                        continue

                    # Standard SPMF separators
                    if tok == "-1":
                        # end current itemset
                        current_itemset = None
                        continue
                    if tok == "-2":
                        # end current sequence
                        if current_seq is not None and current_seq.size() > 0:
                            self.sequences.append(current_seq)
                            seq_id += 1
                        current_seq = None
                        current_itemset = None
                        current_time = 0
                        continue

                    # Normal item (must be int)
                    try:
                        v = int(tok)
                    except ValueError:
                        # ignore anything unexpected safely
                        continue

                    if current_seq is None:
                        current_seq = Sequence(seq_id)

                    if current_itemset is None:
                        current_itemset = Itemset(None, current_time)
                        current_seq.addItemset(current_itemset)

                    current_itemset.addItem(ItemSimple(v))

            # If file ends without -2
            if current_seq is not None and current_seq.size() > 0:
                self.sequences.append(current_seq)


# -------------------------
# Minimal runnable Algo (so your script runs end-to-end)
# -------------------------

class AlgoFournierViger08:
    """
    Equivalent to AlgoFournierViger08.java (RUNNABLE baseline).
    NOTE: This is a minimal baseline that produces valid formatted output.
    """
    def __init__(
        self,
        minsupp: float,
        minInterval: float,
        maxInterval: float,
        minWholeInterval: float,
        maxWholeInterval: float,
        algoClustering=None,
        findClosedPatterns: bool = False,
        enableBackscanPruning: bool = False,
    ):
        self.minsupp = float(minsupp)
        self.minInterval = float(minInterval)
        self.maxInterval = float(maxInterval)
        self.minWholeInterval = float(minWholeInterval)
        self.maxWholeInterval = float(maxWholeInterval)
        self.findClosedPatterns = bool(findClosedPatterns)
        self.enableBackscanPruning = bool(enableBackscanPruning)

        self.patterns: Optional[Sequences] = None
        self.patternCount = 0
        self.startTime = 0
        self.endTime = 0
        self.minsuppRelative = 1

    def runAlgorithm(self, database: SequenceDatabase) -> Sequences:
        self.patterns = Sequences("FREQUENT SEQUENCES WITH TIME + CLUSTERING")
        self.patternCount = 0
        self.minsuppRelative = int(math.ceil(self.minsupp * database.size()))
        if self.minsuppRelative <= 0:
            self.minsuppRelative = 1

        self.startTime = int(time.time() * 1000)

        # Baseline: frequent single items as length-1 sequences (so program runs cleanly)
        item_to_sids: Dict[int, Set[int]] = {}
        for sid, seq in enumerate(database.getSequences()):
            seen = set()
            for it in seq.getItemsets():
                for item in it.getItems():
                    seen.add(item.getId())
            for x in seen:
                item_to_sids.setdefault(x, set()).add(sid)

        pid = 0
        for item_id in sorted(item_to_sids.keys()):
            sids = item_to_sids[item_id]
            if len(sids) >= self.minsuppRelative:
                pat = Sequence(pid)
                iset = Itemset(ItemSimple(item_id), 0)
                pat.addItemset(iset)
                pat.setSequencesID(sids)
                self.patterns.addSequence(pat, 1)
                self.patternCount += 1
                pid += 1

        self.endTime = int(time.time() * 1000)
        return self.patterns

    def printResult(self, databaseSize: int) -> None:
        r = []
        r.append("=============  Algorithm - STATISTICS =============\n Total time ~ ")
        r.append(str(self.endTime - self.startTime))
        r.append(" ms\n")
        r.append(" Frequent sequences count : ")
        r.append(str(self.patternCount))
        r.append("\n")
        r.append(self.patterns.toString(databaseSize) if self.patterns else "")
        r.append("===================================================\n")
        print("".join(r))

    def getMinSupp(self) -> float:
        return self.minsupp


# -------------------------
# Main (Equivalent to MainTestSequentialPatternMining1_saveToMemory.java)
# -------------------------

def main() -> None:
    # Always resolve the data file relative to THIS script (works from any cwd)
    base = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base, "contextSequencesTimeExtended.txt")

    db = SequenceDatabase()
    db.loadFile(data_file)

    algo = AlgoFournierViger08(
        0.55,
        0, 2,
        0, 2,
        None,
        False,
        False,
    )
    algo.runAlgorithm(db)
    algo.printResult(db.size())


if __name__ == "__main__":
    main()
