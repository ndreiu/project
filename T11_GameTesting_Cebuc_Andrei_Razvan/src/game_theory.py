"""
game_theory.py
==============
Modul pentru simularea jocurilor bazate pe decizii utilizând concepte din teoria jocurilor.
Implementează: Prisoner's Dilemma, Matching Pennies, Stag Hunt, și motorul general de strategii.
"""

from enum import Enum
from typing import List, Tuple, Dict, Optional
import random


# ---------------------------------------------------------------------------
# Tipuri de acțiuni / strategii
# ---------------------------------------------------------------------------

class Action(Enum):
    COOPERATE = "cooperate"
    DEFECT = "defect"
    HEADS = "heads"
    TAILS = "tails"
    STAG = "stag"
    HARE = "hare"


class StrategyType(Enum):
    ALWAYS_COOPERATE = "always_cooperate"
    ALWAYS_DEFECT = "always_defect"
    TIT_FOR_TAT = "tit_for_tat"
    RANDOM = "random"
    GRUDGER = "grudger"
    PAVLOV = "pavlov"


# ---------------------------------------------------------------------------
# Matrici de plată (payoff matrices)
# ---------------------------------------------------------------------------

PRISONER_DILEMMA_PAYOFF: Dict[Tuple[Action, Action], Tuple[int, int]] = {
    (Action.COOPERATE, Action.COOPERATE): (3, 3),
    (Action.COOPERATE, Action.DEFECT):    (0, 5),
    (Action.DEFECT,    Action.COOPERATE): (5, 0),
    (Action.DEFECT,    Action.DEFECT):    (1, 1),
}

MATCHING_PENNIES_PAYOFF: Dict[Tuple[Action, Action], Tuple[int, int]] = {
    (Action.HEADS, Action.HEADS): (1, -1),
    (Action.HEADS, Action.TAILS): (-1, 1),
    (Action.TAILS, Action.HEADS): (-1, 1),
    (Action.TAILS, Action.TAILS): (1, -1),
}

STAG_HUNT_PAYOFF: Dict[Tuple[Action, Action], Tuple[int, int]] = {
    (Action.STAG, Action.STAG):   (4, 4),
    (Action.STAG, Action.HARE):   (0, 2),
    (Action.HARE, Action.STAG):   (2, 0),
    (Action.HARE, Action.HARE):   (2, 2),
}


# ---------------------------------------------------------------------------
# Clasa Player (Jucător cu strategie)
# ---------------------------------------------------------------------------

class Player:
    """Reprezintă un jucător cu o strategie fixă sau adaptivă."""

    def __init__(self, name: str, strategy: StrategyType, seed: Optional[int] = None):
        if not name or not isinstance(name, str):
            raise ValueError("Numele jucătorului trebuie să fie un string nevid.")
        if not isinstance(strategy, StrategyType):
            raise TypeError("Strategia trebuie să fie de tip StrategyType.")

        self.name = name
        self.strategy = strategy
        self.history: List[Action] = []          # acțiunile proprii
        self.opponent_history: List[Action] = [] # acțiunile adversarului
        self.score: int = 0
        self._defected_once = False              # pentru Grudger
        self._rng = random.Random(seed)

    def choose_action(self, valid_actions: List[Action]) -> Action:
        """Alege acțiunea conform strategiei curente."""
        if not valid_actions:
            raise ValueError("Lista de acțiuni valide nu poate fi goală.")

        strategy_map = {
            StrategyType.ALWAYS_COOPERATE: self._always_cooperate,
            StrategyType.ALWAYS_DEFECT:    self._always_defect,
            StrategyType.TIT_FOR_TAT:      self._tit_for_tat,
            StrategyType.RANDOM:           self._random,
            StrategyType.GRUDGER:          self._grudger,
            StrategyType.PAVLOV:           self._pavlov,
        }
        action = strategy_map[self.strategy](valid_actions)
        self.history.append(action)
        return action

    # -- strategii interne --

    def _always_cooperate(self, valid_actions: List[Action]) -> Action:
        return valid_actions[0]

    def _always_defect(self, valid_actions: List[Action]) -> Action:
        return valid_actions[-1]

    def _tit_for_tat(self, valid_actions: List[Action]) -> Action:
        if not self.opponent_history:
            return valid_actions[0]
        return self.opponent_history[-1] if self.opponent_history[-1] in valid_actions else valid_actions[0]

    def _random(self, valid_actions: List[Action]) -> Action:
        return self._rng.choice(valid_actions)

    def _grudger(self, valid_actions: List[Action]) -> Action:
        if self.opponent_history and self.opponent_history[-1] == valid_actions[-1]:
            self._defected_once = True
        if self._defected_once:
            return valid_actions[-1]
        return valid_actions[0]

    def _pavlov(self, valid_actions: List[Action]) -> Action:
        """Win-Stay, Lose-Shift."""
        if not self.history:
            return valid_actions[0]
        last_action = self.history[-1]
        # dacă am cooperat și adversarul a cooperat → repetă; altfel schimbă
        if self.opponent_history and self.opponent_history[-1] == valid_actions[0]:
            return last_action
        # schimbă acțiunea
        idx = valid_actions.index(last_action) if last_action in valid_actions else 0
        return valid_actions[(idx + 1) % len(valid_actions)]

    def update_opponent_history(self, opponent_action: Action) -> None:
        self.opponent_history.append(opponent_action)

    def add_score(self, points: int) -> None:
        if points < 0:
            raise ValueError("Punctele adăugate nu pot fi negative.")
        self.score += points

    def reset(self) -> None:
        self.history.clear()
        self.opponent_history.clear()
        self.score = 0
        self._defected_once = False


