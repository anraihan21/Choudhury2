#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
import time
from itertools import combinations, product


class MemoryLogger:
    """Equivalent to MemoryLogger.java"""
    _instance = None

    def __init__(self):
        self.maxMemory = 0.0

    @staticmethod
    def getInstance():
        if MemoryLogger._instance is None:
            MemoryLogger._instance = MemoryLogger()
        return MemoryLogger._instance

    def reset(self):
        self.maxMemory = 0.0

    def checkMemory(self):
        pass

    def getMaxMemory(self):
        return self.maxMemory


class ItemSimple:
    """Equivalent to ItemSimple.java"""
    def __init__(self, item_id: int):
        self._id = int(item_id)

    def getId(self):
        return self._id


class Itemset:
    """Equivalent to Itemset.java"""
    def __init__(self, items, timestamp: int):
        self._items = items
        self._timestamp = int(timestamp)

    def getItems(self):
        return self._items

    def getTimestamp(self):
        return self._timestamp


class Sequence:
    """Equivalent to Sequence.java"""
    def __init__(self, sid: int):
        self.sid = int(sid)
        self.itemsets = []
        self._sids = set()

    def addItemset(self, it: Itemset):
        self.itemsets.append(it)

    def getItemsets(self):
        return self.itemsets

    def size(self):
        return len(self.itemsets)

    def setSequencesID(self, sids):
        self._sids = set(sids)

    def getAbsoluteSupport(self):
        return len(self._sids)

    def getSequencesID(self):
        return self._sids if hasattr(self, '_sids') and self._sids is not None else set()

    def get(self, index: int):
        return self.itemsets[index]

    def toStringShort(self):
        out = []
        for it in self.itemsets:
            out.append("{t=" + str(it.getTimestamp()) + ", ")
            for x in it.getItems():
                out.append(str(x.getId()) + " ")
            out.append("}")
        out.append("     ")
        return "".join(out)

    def strictlyContains(self, other) -> bool:
        if self.size() < other.size():
            return False

        i = 0
        for it in self.itemsets:
            if i >= other.size():
                break
            oit = other.itemsets[i]
            if it.getTimestamp() != oit.getTimestamp():
                continue
            it_items = set(x.getId() for x in it.getItems())
            oit_items = set(x.getId() for x in oit.getItems())
            if oit_items.issubset(it_items):
                i += 1
        return i == other.size()


class SequenceDatabase:
    """Equivalent to SequenceDatabase.java"""
    def __init__(self):
        self.sequences = []

    def addSequence(self, s: Sequence):
        self.sequences.append(s)

    def getSequences(self):
        return self.sequences

    def size(self):
        return len(self.sequences)


class MDPattern:
    """Equivalent to MDPattern.java"""
    WILDCARD = -1

    def __init__(self):
        self.values = []
        self.sids = set()

    def add(self, v: int):
        self.values.append(int(v))

    def size(self):
        return len(self.values)

    def getValue(self, i: int):
        return self.values[i]

    def setPatternsIDList(self, sids):
        self.sids = set(sids)

    def getAbsoluteSupport(self):
        return len(self.sids)

    def toStringShort(self):
        out = ["[ "]
        for v in self.values:
            out.append("* " if v == MDPattern.WILDCARD else str(v) + " ")
        out.append("]")
        return "".join(out)

    def isAllWildcards(self):
        return all(v == MDPattern.WILDCARD for v in self.values)

    def strictlyContains(self, other) -> bool:
        """
        True if self is MORE GENERAL than other (has * where other has value),
        same support, and matches on all non-* positions.
        """
        if self.getAbsoluteSupport() != other.getAbsoluteSupport():
            return False
        more_general = False
        for i in range(len(self.values)):
            sv = self.values[i]
            ov = other.values[i]
            if sv == MDPattern.WILDCARD and ov != MDPattern.WILDCARD:
                more_general = True
            elif sv != ov:
                return False
        return more_general

    def matches(self, other) -> bool:
        for i in range(len(self.values)):
            sv = self.values[i]
            ov = other.values[i]
            if sv == MDPattern.WILDCARD:
                continue
            if ov == MDPattern.WILDCARD or sv != ov:
                return False
        return True


class MDSequence:
    """Equivalent to MDSequence.java"""
    def __init__(self, md: MDPattern, seq: Sequence):
        self.md = md
        self.seq = seq
        self.support = 0

    def setSupport(self, s: int):
        self.support = int(s)

    def getAbsoluteSupport(self):
        return self.support

    def contains(self, other) -> bool:
        return self.md.strictlyContains(other.md) and self.seq.strictlyContains(other.seq)


