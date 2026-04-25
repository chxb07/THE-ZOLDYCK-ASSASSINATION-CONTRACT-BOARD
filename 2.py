import json
import random
import math
from collections import defaultdict

random.seed(42)

# ======================
# DATA MODELS
# ======================

class Contract:
    def __init__(self, d):
        self.id = d["id"]
        self.city = d["city"]
        self.gold = d["gold"]
        self.deadline = d["deadline"]
        self.duration = d["duration"]
        self.skills = d["required_skills"]
        self.trap = d.get("trap", False)
        self.complication = d.get("complication", False)

class State:
    def __init__(self, profile):
        self.day = 0
        self.city = profile["start_city"]
        self.skills = profile["skills"].copy()
        self.gold = 0
        self.rep_penalty = 0
        self.active = []
        self.completed = []
        self.log = []
        self.skill_log = []

# ======================
# UTIL
# ======================

def dist(a, b, graph):
    return graph[a][b]

def can_do(contract, skills):
    for k, v in contract.skills.items():
        if skills.get(k, 0) < v:
            return False
    return True

def score(contract, state, graph):
    t = dist(state.city, contract.city, graph) + contract.duration
    if t <= 0:
        return 0
    risk = 1.0
    if contract.trap:
        risk *= 0.6
    if contract.complication:
        risk *= 0.8
    urgency = max(1, contract.deadline - state.day)
    return (contract.gold * risk) / (t * (1 + 1/urgency))

def apply_rep_penalty(gold, penalty):
    return gold * ((0.9) ** penalty)

# ======================
# CORE LOGIC
# ======================

def pick_contracts(available, state, graph):
    valid = [c for c in available if can_do(c, state.skills)]
    valid.sort(key=lambda c: score(c, state, graph), reverse=True)
    return valid[:5]

def travel_days(a, b, graph):
    return graph[a][b]

def execute(contract, state):
    dur = contract.duration
    if contract.complication and random.random() < 0.2:
        dur = int(dur * 1.5)

    for _ in range(dur):
        state.day += 1
        state.log.append(f"Day {state.day}: Executing contract {contract.id}")

    earned = apply_rep_penalty(contract.gold, state.rep_penalty)
    state.gold += earned
    state.completed.append(contract.id)

    for s in contract.skills:
        state.skills[s] = state.skills.get(s, 0) + 1
        state.skill_log.append(f"Day {state.day}: {s}+1")

def travel(to_city, state, graph):
    d = travel_days(state.city, to_city, graph)
    for _ in range(d):
        state.day += 1
        state.log.append(f"Day {state.day}: Traveling to {to_city}")
    state.city = to_city

def simulate(contracts, graph, profile):
    state = State(profile)
    remaining = contracts[:]

    while state.day < 200 and remaining:
        available = [c for c in remaining if c.deadline > state.day]

        if not available:
            break

        chosen = pick_contracts(available, state, graph)

        if not chosen:
            state.day += 1
            continue

        c = chosen[0]

        if c.trap:
            state.rep_penalty += 1
            state.log.append(f"Day {state.day}: Abandoned trap {c.id}")
            remaining.remove(c)
            continue

        if state.city != c.city:
            travel(c.city, state, graph)

        if state.day > c.deadline:
            state.rep_penalty += 1
            state.log.append(f"Day {state.day}: Failed {c.id}")
            remaining.remove(c)
            continue

        execute(c, state)
        remaining.remove(c)

    return state

# ======================
# IO
# ======================

def load_contracts(path):
    with open(path) as f:
        data = json.load(f)
    return [Contract(x) for x in data]

def load_map(path):
    with open(path) as f:
        return json.load(f)

def load_profile(path):
    with open(path) as f:
        return json.load(f)

def save_report(state):
    with open("optimal_path.txt", "w") as f:
        for line in state.log:
            f.write(line + "\n")
        f.write(f"\nTotal Gold: {state.gold}\n")

    with open("skill_log.txt", "w") as f:
        for line in state.skill_log:
            f.write(line + "\n")

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    contracts = load_contracts("contracts.json")
    graph = load_map("map.json")
    profile = load_profile("profile.json")

    state = simulate(contracts, graph, profile)

    print("Total Gold:", state.gold)
    print("Completed:", len(state.completed))

    save_report(state)