# src/dfa.py
import json

class DFA:
    def __init__(self, states, alphabet, transitions, start, accepting):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions  # dict: {state: {symbol: state}}
        self.start = start
        self.accepting = set(accepting)

    @classmethod
    def from_json(cls, path):
        with open(path) as f:
            data = json.load(f)
        return cls(
            data["states"],
            data["alphabet"],
            data["transitions"],
            data["start"],
            data["accepting"]
        )

    def step(self, state, symbol):
        """One transition: δ(state, symbol)"""
        return self.transitions[state][symbol]

    def run(self, word):
        """Extended transition: δ̂(q0, word). Returns final state."""
        state = self.start
        for symbol in word:
            state = self.step(state, symbol)
        return state

    def accepts(self, word):
        """Returns True if word is accepted."""
        return self.run(word) in self.accepting

    def transformation(self, word):
        """
        Returns f_w: Q -> Q as a dict.
        f_w(q) = the state reached from q after reading word.
        """
        return {state: self.run_from(state, word) for state in self.states}

    def run_from(self, start_state, word):
        """Run word starting from a specific state (not necessarily q0)."""
        state = start_state
        for symbol in word:
            state = self.step(state, symbol)
        return state