# ---------------------------------------------------------------------------
# Motor de joc (GameEngine)
# ---------------------------------------------------------------------------

class GameEngine:
    """
    Motorul care rulează un joc între doi jucători pentru un număr de runde.
    Suportă orice matrice de plată compatibilă cu perechile de acțiuni.
    """

    SUPPORTED_GAMES = {
        "prisoner_dilemma": {
            "payoff": PRISONER_DILEMMA_PAYOFF,
            "actions": [Action.COOPERATE, Action.DEFECT],
        },
        "matching_pennies": {
            "payoff": MATCHING_PENNIES_PAYOFF,
            "actions": [Action.HEADS, Action.TAILS],
        },
        "stag_hunt": {
            "payoff": STAG_HUNT_PAYOFF,
            "actions": [Action.STAG, Action.HARE],
        },
    }

    def __init__(self, game_name: str, player1: Player, player2: Player, rounds: int):
        if game_name not in self.SUPPORTED_GAMES:
            raise ValueError(f"Jocul '{game_name}' nu este suportat. "
                             f"Alegeți din: {list(self.SUPPORTED_GAMES.keys())}")
        if rounds <= 0:
            raise ValueError("Numărul de runde trebuie să fie pozitiv.")
        if player1 is player2:
            raise ValueError("Cei doi jucători trebuie să fie obiecte diferite.")

        self.game_name = game_name
        self.player1 = player1
        self.player2 = player2
        self.rounds = rounds
        self._config = self.SUPPORTED_GAMES[game_name]
        self.results: List[Dict] = []

    def play_round(self) -> Dict:
        """Joacă o singură rundă și returnează rezultatul."""
        # tracked separately from self.results (which is set only by run())
        if not hasattr(self, "_round_counter"):
            self._round_counter = 0
        self._round_counter += 1
        """Joacă o singură rundă și returnează rezultatul."""
        valid_actions = self._config["actions"]
        payoff = self._config["payoff"]

        a1 = self.player1.choose_action(valid_actions)
        a2 = self.player2.choose_action(valid_actions)

        self.player1.update_opponent_history(a2)
        self.player2.update_opponent_history(a1)

        score1, score2 = payoff[(a1, a2)]

        # Matching Pennies poate da scoruri negative → nu folosim add_score
        self.player1.score += score1
        self.player2.score += score2

        return {
            "round": self._round_counter,
            "action_p1": a1,
            "action_p2": a2,
            "score_p1": score1,
            "score_p2": score2,
        }

    def run(self) -> List[Dict]:
        """Rulează toate rundele și returnează lista de rezultate."""
        self.results = []
        self._round_counter = 0
        for _ in range(self.rounds):
            self.results.append(self.play_round())
        return self.results

    def get_winner(self) -> Optional[str]:
        """Returnează numele câștigătorului sau None la egalitate."""
        if self.player1.score > self.player2.score:
            return self.player1.name
        if self.player2.score > self.player1.score:
            return self.player2.name
        return None  # egalitate

    def get_summary(self) -> Dict:
        """Returnează un sumar al jocului."""
        return {
            "game": self.game_name,
            "rounds_played": len(self.results),
            "player1": self.player1.name,
            "score_p1": self.player1.score,
            "strategy_p1": self.player1.strategy.value,
            "player2": self.player2.name,
            "score_p2": self.player2.score,
            "strategy_p2": self.player2.strategy.value,
            "winner": self.get_winner(),
        }


# ---------------------------------------------------------------------------
# Tournament (turneu între mai mulți jucători)
# ---------------------------------------------------------------------------

class Tournament:
    """
    Organizează un turneu round-robin între o listă de jucători.
    Fiecare pereche joacă același număr de runde.
    """

    def __init__(self, game_name: str, rounds_per_match: int = 10):
        if game_name not in GameEngine.SUPPORTED_GAMES:
            raise ValueError(f"Jocul '{game_name}' nu este suportat.")
        if rounds_per_match <= 0:
            raise ValueError("rounds_per_match trebuie să fie pozitiv.")
        self.game_name = game_name
        self.rounds_per_match = rounds_per_match
        self.players: List[Player] = []
        self.standings: Dict[str, int] = {}

    def add_player(self, player: Player) -> None:
        for p in self.players:
            if p.name == player.name:
                raise ValueError(f"Jucătorul '{player.name}' este deja în turneu.")
        self.players.append(player)
        self.standings[player.name] = 0

    def run(self) -> Dict[str, int]:
        """Rulează turneul și returnează clasamentul final (scor cumulat)."""
        if len(self.players) < 2:
            raise ValueError("Turneul necesită cel puțin 2 jucători.")

        self.standings = {p.name: 0 for p in self.players}

        for i in range(len(self.players)):
            for j in range(i + 1, len(self.players)):
                p1 = self.players[i]
                p2 = self.players[j]
                p1.reset()
                p2.reset()
                engine = GameEngine(self.game_name, p1, p2, self.rounds_per_match)
                engine.run()
                self.standings[p1.name] += p1.score
                self.standings[p2.name] += p2.score

        return self.standings

    def get_champion(self) -> Optional[str]:
        """Returnează jucătorul cu cel mai mare scor total."""
        if not self.standings:
            return None
        return max(self.standings, key=lambda name: self.standings[name])
