# src/algebra.py

class SyntacticMonoid:
    def __init__(self, dfa):
        self.dfa = dfa
        self.elements = []       # list of dicts {state: state}, each is a transformation
        self.generators = {}     # symbol -> transformation
        self.word_map = {}       # word (str) -> transformation (as tuple, for hashing)
        self._compute()

    def _transformation_to_key(self, t):
        """Convert a transformation dict to a hashable tuple."""
        return tuple(sorted(t.items()))

    def _compute(self):
        """
        BFS over words to find all distinct transformations.
        Starts from the identity (empty word) and applies each symbol.
        """
        identity = {s: s for s in self.dfa.states}
        seen = {self._transformation_to_key(identity): identity}
        queue = [("", identity)]
        self.word_map[""] = identity

        while queue:
            word, transformation = queue.pop(0)
            for symbol in sorted(self.dfa.alphabet):
                new_word = word + symbol
                # Compose: first apply transformation, then apply symbol
                new_t = {
                    s: self.dfa.step(transformation[s], symbol)
                    for s in self.dfa.states
                }
                key = self._transformation_to_key(new_t)
                if key not in seen:
                    seen[key] = new_t
                    queue.append((new_word, new_t))
                self.word_map[new_word] = new_t

        self.elements = list(seen.values())

    def compose(self, f, g):
        """Compose two transformations: (f then g)(q) = g(f(q))."""
        return {s: g[f[s]] for s in self.dfa.states}

    def cayley_table(self):
        """Returns the Cayley table as a list of lists (indices into self.elements)."""
        n = len(self.elements)
        table = []
        for i, f in enumerate(self.elements):
            row = []
            for j, g in enumerate(self.elements):
                result = self.compose(f, g)
                key = self._transformation_to_key(result)
                idx = next(
                    k for k, e in enumerate(self.elements)
                    if self._transformation_to_key(e) == key
                )
                row.append(idx)
            table.append(row)
        return table

    def syntactic_congruence_classes(self):
        """
        Groups words (up to some length) by the transformation they induce.
        Returns a list of lists of words.
        """
        from collections import defaultdict
        groups = defaultdict(list)
        for word, t in self.word_map.items():
            groups[self._transformation_to_key(t)].append(word)
        return list(groups.values())

    def is_group(self):
        """Returns True if every element has an inverse (i.e., M(A) is a group)."""
        identity_key = self._transformation_to_key({s: s for s in self.dfa.states})
        for f in self.elements:
            has_inverse = False
            for g in self.elements:
                composed = self.compose(f, g)
                if self._transformation_to_key(composed) == identity_key:
                    has_inverse = True
                    break
            if not has_inverse:
                return False
        return True