class MDSequenceDatabase:
    """Equivalent to MDSequenceDatabase.java"""
    def __init__(self):
        self.mdseqs = []
        self.mdpats = []
        self.seqdb = SequenceDatabase()

    def size(self):
        return len(self.mdseqs)

    def loadFile(self, path: str):
        sid = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                t = line.strip().split()
                if not t:
                    continue

                i = 0
                md = MDPattern()
                while i < len(t) and t[i] != "-3":
                    md.add(MDPattern.WILDCARD if t[i] == "*" else int(t[i]))
                    i += 1
                if i >= len(t) or t[i] != "-3":
                    continue
                i += 1

                seq = Sequence(sid)
                cur_items = []
                cur_t = None

                while i < len(t):
                    tok = t[i]
                    if tok.startswith("<") and tok.endswith(">"):
                        cur_t = int(tok[1:-1])
                        cur_items = []
                    elif tok == "-1":
                        seq.addItemset(Itemset([ItemSimple(x) for x in cur_items], cur_t))
                    elif tok == "-2":
                        break
                    else:
                        cur_items.append(int(tok))
                    i += 1

                self.mdpats.append(md)
                self.seqdb.addSequence(seq)
                self.mdseqs.append((md, seq))
                sid += 1


class AlgoDim:
    """Equivalent to AlgoDim.java"""
    def runAlgorithm(self, mdpatterns, minsup: float):
        minsupp_abs = int(math.ceil(minsup * len(mdpatterns)))
        if minsupp_abs <= 0:
            minsupp_abs = 1

        dims = mdpatterns[0].size()

        domains = []
        for d in range(dims):
            vals = set()
            for p in mdpatterns:
                v = p.getValue(d)
                if v != MDPattern.WILDCARD:
                    vals.add(v)
            domains.append(sorted(vals))

        candidates = []
        for prod in product(*[([MDPattern.WILDCARD] + dom) for dom in domains]):
            if all(v == MDPattern.WILDCARD for v in prod):
                continue
            c = MDPattern()
            for v in prod:
                c.add(v)
            candidates.append(c)

        frequent = []
        for c in candidates:
            sids = set()
            for idx, p in enumerate(mdpatterns):
                if c.matches(p):
                    sids.add(idx)
            if len(sids) >= minsupp_abs:
                c.setPatternsIDList(sids)
                frequent.append(c)

        # ✅ CLOSED FIX: p is NOT closed if there exists q MORE SPECIFIC with same support
        # i.e., p strictlyContains(q) (p more general) is True.
        closed = []
        for p in frequent:
            is_closed = True
            for q in frequent:
                if p is q:
                    continue
                if p.getAbsoluteSupport() != q.getAbsoluteSupport():
                    continue
                if p.strictlyContains(q):  # p more general than q
                    is_closed = False
                    break
            if is_closed:
                closed.append(p)

        # keep a stable deterministic order
        closed.sort(key=lambda x: (-sum(v != MDPattern.WILDCARD for v in x.values), x.toStringShort()))
        return closed


def _mine_closed_sequential_patterns(seqdb_172, minsup: float):
    """
    Mine closed sequential patterns from the sequence part of the MD database.
    Uses enumerate-all + closed filter (same closed definition as Java).
    Returns list of 172-style Sequence with getSequencesID() set.
    """
    minsupp_abs = max(1, int(math.ceil(minsup * len(seqdb_172))))
    patterns = {}
    for (md, seq) in seqdb_172:
        for rep in _enumerate_subsequences(seq):
            patterns.setdefault(rep, set()).add(seq.sid)
    seqs = []
    for rep, sids in patterns.items():
        if len(sids) < minsupp_abs:
            continue
        s = _rep_to_sequence(rep)
        s.setSequencesID(sids)
        seqs.append(s)
    # Closed: keep only if no strict superset with same support
    closed = []
    for s in seqs:
        if any(
            t is not s
            and t.getAbsoluteSupport() == s.getAbsoluteSupport()
            and t.strictlyContains(s)
            for t in seqs
        ):
            continue
        closed.append(s)
    # Match Java FV08: keep only closed seq patterns that are not a
    # (flexible) subsequence of another closed pattern with same support.
    # This prunes e.g. {t=0,3} when {t=0,2}{t=1,3} exists with same support.
    def is_subsequence_of(a, b):
        if b.size() < a.size():
            return False
        j = 0
        for i in range(a.size()):
            ai = a.get(i)
            need = set(x.getId() for x in ai.getItems())
            while j < b.size():
                bj = b.get(j)
                have = set(x.getId() for x in bj.getItems())
                if need.issubset(have):
                    j += 1
                    break
                j += 1
            else:
                return False
        return True

    maximal_closed = []
    for s in closed:
        if any(
            t is not s
            and t.getAbsoluteSupport() == s.getAbsoluteSupport()
            and t.size() > s.size()
            and is_subsequence_of(s, t)
            for t in closed
        ):
            continue
        maximal_closed.append(s)
    maximal_closed.sort(key=lambda x: (-x.size(), x.toStringShort()))
    return maximal_closed


