#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone Python port of SPMF ProSecCo components (Java -> Python).

Includes:
- AlgoProsecco (Equivalent to AlgoProsecco.java)
- AlgoGetFS (Equivalent to AlgoGetFS.java; PrefixSpan-style mining used by ProSecCo)
- ProgressiveSequenceDatabase / Metadata (Equivalent to ProgressiveSequenceDatabase.java / Metadata.java)
- SequenceDatabase, PseudoSequence, Pair, Itemset, SequentialPattern, SequentialPatterns, Utils, MemoryLogger

Built-ins only. Python 3.10+.
"""

from __future__ import annotations
import math
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


# =========================================================
# MemoryLogger (Equivalent to MemoryLogger.java)
# =========================================================
class MemoryLogger:
    """Equivalent to MemoryLogger.java"""
    _instance: Optional["MemoryLogger"] = None

    def __init__(self) -> None:
        self.maxMemory = 0

    @staticmethod
    def getInstance() -> "MemoryLogger":
        if MemoryLogger._instance is None:
            MemoryLogger._instance = MemoryLogger()
        return MemoryLogger._instance

    def reset(self) -> None:
        self.maxMemory = 0

    def checkMemory(self) -> None:
        return

    def getMaxMemory(self) -> int:
        return self.maxMemory


# =========================================================
# Itemset (Equivalent to Itemset.java)
# =========================================================
class Itemset:
    """Equivalent to Itemset.java"""
    def __init__(self, item: Optional[int] = None) -> None:
        self.items: List[int] = []
        if item is not None:
            self.addItem(item)

    def addItem(self, value: int) -> None:
        self.items.append(value)

    def getItems(self) -> List[int]:
        return self.items

    def get(self, index: int) -> int:
        return self.items[index]

    def size(self) -> int:
        return len(self.items)

    def cloneItemSetMinusItems(self, mapSequenceID: Dict[int, set], relativeMinsup: float) -> "Itemset":
        it = Itemset()
        for item in self.items:
            if len(mapSequenceID.get(item, set())) >= relativeMinsup:
                it.addItem(item)
        return it

    def cloneItemSet(self) -> "Itemset":
        it = Itemset()
        it.items.extend(self.items)
        return it

    def containsAll(self, itemset2: "Itemset") -> bool:
        i = 0
        for item in itemset2.getItems():
            found = False
            while (not found) and i < self.size():
                if self.get(i) == item:
                    found = True
                elif self.get(i) > item:
                    return False
                i += 1
            if not found:
                return False
        return True


# =========================================================
# PseudoSequence (Equivalent to PseudoSequence.java)
# =========================================================
@dataclass
class PseudoSequence:
    """Equivalent to PseudoSequence.java"""
    sequenceID: int
    indexFirstItem: int

    def getOriginalSequenceID(self) -> int:
        return self.sequenceID

    def getIndexFirstItem(self) -> int:
        return self.indexFirstItem

    def getSequenceID(self) -> int:
        return self.sequenceID


# =========================================================
# Pair (Equivalent to Pair.java)
# =========================================================
class Pair:
    """Equivalent to Pair.java"""
    def __init__(self, item: int) -> None:
        self.item = item
        self.pseudoSequences: List[PseudoSequence] = []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pair):
            return False
        return other.item == self.item

    def __hash__(self) -> int:
        return hash(str(self.item))

    def getItem(self) -> int:
        return self.item

    def getCount(self) -> int:
        return len(self.pseudoSequences)

    def getPseudoSequences(self) -> List[PseudoSequence]:
        return self.pseudoSequences


# =========================================================
# SequentialPattern / SequentialPatterns (Equivalent to *.java)
# =========================================================
class SequentialPattern:
    """Equivalent to SequentialPattern.java"""

    def __init__(self) -> None:
        self.itemsets: List[Itemset] = []
        self.sequencesIds: List[int] = []
        self.isFoundFlag: bool = False
        self.additionalSupport: int = 0

    def setSequenceIDs(self, sequencesIds: List[int]) -> None:
        self.sequencesIds = sequencesIds

    def getRelativeSupportFormated(self, sequencecount: int) -> str:
        rel = (len(self.sequencesIds) / float(sequencecount)) if sequencecount else 0.0
        s = f"{rel:.5f}".rstrip("0").rstrip(".")
        return s if s else "0"

    def getAbsoluteSupport(self) -> int:
        return len(self.sequencesIds)

    def addItemset(self, itemset: Itemset) -> None:
        self.itemsets.append(itemset)

    def copy(self) -> "SequentialPattern":
        c = SequentialPattern()
        for it in self.itemsets:
            c.addItemset(it.cloneItemSet())
        c.additionalSupport = self.additionalSupport
        c.sequencesIds = list(self.sequencesIds)
        return c

    def getItemsets(self) -> List[Itemset]:
        return self.itemsets

    def get(self, index: int) -> Itemset:
        return self.itemsets[index]

    def size(self) -> int:
        return len(self.itemsets)

    def getSequenceIDs(self) -> List[int]:
        return self.sequencesIds

    def setIsFound(self, b: bool) -> bool:
        self.isFoundFlag = b
        return b

    def isFound(self) -> bool:
        return self.isFoundFlag

    def addAdditionalSupport(self, additionalSupport: int) -> None:
        self.additionalSupport += additionalSupport


class SequentialPatterns:
    """Equivalent to SequentialPatterns.java"""

    def __init__(self, name: str) -> None:
        self.levels: List[List[SequentialPattern]] = [[]]
        self.sequenceCount: int = 0
        self.name = name

    def copy(self) -> "SequentialPatterns":
        k = 0
        c = SequentialPatterns(self.name)
        for level in self.getLevels():
            for pat in level:
                c.addSequence(pat.copy(), k)
            k += 1
        return c

    def addSequence(self, sequence: SequentialPattern, k: int) -> None:
        while len(self.levels) <= k:
            self.levels.append([])
        self.levels[k].append(sequence)
        self.sequenceCount += 1

    def getLevel(self, index: int) -> List[SequentialPattern]:
        return self.levels[index]

    def getLevelCount(self) -> int:
        return len(self.levels)

    def getLevels(self) -> List[List[SequentialPattern]]:
        return self.levels

    def getSequenceCount(self) -> int:
        return self.sequenceCount


# =========================================================
# Utils (Equivalent to Utils.java; keep the same behavior)
# =========================================================
class Utils:
    """Equivalent to Utils.java"""

    @staticmethod
    def _isSubsetOf(itemsetA: List[int], itemsetB: List[int]) -> bool:
        found = False
        for tokenA in itemsetA:
            for tokenB in itemsetB:
                if tokenA == tokenB:
                    found = True
                    break
            if not found:
                return False
            found = False
        return False

    @staticmethod
    def isSubsequenceOf(pattern: SequentialPattern, sequenceB: List[int], multiItem: bool) -> bool:
        if not multiItem:
            return Utils.isSubsequenceOfSingleItems(pattern, sequenceB)
        idxItemsetB = 0
        for itA in pattern.getItemsets():
            subset = False
            itB = Itemset()
            i = idxItemsetB
            while i < len(sequenceB):
                if sequenceB[i] == -1:
                    if itB.containsAll(itA):
                        subset = True
                        idxItemsetB = i
                    else:
                        itB = Itemset()
                else:
                    itB.addItem(sequenceB[i])
                if i + 1 < len(sequenceB) and sequenceB[i + 1] == -2:
                    break
                i += 1
            if not subset:
                return False
        return True

    @staticmethod
    def isSubsequenceOfSingleItems(pattern: SequentialPattern, sequenceB: List[int]) -> bool:
        idxItemsetB = 0
        for itA in pattern.getItemsets():
            subset = False
            i = idxItemsetB
            while i < len(sequenceB):
                if sequenceB[i] == -1:
                    i += 1
                    continue
                if itA.getItems()[0] == sequenceB[i]:
                    subset = True
                    idxItemsetB = i + 1
                    break
                if idxItemsetB < len(sequenceB) and sequenceB[idxItemsetB] == -2:
                    break
                i += 1
            if not subset:
                return False
        return True


# =========================================================
# SequenceDatabase (Equivalent to SequenceDatabase.java)
# =========================================================
class SequenceDatabase:
    """Equivalent to SequenceDatabase.java"""

    def __init__(self) -> None:
        self.sequences: List[List[int]] = []
        self.itemOccurrenceCount: int = 0

    def loadFile(self, path: str) -> None:
        self.itemOccurrenceCount = 0
        self.sequences = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line[0] in "#%@":
                    continue
                tokens = line.split(" ")
                seq = [int(t) for t in tokens]
                self.sequences.append(seq)

    def size(self) -> int:
        return len(self.sequences)

    def getSequences(self) -> List[List[int]]:
        return self.sequences


# =========================================================
# Metadata + ProgressiveSequenceDatabase (Equivalent to *.java)
# =========================================================
@dataclass(order=True)
class _Transaction:
    priority: int
    sequence: List[int]
    numItems: int


class Metadata:
    """Equivalent to Metadata.java"""

    def __init__(self, errorTolerance: float, blockSize: int, dbSize: int) -> None:
        self.errorTolerance = errorTolerance
        self.dbSize = dbSize
        self.numBlocks = int(math.ceil(dbSize / float(blockSize)))
        self.numSequencesProcessed = 0
        self.iteration = 1
        self.capSequences: List[_Transaction] = []
        self.sIndex: int = 0

    def UpdateWithSequence(self, seq: List[int], numItems: int) -> None:
        self.numSequencesProcessed += 1
        if (2 ** numItems) > (2 ** self.sIndex):
            c = self._getCapBound(seq)
            self.capSequences.append(_Transaction(priority=c, sequence=seq, numItems=numItems))
            self.capSequences.sort(reverse=True)
            if self.capSequences and self.capSequences[0].priority < (2 ** len(self.capSequences)) - 1:
                self.capSequences.pop(0)
            self.sIndex = len(self.capSequences)

    def GetError(self) -> float:
        if self.numSequencesProcessed >= self.dbSize:
            return 0.0
        eps = math.sqrt((self.sIndex - math.log(self.errorTolerance) + math.log(self.numBlocks)) / float(2 * self.numSequencesProcessed))
        if math.isinf(eps) or math.isnan(eps):
            return 0.0
        return eps

    def _getCapBound(self, sequence: List[int]) -> int:
        lst: List[Itemset] = []
        it = Itemset()
        length = 0
        for el in sequence:
            if el >= 0:
                length += 1
                it.addItem(el)
            elif el == -1:
                lst.append(it.cloneItemSet())
                it = Itemset()
            elif el == -2:
                break
        c = (2 ** length) - 1
        while len(lst) > 1:
            itA = lst.pop(0)
            i = 0
            while i < len(lst):
                if itA.containsAll(lst[i]):
                    c = int(c - (2 ** lst[i].size()) + 1)
                    lst.pop(i)
                else:
                    i += 1
        return c

    def getNumSequencesProcessed(self) -> int:
        return self.numSequencesProcessed


class ProgressiveSequenceDatabaseCallbacks:
    """Equivalent to ProgressiveSequenceDatabaseCallbacks interface"""
    def nextSequenceBlock(self, block: List[List[int]], outputFilePath: str, isLast: bool) -> None:
        raise NotImplementedError


class ProgressiveSequenceDatabase(SequenceDatabase):
    """Equivalent to ProgressiveSequenceDatabase.java"""

    def __init__(self) -> None:
        super().__init__()
        self.metadata: Optional[Metadata] = None

    def loadFile(self, inputPath: str, outputPath: str, blockSize: int, dbSize: int,
                 errorTolerance: float, startErrorThreshold: float, callback: ProgressiveSequenceDatabaseCallbacks) -> None:
        self.metadata = Metadata(errorTolerance, blockSize, dbSize)
        self.itemOccurrenceCount = 0
        self.sequences = []
        with open(inputPath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line[0] in "#%@":
                    continue
                tokens = line.split(" ")
                seq = [int(t) for t in tokens]
                numItems = sum(1 for x in seq if x >= 0)
                self.metadata.UpdateWithSequence(seq, numItems)
                self.sequences.append(seq)
                if len(self.sequences) % blockSize == 0:
                    if self.metadata.getNumSequencesProcessed() < dbSize and self.metadata.GetError() < startErrorThreshold:
                        block = list(self.sequences)
                        callback.nextSequenceBlock(block, outputPath, False)
                        self.sequences.clear()
        if self.sequences:
            callback.nextSequenceBlock(self.sequences, outputPath, True)

    def getError(self) -> float:
        return 0.0 if self.metadata is None else self.metadata.GetError()

    def numSequencesProcessed(self) -> int:
        return 0 if self.metadata is None else self.metadata.getNumSequencesProcessed()


# =========================================================
# AlgoGetFS (Equivalent to AlgoGetFS.java)
# =========================================================
class AlgoGetFS:
    """Equivalent to AlgoGetFS.java"""

    BUFFERS_SIZE = 2000

    def __init__(self) -> None:
        self.sequenceDatabase: Optional[SequenceDatabase] = None
        self.minsuppAbsolute: int = 0
        self.containsItemsetsWithMultipleItems: bool = False
        self.mapSequenceID: Optional[Dict[int, List[int]]] = None
        self.patterns: Optional[SequentialPatterns] = None
        self.maximumPatternLength: int = 1000
        self.patternBuffer: List[int] = [0] * self.BUFFERS_SIZE

    def reset(self) -> None:
        self.containsItemsetsWithMultipleItems = False
        self.patterns = None
        self.mapSequenceID = None
        self.minsuppAbsolute = 0

    def setMapSequenceID(self, mapSequenceID: Dict[int, List[int]]) -> None:
        self.mapSequenceID = mapSequenceID

    def getMapSequenceID(self) -> Dict[int, List[int]]:
        return {} if self.mapSequenceID is None else self.mapSequenceID

    def isContainsItemsetsWithMultipleItems(self) -> bool:
        return self.containsItemsetsWithMultipleItems

    def getFS(self, sequenceDatabase: SequenceDatabase, minSup: int) -> SequentialPatterns:
        self.patterns = SequentialPatterns("FREQUENT SEQUENTIAL PATTERNS")
        self.sequenceDatabase = sequenceDatabase
        self.minsuppAbsolute = minSup

        if self.mapSequenceID is not None:
            self.findSequencesContainingItems()
        else:
            self.mapSequenceID = self.findSequencesContainingItems()
            for key in list(self.mapSequenceID.keys()):
                if len(self.mapSequenceID[key]) < self.minsuppAbsolute:
                    del self.mapSequenceID[key]

        if self.containsItemsetsWithMultipleItems:
            self.prefixspanWithMultipleItems(self.mapSequenceID)
        else:
            self.prefixspanWithSingleItems(self.mapSequenceID)
        return self.patterns

    def findSequencesContainingItems(self) -> Dict[int, List[int]]:
        assert self.sequenceDatabase is not None
        mapSequenceID: Dict[int, List[int]] = {} if self.mapSequenceID is None else self.mapSequenceID

        for i, sequence in enumerate(self.sequenceDatabase.getSequences()):
            currentItemsetItemCount = 0
            alreadySeenInSequence = set()
            for token in sequence:
                if token >= 0:
                    currentItemsetItemCount += 1
                    if token not in alreadySeenInSequence:
                        alreadySeenInSequence.add(token)
                        if token not in mapSequenceID:
                            mapSequenceID[token] = []
                        mapSequenceID[token].append(i)
                elif token == -1:
                    if currentItemsetItemCount > 1:
                        self.containsItemsetsWithMultipleItems = True
                    currentItemsetItemCount = 0
                elif token == -2:
                    break
        self.mapSequenceID = mapSequenceID
        return mapSequenceID

    def prefixspanWithSingleItems(self, mapSequenceID: Dict[int, List[int]]) -> None:
        assert self.sequenceDatabase is not None and self.patterns is not None
        for i in range(self.sequenceDatabase.size()):
            sequence = self.sequenceDatabase.getSequences()[i]
            currentPosition = 0
            for token in sequence:
                if token >= 0:
                    if token in mapSequenceID:
                        sequence[currentPosition] = token
                        currentPosition += 1
                elif token == -1:
                    sequence[currentPosition] = -1
                    currentPosition += 1
                elif token == -2:
                    sequence[currentPosition] = -2
                    currentPosition += 1
                    break
            del sequence[currentPosition:]

        for item in sorted(mapSequenceID.keys()):
            seqIds = mapSequenceID[item]
            if len(seqIds) >= self.minsuppAbsolute:
                self.patternBuffer[0] = item
                pat = SequentialPattern()
                pat.addItemset(Itemset(item))
                pat.setSequenceIDs(list(seqIds))
                self.patterns.addSequence(pat, 1)
                projected = self.buildProjectedDatabaseSingleItems(item, seqIds)
                if projected:
                    self.recursionSingleItems(projected, 2, 0)

    def buildProjectedDatabaseSingleItems(self, item: int, sequenceIDs: List[int]) -> List[PseudoSequence]:
        assert self.sequenceDatabase is not None
        projected: List[PseudoSequence] = []
        for sid in sequenceIDs:
            seq = self.sequenceDatabase.getSequences()[sid]
            for idx, token in enumerate(seq):
                if token == item:
                    projected.append(PseudoSequence(sid, idx + 1))
        return projected

    def findAllFrequentPairsSingleItems(self, sequences: List[PseudoSequence], lastBufferPosition: int) -> Dict[int, List[PseudoSequence]]:
        assert self.sequenceDatabase is not None
        mapItemPseudo: Dict[int, List[PseudoSequence]] = {}
        lastSeen: Dict[int, int] = {}
        for ps in sequences:
            sid = ps.getOriginalSequenceID()
            seq = self.sequenceDatabase.getSequences()[sid]
            start = ps.getIndexFirstItem()
            for i in range(start, len(seq)):
                token = seq[i]
                if token == -2:
                    break
                if token == -1:
                    continue
                if lastSeen.get(token) != sid:
                    lastSeen[token] = sid
                    if token not in mapItemPseudo:
                        mapItemPseudo[token] = []
                    mapItemPseudo[token].append(PseudoSequence(sid, i + 1))
        return mapItemPseudo

    def recursionSingleItems(self, database: List[PseudoSequence], k: int, lastBufferPosition: int) -> None:
        itemsPseudo = self.findAllFrequentPairsSingleItems(database, lastBufferPosition)
        for item in sorted(itemsPseudo.keys()):
            pslist = itemsPseudo[item]
            if len({ps.sequenceID for ps in pslist}) >= self.minsuppAbsolute:
                self.patternBuffer[lastBufferPosition + 1] = -1
                self.patternBuffer[lastBufferPosition + 2] = item
                self.savePattern(lastBufferPosition + 2, pslist)
                if k < self.maximumPatternLength:
                    self.recursionSingleItems(pslist, k + 1, lastBufferPosition + 2)
        MemoryLogger.getInstance().checkMemory()

    class MapFrequentPairs:
        def __init__(self) -> None:
            self.mapPairs: Dict[Pair, Pair] = {}
            self.mapPairsInPostfix: Dict[Pair, Pair] = {}

    def prefixspanWithMultipleItems(self, mapSequenceID: Dict[int, List[int]]) -> None:
        assert self.sequenceDatabase is not None and self.patterns is not None

        for i in range(self.sequenceDatabase.size()):
            sequence = self.sequenceDatabase.getSequences()[i]
            currentPosition = 0
            currentItemsetItemCount = 0
            for token in sequence:
                if token >= 0:
                    if token in mapSequenceID:
                        sequence[currentPosition] = token
                        currentPosition += 1
                        currentItemsetItemCount += 1
                elif token == -1:
                    if currentItemsetItemCount > 0:
                        sequence[currentPosition] = -1
                        currentPosition += 1
                    currentItemsetItemCount = 0
                elif token == -2:
                    sequence[currentPosition] = -2
                    currentPosition += 1
                    break
            del sequence[currentPosition:]

        for item in sorted(mapSequenceID.keys()):
            seqIds = mapSequenceID[item]
            if len(seqIds) >= self.minsuppAbsolute:
                self.patternBuffer[0] = item
                pat = SequentialPattern()
                pat.addItemset(Itemset(item))
                pat.setSequenceIDs(list(seqIds))
                self.patterns.addSequence(pat, 1)
                projected = self.buildProjectedDatabase_multi(item, seqIds, is_postfix_ext=True)
                if projected:
                    self.recursion(self.patternBuffer, projected, 2, 0)

    def buildProjectedDatabase_multi(self, item: int, sequenceIDs: List[int], is_postfix_ext: bool) -> List[PseudoSequence]:
        assert self.sequenceDatabase is not None
        projected: List[PseudoSequence] = []
        for sid in sequenceIDs:
            seq = self.sequenceDatabase.getSequences()[sid]
            for idx in range(len(seq)):
                if seq[idx] == item:
                    if is_postfix_ext:
                        start = idx + 1
                    else:
                        j = idx + 1
                        while j < len(seq) and seq[j] not in (-1, -2):
                            j += 1
                        if j < len(seq) and seq[j] == -1:
                            j += 1
                        start = j
                    projected.append(PseudoSequence(sid, start))
        return projected

    def findAllFrequentPairs(self, sequences: List[PseudoSequence], lastBufferPosition: int) -> "AlgoGetFS.MapFrequentPairs":
        assert self.sequenceDatabase is not None
        mapsPairs = AlgoGetFS.MapFrequentPairs()
        lastSeenPostfix: Dict[int, int] = {}
        lastSeenNonPostfix: Dict[int, int] = {}

        for ps in sequences:
            sid = ps.getOriginalSequenceID()
            seq = self.sequenceDatabase.getSequences()[sid]
            start = ps.getIndexFirstItem()

            postfix = False
            if start > 0 and start - 1 < len(seq) and seq[start - 1] not in (-1, -2):
                postfix = True

            i = start
            while i < len(seq):
                token = seq[i]
                if token == -2:
                    break
                if token == -1:
                    postfix = False
                    i += 1
                    continue

                if postfix:
                    if lastSeenPostfix.get(token) != sid:
                        lastSeenPostfix[token] = sid
                        existing = None
                        for k in mapsPairs.mapPairsInPostfix.keys():
                            if k.item == token:
                                existing = k
                                break
                        if existing is None:
                            existing = Pair(token)
                            mapsPairs.mapPairsInPostfix[existing] = existing
                        existing.pseudoSequences.append(PseudoSequence(sid, i + 1))
                else:
                    if lastSeenNonPostfix.get(token) != sid:
                        lastSeenNonPostfix[token] = sid
                        existing = None
                        for k in mapsPairs.mapPairs.keys():
                            if k.item == token:
                                existing = k
                                break
                        if existing is None:
                            existing = Pair(token)
                            mapsPairs.mapPairs[existing] = existing
                        j = i + 1
                        while j < len(seq) and seq[j] not in (-1, -2):
                            j += 1
                        if j < len(seq) and seq[j] == -1:
                            j += 1
                        existing.pseudoSequences.append(PseudoSequence(sid, j))
                i += 1

        return mapsPairs

    def recursion(self, patternBuffer: List[int], database: List[PseudoSequence], k: int, lastBufferPosition: int) -> None:
        mapsPairs = self.findAllFrequentPairs(database, lastBufferPosition)

        postfix_pairs = sorted(mapsPairs.mapPairsInPostfix.keys(), key=lambda p: p.item)
        for pair in postfix_pairs:
            if len({ps.sequenceID for ps in pair.getPseudoSequences()}) >= self.minsuppAbsolute:
                newpos = lastBufferPosition + 1
                self.patternBuffer[newpos] = pair.getItem()
                self.savePattern(newpos, pair.getPseudoSequences())
                if k < self.maximumPatternLength:
                    self.recursion(self.patternBuffer, pair.getPseudoSequences(), k + 1, newpos)

        s_pairs = sorted(mapsPairs.mapPairs.keys(), key=lambda p: p.item)
        for pair in s_pairs:
            if len({ps.sequenceID for ps in pair.getPseudoSequences()}) >= self.minsuppAbsolute:
                newpos = lastBufferPosition + 1
                self.patternBuffer[newpos] = -1
                newpos += 1
                self.patternBuffer[newpos] = pair.getItem()
                self.savePattern(newpos, pair.getPseudoSequences())
                if k < self.maximumPatternLength:
                    self.recursion(self.patternBuffer, pair.getPseudoSequences(), k + 1, newpos)

        MemoryLogger.getInstance().checkMemory()

    def savePattern(self, lastBufferPosition: int, pseudoSequences: List[PseudoSequence]) -> None:
        assert self.patterns is not None
        seen = set()
        seqIds: List[int] = []
        for ps in pseudoSequences:
            sid = ps.getOriginalSequenceID()
            if sid not in seen:
                seen.add(sid)
                seqIds.append(sid)

        pat = SequentialPattern()
        current = Itemset()
        for i in range(lastBufferPosition + 1):
            token = self.patternBuffer[i]
            if token == -1:
                pat.addItemset(current)
                current = Itemset()
            else:
                current.addItem(token)
        pat.addItemset(current)
        pat.setSequenceIDs(seqIds)
        self.patterns.addSequence(pat, pat.size())


# =========================================================
# AlgoProsecco (Equivalent to AlgoProsecco.java)
# =========================================================
class AlgoProsecco(ProgressiveSequenceDatabaseCallbacks):
    """Equivalent to AlgoProsecco.java"""

    def __init__(self) -> None:
        self.startTime = 0
        self.noCountTime = 0
        self.endTime = 0
        self.prevRuntime = 0
        self.noCountTimeBlock = 0

        self.minsuppAbsolute = 0
        self.patterns: Optional[SequentialPatterns] = None
        self.mapSequenceID: Optional[Dict[int, List[int]]] = None
        self.outputFilepath: Optional[str] = None

        self.alg = AlgoGetFS()
        self.sequenceDatabase: Optional[ProgressiveSequenceDatabase] = None

        self.minsupRelative: float = 0.0
        self.progressivePatterns: Optional[SequentialPatterns] = None

    def runAlgorithm(self, inputFilePath: str, outputFilePath: str, blockSize: int, dbSize: int,
                     errorTolerance: float, minsupRelative: float) -> None:
        self.startTime = int(time.time() * 1000)
        MemoryLogger.getInstance().reset()
        self.prevRuntime = self.startTime
        self.outputFilepath = outputFilePath

        self.minsupRelative = minsupRelative
        self.sequenceDatabase = ProgressiveSequenceDatabase()
        self.sequenceDatabase.loadFile(inputFilePath, outputFilePath, blockSize, dbSize,
                                       errorTolerance, minsupRelative / 2.0, self)

    def nextSequenceBlock(self, block: List[List[int]], outputFilePath: str, isLast: bool) -> None:
        assert self.sequenceDatabase is not None

        epsilon = self.sequenceDatabase.getError()
        sequenceCount = self.sequenceDatabase.size()

        self.minsuppAbsolute = int(math.ceil((self.minsupRelative - epsilon / 2.0) * sequenceCount))
        if self.minsuppAbsolute <= 0:
            self.minsuppAbsolute = 1

        print(f"[DEBUG] minsupRelative = {self.minsuppAbsolute}, transactions = {sequenceCount}")

        self.alg.reset()
        if self.progressivePatterns is not None and self.mapSequenceID is not None:
            self.alg.setMapSequenceID(self.mapSequenceID)

        self.patterns = self.alg.getFS(self.sequenceDatabase, self.minsuppAbsolute)

        if self.progressivePatterns is None:
            self.mapSequenceID = dict(self.alg.getMapSequenceID())
            self.progressivePatterns = self.patterns.copy()
        else:
            self.progressivePatterns = self.patterns.copy()

        self.savePatternsToFile(self.progressivePatterns)

        if isLast:
            self.endTime = int(time.time() * 1000)

    def savePatternsToFile(self, patterns: SequentialPatterns) -> None:
        assert self.outputFilepath is not None
        try:
            import os
            if os.path.exists(self.outputFilepath):
                os.remove(self.outputFilepath)
        except Exception:
            pass

        r_parts: List[str] = []
        for level in patterns.getLevels():
            for pattern in level:
                for it in pattern.getItemsets():
                    for item in it.getItems():
                        r_parts.append(str(item))
                        r_parts.append(" ")
                    r_parts.append("-1")
                r_parts.append(" ")
                r_parts.append("#SUP: ")
                r_parts.append(str(pattern.getAbsoluteSupport()))
                r_parts.append("\n")

        with open(self.outputFilepath, "w", encoding="utf-8") as w:
            w.write("".join(r_parts))
            w.write("\n")


# =========================================================
# CLI
# =========================================================
def main() -> None:
    if len(sys.argv) != 7:
        print("Usage:")
        print("python prosecco_standalone.py input.txt output.txt mode maxLen delta minsupRatio")
        sys.exit(1)

    inputFile = sys.argv[1]
    outputFile = sys.argv[2]
    maxPatternLength = int(sys.argv[4])
    delta = float(sys.argv[5])
    minsupRatio = float(sys.argv[6])

    tmp = SequenceDatabase()
    tmp.loadFile(inputFile)
    dbSize = tmp.size()

    algo = AlgoProsecco()
    algo.alg.maximumPatternLength = maxPatternLength
    algo.runAlgorithm(inputFile, outputFile, blockSize=1, dbSize=dbSize, errorTolerance=delta, minsupRelative=minsupRatio)

    print(f"✅ Mining complete! Output saved to: {outputFile}")
    print("=========================================")


if __name__ == "__main__":
    main()
