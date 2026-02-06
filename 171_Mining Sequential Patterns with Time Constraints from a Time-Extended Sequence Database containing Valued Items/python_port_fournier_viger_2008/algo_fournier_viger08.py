#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
171: Full Fournier-Viger 08 with time-extended sequences and valued-item input.
Parses id(value) but mines by item id only. Matches Java MainTestSequentialPatternMining3 (56 patterns).
Self-contained: includes full algo from 170; only loader and main differ.
"""

from __future__ import annotations

import os
import re
import math
import time
from typing import List, Dict, Set, Optional

# --- Copy of 170 structures (minimal set for algo) ---
class ItemSimple:
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

class Itemset:
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
    def setTimestamp(self, ts: int) -> None:
        self.timestamp = int(ts)
    def size(self) -> int:
        return len(self.items)
    def get(self, index: int) -> ItemSimple:
        return self.items[index]
    def cloneItemSet(self) -> "Itemset":
        out = Itemset()
        out.timestamp = self.timestamp
        out.items = list(self.items)
        return out
    def cloneItemSetMinusItems(self, map_sequence_id: Dict[ItemSimple, Set[int]], relative_minsup: float) -> "Itemset":
        out = Itemset()
        out.timestamp = self.timestamp
        for item in self.items:
            sids = map_sequence_id.get(item)
            if sids is not None and len(sids) >= relative_minsup:
                out.addItem(item)
        return out

class Sequence:
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
    def get(self, index: int) -> Itemset:
        return self._itemsets[index]
    def getTimeLength(self) -> int:
        if not self._itemsets:
            return 0
        return self._itemsets[-1].getTimestamp() - self._itemsets[0].getTimestamp()
    def getItemOccurencesTotalCount(self) -> int:
        return sum(it.size() for it in self._itemsets)
    def cloneSequence(self) -> "Sequence":
        out = Sequence(self._id)
        for it in self._itemsets:
            out.addItemset(it.cloneItemSet())
        return out
    def cloneSequenceMinusItems(self, map_sequence_id: Dict[ItemSimple, Set[int]], relative_minsup: float) -> "Sequence":
        out = Sequence(self._id)
        for it in self._itemsets:
            new_it = it.cloneItemSetMinusItems(map_sequence_id, relative_minsup)
            if new_it.size() != 0:
                out.addItemset(new_it)
        return out
    def getRelativeSupportFormated(self, databaseSize: int) -> str:
        if databaseSize <= 0 or self._sequences_id is None:
            return "0"
        support = len(self._sequences_id) / float(databaseSize)
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

class PseudoSequence:
    def __init__(self, time_shift: int, sequence: Sequence, first_itemset: int, first_item: int, last_itemset: Optional[int] = None, last_item: Optional[int] = None):
        self.time_shift = time_shift
        self.sequence = sequence
        self.first_itemset = first_itemset
        self.first_item = first_item
        if last_itemset is not None and last_item is not None:
            self.last_itemset = last_itemset
            self.last_item = last_item
        else:
            self.last_itemset = sequence.size() - 1
            self.last_item = sequence.get(self.last_itemset).size() - 1
    def size(self) -> int:
        n = self.sequence.size() - self.first_itemset - ((self.sequence.size() - 1) - self.last_itemset)
        if n == 1 and self.sequence.get(self.first_itemset).size() == 0:
            return 0
        return n
    def _get_itemset(self, index: int) -> Itemset:
        return self.sequence.get(index + self.first_itemset)
    def getSizeOfItemsetAt(self, index: int) -> int:
        sz = self._get_itemset(index).size()
        if self._is_last_itemset(index):
            sz -= (sz - 1) - self.last_item
        if self._is_first_itemset(index):
            sz -= self.first_item
        return sz
    def _is_first_itemset(self, index: int) -> bool:
        return index == 0
    def _is_last_itemset(self, index: int) -> bool:
        return (index + self.first_itemset) == self.last_itemset
    def isCutAtRight(self, index: int) -> bool:
        if not self._is_last_itemset(index):
            return False
        return self._get_itemset(index).size() - 1 != self.last_item
    def isCutAtLeft(self, index: int) -> bool:
        return index == 0 and self.first_item != 0
    def getItemAtInItemsetAt(self, index_item: int, index_itemset: int) -> ItemSimple:
        if self._is_first_itemset(index_itemset):
            return self._get_itemset(index_itemset).get(index_item + self.first_item)
        return self._get_itemset(index_itemset).get(index_item)
    def getTimeStamp(self, index_itemset: int) -> int:
        return self._get_itemset(index_itemset).getTimestamp() - self.time_shift
    def getAbsoluteTimeStamp(self, index_itemset: int) -> int:
        return self._get_itemset(index_itemset).getTimestamp()
    def getId(self) -> int:
        return self.sequence.getId()
    def indexOf(self, index_itemset: int, id_item: int) -> int:
        for j in range(self.getSizeOfItemsetAt(index_itemset)):
            if self.getItemAtInItemsetAt(j, index_itemset).getId() == id_item:
                return j
        return -1
    def getTimeSucessor(self) -> int:
        pos_last = self.size() - 1
        abs_pos_last = self.size() - 1 + self.first_itemset
        if self.isCutAtRight(pos_last):
            return self.getAbsoluteTimeStamp(pos_last)
        if abs_pos_last < self.sequence.size() - 1:
            return self.sequence.get(abs_pos_last + 1).getTimestamp()
        return 0
    def getTimePredecessor(self) -> int:
        if self.first_itemset == 0:
            return 0
        if self.first_item == 0:
            return self.sequence.get(self.first_itemset - 1).getTimestamp()
        return self.getAbsoluteTimeStamp(0)

class Pair:
    __slots__ = ("timestamp", "postfix", "prefix", "item", "sequences_id")
    def __init__(self, timestamp: int, prefix: bool, postfix: bool, item: ItemSimple):
        self.timestamp = timestamp
        self.prefix = prefix
        self.postfix = postfix
        self.item = item
        self.sequences_id: Set[int] = set()
    def __hash__(self) -> int:
        return hash((self.timestamp, self.prefix, self.postfix, self.item.getId()))
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pair):
            return False
        return self.timestamp == other.timestamp and self.prefix == other.prefix and self.postfix == other.postfix and self.item.getId() == other.item.getId()
    def getTimestamp(self) -> int:
        return self.timestamp
    def isPostfix(self) -> bool:
        return self.postfix
    def getItem(self) -> ItemSimple:
        return self.item
    def getCount(self) -> int:
        return len(self.sequences_id)
    def getSequencesID(self) -> Set[int]:
        return self.sequences_id

class PseudoSequenceDatabase:
    def __init__(self) -> None:
        self._pseudo_sequences: List[PseudoSequence] = []
    def addSequence(self, ps: PseudoSequence) -> None:
        self._pseudo_sequences.append(ps)
    def getPseudoSequences(self) -> List[PseudoSequence]:
        return self._pseudo_sequences

class Sequences:
    def __init__(self, name: str):
        self.name = name
        self.levels: List[List[Sequence]] = [[]]
        self.sequenceCount = 0
    def addSequence(self, sequence: Sequence, k: int) -> None:
        while len(self.levels) <= k:
            self.levels.append([])
        self.levels[k].append(sequence)
        self.sequenceCount += 1
    def toString(self, databaseSize: int) -> str:
        r = []
        r.append(" ----------")
        r.append(self.name)
        r.append(" -------\n")
        for levelCount, level in enumerate(self.levels):
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
        r.append(" -------------------------------- Patterns count : ")
        r.append(str(self.sequenceCount))
        return "".join(r)

# --- 171 database: parse id(value) and store ItemSimple(id) ---
class SequenceDatabase:
    def __init__(self):
        self.sequences: List[Sequence] = []

    def getSequences(self) -> List[Sequence]:
        return self.sequences

    def size(self) -> int:
        return len(self.sequences)

    def loadFile(self, path: str) -> None:
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
                    m = re.fullmatch(r"<\s*(-?\d+)\s*>", tok)
                    if m:
                        current_time = int(m.group(1))
                        continue
                    if tok == "-1":
                        current_itemset = None
                        continue
                    if tok == "-2":
                        if current_seq is not None and current_seq.size() > 0:
                            self.sequences.append(current_seq)
                            seq_id += 1
                        current_seq = None
                        current_itemset = None
                        current_time = 0
                        continue
                    item_id: Optional[int] = None
                    if "(" in tok:
                        left = tok.split("(", 1)[0]
                        try:
                            item_id = int(left)
                        except ValueError:
                            continue
                    else:
                        try:
                            item_id = int(tok)
                        except ValueError:
                            continue
                    if item_id is None:
                        continue
                    if current_seq is None:
                        current_seq = Sequence(seq_id)
                    if current_itemset is None:
                        current_itemset = Itemset(None, current_time)
                        current_seq.addItemset(current_itemset)
                    current_itemset.addItem(ItemSimple(item_id))
            if current_seq is not None and current_seq.size() > 0:
                self.sequences.append(current_seq)

def _item_to_sids_map(database: SequenceDatabase) -> Dict[ItemSimple, Set[int]]:
    map_sid: Dict[ItemSimple, Set[int]] = {}
    already_counted: Set[int] = set()
    last_seq_id: Optional[int] = None
    for seq in database.getSequences():
        if last_seq_id is None or seq.getId() != last_seq_id:
            already_counted.clear()
            last_seq_id = seq.getId()
        for it in seq.getItemsets():
            for item in it.getItems():
                if item.getId() not in already_counted:
                    map_sid.setdefault(item, set()).add(seq.getId())
                    already_counted.add(item.getId())
    return map_sid

class AlgoFournierViger08:
    def __init__(self, minsupp: float, min_interval: float, max_interval: float, min_whole_interval: float, max_whole_interval: float, algo_clustering=None, find_closed_patterns: bool = False, enable_backscan_pruning: bool = False):
        self.minsupp = float(minsupp)
        self.min_interval = float(min_interval)
        self.max_interval = float(max_interval)
        self.min_whole_interval = float(min_whole_interval)
        self.max_whole_interval = float(max_whole_interval)
        self.find_closed_patterns = find_closed_patterns
        self.enable_backscan_pruning = enable_backscan_pruning
        self.patterns: Optional[Sequences] = None
        self.pattern_count = 0
        self.start_time = 0
        self.end_time = 0
        self.minsupp_relative = 1
        self._initial_database: Optional[PseudoSequenceDatabase] = None

    def _is_the_min_and_max_interval_respected(self, time_interval: int) -> bool:
        return self.min_interval <= time_interval <= self.max_interval

    def _is_max_whole_interval_respected(self, sequence: Sequence) -> bool:
        if not sequence.getItemsets():
            return True
        return sequence.get(sequence.size() - 1).getTimestamp() <= self.max_whole_interval

    def _is_min_whole_interval_respected(self, sequence: Sequence) -> bool:
        if not sequence.getItemsets():
            return False
        return sequence.get(sequence.size() - 1).getTimestamp() >= self.min_whole_interval

    def _append_item_to_sequence(self, prefix: Sequence, item: ItemSimple, timestamp: int) -> Sequence:
        new_prefix = prefix.cloneSequence()
        decal = new_prefix.get(new_prefix.size() - 1).getTimestamp()
        new_prefix.addItemset(Itemset(item, timestamp + decal))
        return new_prefix

    def _append_item_to_prefix_of_sequence(self, prefix: Sequence, item: ItemSimple) -> Sequence:
        new_prefix = prefix.cloneSequence()
        last_it = new_prefix.get(new_prefix.size() - 1)
        last_it.addItem(item)
        return new_prefix

    def _build_projected_database(self, item: ItemSimple, contexte: PseudoSequenceDatabase, in_suffix: bool, timestamp: int) -> List[PseudoSequenceDatabase]:
        out = PseudoSequenceDatabase()
        for seq in contexte.getPseudoSequences():
            for i in range(seq.size()):
                if timestamp != -1 and timestamp != seq.getTimeStamp(i):
                    continue
                idx = seq.indexOf(i, item.getId())
                if idx == -1 or seq.isCutAtLeft(i) != in_suffix:
                    continue
                base_seq = seq.sequence
                if idx != seq.getSizeOfItemsetAt(i) - 1:
                    base_first = seq.first_itemset + i
                    base_first_item = (seq.first_item + idx + 1) if i == 0 else (idx + 1)
                    new_ps = PseudoSequence(seq.getAbsoluteTimeStamp(i), base_seq, base_first, base_first_item)
                    if new_ps.size() > 0:
                        out.addSequence(new_ps)
                elif i != seq.size() - 1:
                    base_first = seq.first_itemset + i + 1
                    base_first_item = 0
                    new_ps = PseudoSequence(seq.getAbsoluteTimeStamp(i), base_seq, base_first, base_first_item)
                    if new_ps.size() > 0:
                        out.addSequence(new_ps)
        return [out]

    def _find_all_frequent_pairs_satisfying_c1_c2(self, prefix: Sequence, database: List[PseudoSequence]) -> Set[Pair]:
        map_pairs: Dict[Pair, Pair] = {}
        already_counted: Set[Pair] = set()
        last_seq: Optional[PseudoSequence] = None
        for seq in database:
            if last_seq is None or seq.getId() != last_seq.getId():
                already_counted.clear()
                last_seq = seq
            for i in range(seq.size()):
                for j in range(seq.getSizeOfItemsetAt(i)):
                    item = seq.getItemAtInItemsetAt(j, i)
                    ts = seq.getTimeStamp(i)
                    if self._is_the_min_and_max_interval_respected(ts) or seq.isCutAtLeft(i):
                        pair = Pair(ts, seq.isCutAtRight(i), seq.isCutAtLeft(i), item)
                        if pair not in already_counted:
                            existing = map_pairs.get(pair)
                            if existing is None:
                                map_pairs[pair] = pair
                                existing = pair
                            else:
                                pair = existing
                            already_counted.add(pair)
                            pair.getSequencesID().add(seq.getId())
        return set(map_pairs.keys())

    def _save_pattern(self, prefix: Sequence) -> None:
        self.pattern_count += 1
        if self.patterns is not None:
            self.patterns.addSequence(prefix, prefix.size())

    def _projection(self, prefix: Sequence, k: int, database: PseudoSequenceDatabase) -> int:
        max_support = 0
        pairs = self._find_all_frequent_pairs_satisfying_c1_c2(prefix, database.getPseudoSequences())
        for pair in pairs:
            if pair.getCount() < self.minsupp_relative:
                continue
            if pair.isPostfix():
                new_prefix = self._append_item_to_prefix_of_sequence(prefix, pair.getItem())
            else:
                new_prefix = self._append_item_to_sequence(prefix, pair.getItem(), pair.getTimestamp())
            if self._is_max_whole_interval_respected(new_prefix):
                succ = self._projection_pair(new_prefix, pair, prefix, database, k)
                if succ > max_support:
                    max_support = succ
        return max_support

    def _projection_pair(self, new_prefix: Sequence, pair: Pair, old_prefix: Sequence, database: PseudoSequenceDatabase, k: int) -> int:
        max_support = 0
        projected_list = self._build_projected_database(pair.getItem(), database, pair.isPostfix(), pair.getTimestamp())
        for proj_db in projected_list:
            prefix = new_prefix.cloneSequence()
            prefix.setSequencesID(pair.getSequencesID())
            max_succ = self._projection(prefix, k + 1, proj_db)
            if self._is_min_whole_interval_respected(prefix):
                no_forward = not self.find_closed_patterns or (prefix.getAbsoluteSupport() != max_succ)
                no_backward = not self.find_closed_patterns
                if no_forward and no_backward:
                    self._save_pattern(prefix)
                if prefix.getAbsoluteSupport() > max_support:
                    max_support = prefix.getAbsoluteSupport()
        return max_support

    def runAlgorithm(self, database: SequenceDatabase) -> Sequences:
        self.patterns = Sequences("FREQUENT SEQUENCES WITH TIME + CLUSTERING")
        self.pattern_count = 0
        self.minsupp_relative = max(1, int(math.ceil(self.minsupp * database.size())))
        self.start_time = int(time.time() * 1000)
        map_sid = _item_to_sids_map(database)
        initial_db = PseudoSequenceDatabase()
        for seq in database.getSequences():
            opt_seq = seq.cloneSequenceMinusItems(map_sid, self.minsupp_relative)
            if opt_seq.size() != 0:
                initial_db.addSequence(PseudoSequence(0, opt_seq, 0, 0))
        self._initial_database = initial_db
        for item, sids in map_sid.items():
            if len(sids) < self.minsupp_relative:
                continue
            projected_list = self._build_projected_database(item, initial_db, False, -1)
            for proj_db in projected_list:
                prefix = Sequence(0)
                prefix.addItemset(Itemset(item, 0))
                prefix.setSequencesID(sids)
                self._projection(prefix, 2, proj_db)
                if self._is_min_whole_interval_respected(prefix):
                    no_forward = not self.find_closed_patterns
                    no_backward = not self.find_closed_patterns
                    if no_forward and no_backward:
                        self._save_pattern(prefix)
        self.end_time = int(time.time() * 1000)
        return self.patterns

    def printResult(self, database_size: int) -> None:
        r = []
        r.append("=============  Algorithm - STATISTICS =============\n Total time ~ ")
        r.append(str(self.end_time - self.start_time))
        r.append(" ms\n")
        r.append(" Frequent sequences count : ")
        r.append(str(self.pattern_count))
        r.append("\n")
        r.append(self.patterns.toString(database_size) if self.patterns else "")
        r.append("===================================================\n")
        print("".join(r))

def main() -> None:
    base = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base, "contextSequencesTimeExtended_ValuedItems.txt")
    db = SequenceDatabase()
    db.loadFile(data_file)
    algo = AlgoFournierViger08(0.50, 0, float("inf"), 0, float("inf"), None, False, False)
    algo.runAlgorithm(db)
    algo.printResult(db.size())

if __name__ == "__main__":
    main()