def _enumerate_subsequences(seq: Sequence):
    its = seq.getItemsets()
    results = set()
    for r in range(1, len(its) + 1):
        for idxs in combinations(range(len(its)), r):
            base_time = its[idxs[0]].getTimestamp()
            parts = []
            for i in idxs:
                ts = its[i].getTimestamp() - base_time
                items = [x.getId() for x in its[i].getItems()]
                opts = []
                for k in range(1, len(items) + 1):
                    for c in combinations(items, k):
                        opts.append((ts, tuple(c)))
                parts.append(opts)
            for prod in product(*parts):
                results.add(tuple(prod))
    return results


def _rep_to_sequence(rep):
    s = Sequence(0)
    for t, items in rep:
        s.addItemset(Itemset([ItemSimple(x) for x in items], t))
    return s


class AlgoSeqDim:
    """Equivalent to AlgoSeqDim.java: closed seq first, then project MD DB and run AlgoDim (Charm)."""
    def __init__(self):
        self.patternCount = 0
        self.startTime = 0
        self.endTime = 0

    def runAlgorithm(self, db: MDSequenceDatabase, minsup: float, outpath: str):
        MemoryLogger.getInstance().reset()
        self.patternCount = 0
        self.startTime = int(time.time() * 1000)

        # (1) Mine closed sequential patterns (enumerate-all + closed filter)
        closed_seqs = _mine_closed_sequential_patterns(db.mdseqs, minsup)

        algoDim = AlgoDim()
        all_patterns = []

        # (2) For each closed sequential pattern: project MD database and run AlgoDim (Charm)
        for seq in closed_seqs:
            sids = seq.getSequencesID()
            projected_mdpats = [db.mdpats[i] for i in sids]
            if not projected_mdpats:
                continue
            newMinSupp = minsup * db.size() / len(projected_mdpats)
            closed_md = algoDim.runAlgorithm(projected_mdpats, newMinSupp)

            for mdpat in closed_md:
                mds = MDSequence(mdpat, seq)
                if mdpat.isAllWildcards():
                    mds.setSupport(len(sids))
                else:
                    mds.setSupport(mdpat.getAbsoluteSupport())
                all_patterns.append(mds)
                self.patternCount += 1

        # (3) Remove redundancy: keep only closed MD-sequences (Java removeRedundancy)
        final = []
        for p in all_patterns:
            included = False
            for q in all_patterns:
                if p is q:
                    continue
                if q.getAbsoluteSupport() != p.getAbsoluteSupport():
                    continue
                if q.contains(p):
                    included = True
                    break
            if not included:
                final.append(p)

        # output ordering: match Java (level/length then string)
        final.sort(key=lambda x: (-x.seq.size(), x.md.toStringShort(), x.seq.toStringShort()))

        with open(outpath, "w", encoding="utf-8") as f:
            for r in final:
                f.write(r.md.toStringShort() + r.seq.toStringShort() + " #SUP: " + str(r.getAbsoluteSupport()) + "\n")

        self.endTime = int(time.time() * 1000)
        MemoryLogger.getInstance().checkMemory()

    def printStatistics(self, dbsize):
        print("=============  SEQ-DIM - STATISTICS =============")
        print(" Total time ~ {} ms".format(self.endTime - self.startTime))
        print(" max memory : {}".format(MemoryLogger.getInstance().getMaxMemory()))
        print(" Frequent sequences count : {}".format(self.patternCount))
        print("=================================================")


def main():
    if len(sys.argv) != 3:
        print("Usage: python seqdim_closed_mdspm.py <input_path> <minsup>")
        print("Example: python seqdim_closed_mdspm.py ContextMDSequence.txt 0.5")
        return

    input_path = sys.argv[1]
    minsup = float(sys.argv[2])

    db = MDSequenceDatabase()
    db.loadFile(input_path)

    algo = AlgoSeqDim()
    algo.runAlgorithm(db, minsup, "pythonout.txt")
    algo.printStatistics(db.size())
    print("Done. Output written to pythonout.txt")


if __name__ == "__main__":
    main()
