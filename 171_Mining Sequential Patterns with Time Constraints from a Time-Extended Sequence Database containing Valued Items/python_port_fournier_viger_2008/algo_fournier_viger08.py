#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
from collections import defaultdict

# =========================================================
# MemoryLogger
# =========================================================
class MemoryLogger:
    _instance = None

    def __init__(self):
        self.maxMemory = 0

    @staticmethod
    def getInstance():
        if MemoryLogger._instance is None:
            MemoryLogger._instance = MemoryLogger()
        return MemoryLogger._instance

    def reset(self):
        self.maxMemory = 0

    def checkMemory(self):
        pass


# =========================================================
# Item classes
# =========================================================
class ItemSimple:
    def __init__(self, item):
        self.item = item

    def __eq__(self, other):
        return isinstance(other, ItemSimple) and self.item == other.item

    def __hash__(self):
        return hash(self.item)

    def __str__(self):
        return str(self.item)


class ItemValued(ItemSimple):
    def __init__(self, item, value):
        super().__init__(item)
        self.value = value

    def __str__(self):
        return f"{self.item}({self.value})"


# =========================================================
# Itemset
# =========================================================
class Itemset:
    def __init__(self):
        self.items = []

    def addItem(self, item):
        self.items.append(item)

    def __str__(self):
        return " ".join(str(i) for i in self.items)


# =========================================================
# Sequence
# =========================================================
class Sequence:
    def __init__(self, sid):
        self.sid = sid
        self.itemsets = []
        self.timestamps = []
        self.support = 0

    def addItemset(self, itemset, timestamp):
        self.itemsets.append(itemset)
        self.timestamps.append(timestamp)

    def size(self):
        return len(self.itemsets)


# =========================================================
# Sequences container
# =========================================================
class Sequences:
    def __init__(self):
        self.sequences = []

    def addSequence(self, seq):
        self.sequences.append(seq)


# =========================================================
# SequenceDatabase
# =========================================================
class SequenceDatabase:
    def __init__(self):
        self.sequences = []

    def loadFile(self, path):
        sid = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                seq = Sequence(sid)
                sid += 1

                tokens = line.split()
                currentItemset = Itemset()
                currentTimestamp = None

                for token in tokens:
                    if token.startswith("<") and token.endswith(">"):
                        currentTimestamp = int(token[1:-1])

                    elif token == "-1":
                        seq.addItemset(currentItemset, currentTimestamp)
                        currentItemset = Itemset()

                    elif token == "-2":
                        break

                    else:
                        if "(" in token:
                            i, v = token[:-1].split("(")
                            currentItemset.addItem(ItemValued(int(i), int(v)))
                        else:
                            currentItemset.addItem(ItemSimple(int(token)))

                self.sequences.append(seq)


# =========================================================
# PseudoSequence
# =========================================================
class PseudoSequence:
    def __init__(self, sequence, indexItemset, indexItem):
        self.sequence = sequence
        self.indexItemset = indexItemset
        self.indexItem = indexItem


class PseudoSequenceDatabase:
    def __init__(self):
        self.pseudoSequences = []

    def addSequence(self, ps):
        self.pseudoSequences.append(ps)

    def size(self):
        return len(self.pseudoSequences)


# =========================================================
# AlgoFournierViger08
# =========================================================
class AlgoFournierViger08:
    def __init__(self):
        self.startTime = 0
        self.endTime = 0
        self.patternCount = 0
        self.minSupport = 0
        self.patterns = Sequences()
        self.memoryLogger = MemoryLogger.getInstance()

    def runAlgorithm(self, minsupRelative, database):
        self.startTime = time.time()
        self.patternCount = 0
        self.patterns = Sequences()
        self.memoryLogger.reset()

        self.minSupport = max(1, int(minsupRelative * len(database.sequences)))

        pdb = PseudoSequenceDatabase()
        for seq in database.sequences:
            pdb.addSequence(PseudoSequence(seq, 0, 0))

        self._prefixSpan([], pdb)

        self.endTime = time.time()

    def _prefixSpan(self, prefix, pdb):
        supportMap = defaultdict(int)
        occurrenceMap = defaultdict(list)

        for ps in pdb.pseudoSequences:
            seq = ps.sequence
            startI = ps.indexItemset
            startP = ps.indexItem

            seenItems = set()

            for i in range(startI, seq.size()):
                itemset = seq.itemsets[i]
                posStart = startP if i == startI else 0

                for pos in range(posStart, len(itemset.items)):
                    item = itemset.items[pos]
                    if item not in seenItems:
                        supportMap[item] += 1
                        occurrenceMap[item].append((seq, i, pos))
                        seenItems.add(item)

        for item, support in supportMap.items():
            if support < self.minSupport:
                continue

            newPrefix = prefix + [item]
            self._savePattern(newPrefix, support)

            newPDB = PseudoSequenceDatabase()
            for seq, i, pos in occurrenceMap[item]:
                if pos + 1 < len(seq.itemsets[i].items):
                    newPDB.addSequence(PseudoSequence(seq, i, pos + 1))
                elif i + 1 < seq.size():
                    newPDB.addSequence(PseudoSequence(seq, i + 1, 0))

            if newPDB.size() > 0:
                self._prefixSpan(newPrefix, newPDB)

    def _savePattern(self, prefix, support):
        seq = Sequence(self.patternCount)
        itemset = Itemset()
        for item in prefix:
            itemset.addItem(item)
        seq.addItemset(itemset, 0)
        seq.support = support
        self.patterns.addSequence(seq)
        self.patternCount += 1


# =========================================================
# Main
# =========================================================
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inputFile = os.path.join(base_dir, "contextSequencesTimeExtended_ValuedItems.txt")
    minsup = 0.5

    db = SequenceDatabase()
    db.loadFile(inputFile)

    algo = AlgoFournierViger08()
    algo.runAlgorithm(minsup, db)

    for seq in algo.patterns.sequences:
        print(f"{{t=0}} {seq.itemsets[0]} #SUP: {seq.support}")

    print("============ Algorithm - STATISTICS ============")
    print(f"Total time ~ {int((algo.endTime - algo.startTime) * 1000)} ms")
    print(f"Frequent sequences count : {algo.patternCount}")
    print("===============================================")


if __name__ == "__main__":
    main()
