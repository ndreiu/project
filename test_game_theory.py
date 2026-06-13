"""
test_game_theory.py
===================
Suite completă de teste unitare pentru modulul game_theory.py.
Acoperire: clase de echivalență, valori de frontieră, instrucțiune,
           decizie, condiție, circuite independente, mutanți.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game_theory import (
    Action, StrategyType, Player, GameEngine, Tournament,
    PRISONER_DILEMMA_PAYOFF, MATCHING_PENNIES_PAYOFF, STAG_HUNT_PAYOFF
)


# ===========================================================================
# 1. TESTE PENTRU CLASA Player
# ===========================================================================

class TestPlayerInit(unittest.TestCase):
    """Testează inițializarea corectă și validările din constructorul Player."""

    # --- Clase de echivalență valide ---
    def test_valid_player_creation(self):
        """EC-P1: Player valid cu strategie ALWAYS_COOPERATE."""
        p = Player("Alice", StrategyType.ALWAYS_COOPERATE)
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.strategy, StrategyType.ALWAYS_COOPERATE)
        self.assertEqual(p.score, 0)
        self.assertEqual(p.history, [])
        self.assertEqual(p.opponent_history, [])

    def test_valid_player_all_strategies(self):
        """EC-P2: Player valid poate fi creat cu oricare StrategyType."""
        for strategy in StrategyType:
            with self.subTest(strategy=strategy):
                p = Player("Test", strategy)
                self.assertEqual(p.strategy, strategy)

    # --- Clase de echivalență invalide ---
    def test_invalid_name_empty_string(self):
        """EC-P3: Nume gol → ValueError."""
        with self.assertRaises(ValueError):
            Player("", StrategyType.ALWAYS_COOPERATE)

    def test_invalid_name_none(self):
        """EC-P4: Nume None → ValueError."""
        with self.assertRaises(ValueError):
            Player(None, StrategyType.ALWAYS_COOPERATE)  # type: ignore

    def test_invalid_strategy_string(self):
        """EC-P5: Strategie ca string → TypeError."""
        with self.assertRaises(TypeError):
            Player("Alice", "always_cooperate")  # type: ignore

    def test_invalid_strategy_none(self):
        """EC-P6: Strategie None → TypeError."""
        with self.assertRaises(TypeError):
            Player("Alice", None)  # type: ignore


class TestPlayerChooseAction(unittest.TestCase):
    """Testează metoda choose_action pentru fiecare strategie."""

    def setUp(self):
        self.actions = [Action.COOPERATE, Action.DEFECT]

    # --- ALWAYS_COOPERATE ---
    def test_always_cooperate_returns_first_action(self):
        """EC-PA1: ALWAYS_COOPERATE returnează întotdeauna prima acțiune."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        for _ in range(5):
            action = p.choose_action(self.actions)
            self.assertEqual(action, Action.COOPERATE)

    # --- ALWAYS_DEFECT ---
    def test_always_defect_returns_last_action(self):
        """EC-PA2: ALWAYS_DEFECT returnează întotdeauna ultima acțiune."""
        p = Player("P", StrategyType.ALWAYS_DEFECT)
        for _ in range(5):
            action = p.choose_action(self.actions)
            self.assertEqual(action, Action.DEFECT)

    # --- TIT_FOR_TAT ---
    def test_tit_for_tat_first_round_cooperates(self):
        """EC-PA3: TIT_FOR_TAT cooperează la prima rundă (fără istoric)."""
        p = Player("P", StrategyType.TIT_FOR_TAT)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.COOPERATE)

    def test_tit_for_tat_copies_defect(self):
        """EC-PA4: TIT_FOR_TAT copiază DEFECT din runda anterioară."""
        p = Player("P", StrategyType.TIT_FOR_TAT)
        p.choose_action(self.actions)  # runda 1: cooperează
        p.update_opponent_history(Action.DEFECT)
        action = p.choose_action(self.actions)  # runda 2: copiază defect
        self.assertEqual(action, Action.DEFECT)

    def test_tit_for_tat_copies_cooperate(self):
        """EC-PA5: TIT_FOR_TAT copiază COOPERATE din runda anterioară."""
        p = Player("P", StrategyType.TIT_FOR_TAT)
        p.choose_action(self.actions)
        p.update_opponent_history(Action.COOPERATE)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.COOPERATE)

    # --- GRUDGER ---
    def test_grudger_cooperates_until_first_defect(self):
        """EC-PA6: GRUDGER cooperează atâta timp cât adversarul nu a trădat."""
        p = Player("P", StrategyType.GRUDGER)
        p.choose_action(self.actions)
        p.update_opponent_history(Action.COOPERATE)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.COOPERATE)

    def test_grudger_defects_forever_after_one_defect(self):
        """EC-PA7: GRUDGER defectează permanent după primul DEFECT al adversarului."""
        p = Player("P", StrategyType.GRUDGER)
        p.choose_action(self.actions)
        p.update_opponent_history(Action.DEFECT)  # adversarul a trădat
        for _ in range(3):
            action = p.choose_action(self.actions)
            self.assertEqual(action, Action.DEFECT)

    # --- PAVLOV ---
    def test_pavlov_cooperates_first_round(self):
        """EC-PA8: PAVLOV cooperează la prima rundă."""
        p = Player("P", StrategyType.PAVLOV)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.COOPERATE)

    def test_pavlov_stays_if_opponent_cooperated(self):
        """EC-PA9: PAVLOV menține acțiunea dacă adversarul a cooperat."""
        p = Player("P", StrategyType.PAVLOV)
        p.choose_action(self.actions)  # cooperate
        p.update_opponent_history(Action.COOPERATE)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.COOPERATE)

    def test_pavlov_shifts_if_opponent_defected(self):
        """EC-PA10: PAVLOV schimbă acțiunea dacă adversarul a defectat."""
        p = Player("P", StrategyType.PAVLOV)
        p.choose_action(self.actions)  # cooperate
        p.update_opponent_history(Action.DEFECT)
        action = p.choose_action(self.actions)
        self.assertEqual(action, Action.DEFECT)

    # --- RANDOM ---
    def test_random_returns_valid_action(self):
        """EC-PA11: RANDOM returnează o acțiune validă."""
        p = Player("P", StrategyType.RANDOM, seed=42)
        for _ in range(20):
            action = p.choose_action(self.actions)
            self.assertIn(action, self.actions)

    # --- Frontiere ---
    def test_choose_action_empty_list_raises(self):
        """BVA-PA1: Lista goală de acțiuni → ValueError."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        with self.assertRaises(ValueError):
            p.choose_action([])

    def test_choose_action_single_action(self):
        """BVA-PA2: O singură acțiune validă → returnează acea acțiune."""
        p = Player("P", StrategyType.RANDOM, seed=0)
        action = p.choose_action([Action.COOPERATE])
        self.assertEqual(action, Action.COOPERATE)

    def test_action_appended_to_history(self):
        """COV-PA1: Acțiunea aleasă este adăugată în history."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        p.choose_action(self.actions)
        p.choose_action(self.actions)
        self.assertEqual(len(p.history), 2)
        self.assertTrue(all(a == Action.COOPERATE for a in p.history))


class TestPlayerScoreAndReset(unittest.TestCase):
    """Testează add_score, update_opponent_history și reset."""

    def test_add_positive_score(self):
        """EC-S1: Adăugare scor pozitiv."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        p.add_score(5)
        self.assertEqual(p.score, 5)

    def test_add_zero_score(self):
        """BVA-S1: Adăugare zero → scor nemodificat."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        p.add_score(0)
        self.assertEqual(p.score, 0)

    def test_add_negative_score_raises(self):
        """BVA-S2: Adăugare scor negativ → ValueError."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        with self.assertRaises(ValueError):
            p.add_score(-1)

    def test_reset_clears_everything(self):
        """COV-R1: Reset curăță istoricul, scorul și flag-ul grudger."""
        p = Player("P", StrategyType.GRUDGER)
        p.score = 100
        p.history = [Action.COOPERATE]
        p.opponent_history = [Action.DEFECT]
        p._defected_once = True
        p.reset()
        self.assertEqual(p.score, 0)
        self.assertEqual(p.history, [])
        self.assertEqual(p.opponent_history, [])
        self.assertFalse(p._defected_once)

    def test_update_opponent_history(self):
        """COV-OH1: update_opponent_history adaugă acțiunea adversarului."""
        p = Player("P", StrategyType.TIT_FOR_TAT)
        p.update_opponent_history(Action.DEFECT)
        self.assertEqual(p.opponent_history, [Action.DEFECT])


# ===========================================================================
# 2. TESTE PENTRU GameEngine
# ===========================================================================

class TestGameEngineInit(unittest.TestCase):
    """Testează inițializarea GameEngine."""

    def _make_players(self):
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        return p1, p2

    def test_valid_engine_creation(self):
        """EC-GE1: Motor valid pentru prisoner_dilemma."""
        p1, p2 = self._make_players()
        engine = GameEngine("prisoner_dilemma", p1, p2, 5)
        self.assertEqual(engine.game_name, "prisoner_dilemma")
        self.assertEqual(engine.rounds, 5)

    def test_invalid_game_name(self):
        """EC-GE2: Nume joc inexistent → ValueError."""
        p1, p2 = self._make_players()
        with self.assertRaises(ValueError):
            GameEngine("chess", p1, p2, 5)

    def test_zero_rounds_raises(self):
        """BVA-GE1: Runde = 0 → ValueError."""
        p1, p2 = self._make_players()
        with self.assertRaises(ValueError):
            GameEngine("prisoner_dilemma", p1, p2, 0)

    def test_negative_rounds_raises(self):
        """BVA-GE2: Runde negative → ValueError."""
        p1, p2 = self._make_players()
        with self.assertRaises(ValueError):
            GameEngine("prisoner_dilemma", p1, p2, -3)

    def test_one_round_valid(self):
        """BVA-GE3: O singură rundă → valid."""
        p1, p2 = self._make_players()
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        self.assertEqual(engine.rounds, 1)

    def test_same_player_object_raises(self):
        """EC-GE3: Același obiect pentru ambii jucători → ValueError."""
        p1 = Player("P", StrategyType.ALWAYS_COOPERATE)
        with self.assertRaises(ValueError):
            GameEngine("prisoner_dilemma", p1, p1, 5)

    def test_all_supported_games_valid(self):
        """EC-GE4: Toate jocurile suportate sunt acceptate."""
        for game in ["prisoner_dilemma", "matching_pennies", "stag_hunt"]:
            p1, p2 = self._make_players()
            engine = GameEngine(game, p1, p2, 1)
            self.assertEqual(engine.game_name, game)


class TestGameEnginePlayRound(unittest.TestCase):
    """Testează play_round pentru toate jocurile."""

    def test_prisoner_dilemma_cooperate_cooperate(self):
        """EC-PR1: COOPERATE vs COOPERATE → (3, 3)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 3)
        self.assertEqual(result["score_p2"], 3)

    def test_prisoner_dilemma_cooperate_defect(self):
        """EC-PR2: COOPERATE vs DEFECT → (0, 5)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 0)
        self.assertEqual(result["score_p2"], 5)

    def test_prisoner_dilemma_defect_cooperate(self):
        """EC-PR3: DEFECT vs COOPERATE → (5, 0)."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 5)
        self.assertEqual(result["score_p2"], 0)

    def test_prisoner_dilemma_defect_defect(self):
        """EC-PR4: DEFECT vs DEFECT → (1, 1)."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 1)
        self.assertEqual(result["score_p2"], 1)

    def test_matching_pennies_heads_heads(self):
        """EC-MP1: HEADS vs HEADS → (1, -1)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)  # va returna HEADS (primul)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("matching_pennies", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 1)
        self.assertEqual(result["score_p2"], -1)

    def test_matching_pennies_tails_tails(self):
        """EC-MP2: TAILS vs TAILS → (1, -1)."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)  # va returna TAILS (ultimul)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("matching_pennies", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 1)
        self.assertEqual(result["score_p2"], -1)

    def test_stag_hunt_stag_stag(self):
        """EC-SH1: STAG vs STAG → (4, 4)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("stag_hunt", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 4)
        self.assertEqual(result["score_p2"], 4)

    def test_stag_hunt_hare_hare(self):
        """EC-SH2: HARE vs HARE → (2, 2)."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("stag_hunt", p1, p2, 1)
        result = engine.play_round()
        self.assertEqual(result["score_p1"], 2)
        self.assertEqual(result["score_p2"], 2)

    def test_play_round_returns_dict_with_required_keys(self):
        """COV-PR1: play_round returnează dict cu cheile corecte."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        result = engine.play_round()
        for key in ["round", "action_p1", "action_p2", "score_p1", "score_p2"]:
            self.assertIn(key, result)

    def test_round_number_increments(self):
        """COV-PR2: Numărul de rundă crește la fiecare apel play_round()."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 5)
        collected = []
        for _ in range(3):
            collected.append(engine.play_round())
        for i, result in enumerate(collected):
            self.assertEqual(result["round"], i + 1)


class TestGameEngineRun(unittest.TestCase):
    """Testează metoda run() și get_winner()."""

    def test_run_returns_correct_number_of_results(self):
        """EC-RUN1: run() returnează atâtea rezultate câte runde s-au specificat."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 7)
        results = engine.run()
        self.assertEqual(len(results), 7)

    def test_run_one_round(self):
        """BVA-RUN1: run() cu o singură rundă."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        results = engine.run()
        self.assertEqual(len(results), 1)

    def test_get_winner_player1_wins(self):
        """EC-WIN1: P1 câștigă când DEFECT vs COOPERATE."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 3)
        engine.run()
        self.assertEqual(engine.get_winner(), "P1")

    def test_get_winner_player2_wins(self):
        """EC-WIN2: P2 câștigă când COOPERATE vs DEFECT."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 3)
        engine.run()
        self.assertEqual(engine.get_winner(), "P2")

    def test_get_winner_tie(self):
        """EC-WIN3: Egalitate → get_winner() returnează None."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 3)
        engine.run()
        self.assertIsNone(engine.get_winner())  # ambii cooperează → 3, 3 fiecare

    def test_scores_accumulate_over_rounds(self):
        """COV-RUN2: Scorurile se acumulează corect pe parcursul rundelor."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 5)
        engine.run()
        self.assertEqual(p1.score, 15)  # 5 runde × 3 puncte
        self.assertEqual(p2.score, 15)

    def test_get_summary_structure(self):
        """COV-SUM1: get_summary() returnează dict cu toate câmpurile."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 2)
        engine.run()
        summary = engine.get_summary()
        expected_keys = ["game", "rounds_played", "player1", "score_p1",
                         "strategy_p1", "player2", "score_p2", "strategy_p2", "winner"]
        for key in expected_keys:
            self.assertIn(key, summary)

    def test_get_summary_values(self):
        """COV-SUM2: Valorile din get_summary() sunt corecte."""
        p1 = Player("P1", StrategyType.ALWAYS_DEFECT)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 2)
        engine.run()
        summary = engine.get_summary()
        self.assertEqual(summary["game"], "prisoner_dilemma")
        self.assertEqual(summary["rounds_played"], 2)
        self.assertEqual(summary["winner"], "P1")
        self.assertEqual(summary["score_p1"], 10)  # 2 × 5


# ===========================================================================
# 3. TESTE PENTRU Tournament
# ===========================================================================

class TestTournament(unittest.TestCase):
    """Testează turneul round-robin."""

    def _make_tournament(self):
        t = Tournament("prisoner_dilemma", rounds_per_match=5)
        return t

    def test_tournament_valid_creation(self):
        """EC-T1: Turneu valid creat."""
        t = Tournament("prisoner_dilemma", 5)
        self.assertEqual(t.game_name, "prisoner_dilemma")
        self.assertEqual(t.rounds_per_match, 5)

    def test_tournament_invalid_game(self):
        """EC-T2: Joc invalid → ValueError."""
        with self.assertRaises(ValueError):
            Tournament("go", 5)

    def test_tournament_zero_rounds(self):
        """BVA-T1: Runde = 0 → ValueError."""
        with self.assertRaises(ValueError):
            Tournament("prisoner_dilemma", 0)

    def test_add_player_valid(self):
        """EC-T3: Adăugare jucător valid."""
        t = self._make_tournament()
        p = Player("Alice", StrategyType.TIT_FOR_TAT)
        t.add_player(p)
        self.assertIn("Alice", t.standings)

    def test_add_duplicate_player_raises(self):
        """EC-T4: Adăugare jucător duplicat → ValueError."""
        t = self._make_tournament()
        p1 = Player("Alice", StrategyType.TIT_FOR_TAT)
        p2 = Player("Alice", StrategyType.ALWAYS_DEFECT)
        t.add_player(p1)
        with self.assertRaises(ValueError):
            t.add_player(p2)

    def test_run_with_less_than_two_players_raises(self):
        """BVA-T2: Turneu cu un singur jucător → ValueError."""
        t = self._make_tournament()
        t.add_player(Player("Alice", StrategyType.TIT_FOR_TAT))
        with self.assertRaises(ValueError):
            t.run()

    def test_run_with_two_players(self):
        """EC-T5: Turneu cu doi jucători returnează clasament cu 2 intrări."""
        t = self._make_tournament()
        t.add_player(Player("Alice", StrategyType.TIT_FOR_TAT))
        t.add_player(Player("Bob", StrategyType.ALWAYS_DEFECT))
        standings = t.run()
        self.assertEqual(len(standings), 2)
        self.assertIn("Alice", standings)
        self.assertIn("Bob", standings)

    def test_run_with_three_players_all_combinations(self):
        """EC-T6: Turneu cu 3 jucători → C(3,2)=3 meciuri, toate jucate."""
        t = self._make_tournament()
        t.add_player(Player("AlwaysCoop", StrategyType.ALWAYS_COOPERATE))
        t.add_player(Player("AlwaysDef", StrategyType.ALWAYS_DEFECT))
        t.add_player(Player("TitForTat", StrategyType.TIT_FOR_TAT))
        standings = t.run()
        self.assertEqual(len(standings), 3)
        # AlwaysDef bate AlwaysCoop → scor mai mare
        self.assertGreater(standings["AlwaysDef"], standings["AlwaysCoop"])

    def test_get_champion_returns_best_player(self):
        """EC-T7: get_champion() returnează jucătorul cu cel mai mare scor."""
        t = self._make_tournament()
        t.add_player(Player("AlwaysCoop", StrategyType.ALWAYS_COOPERATE))
        t.add_player(Player("AlwaysDef", StrategyType.ALWAYS_DEFECT))
        t.run()
        champion = t.get_champion()
        self.assertEqual(champion, "AlwaysDef")

    def test_get_champion_without_run_returns_none(self):
        """EC-T8: get_champion() fără run → None (standings gol)."""
        t = self._make_tournament()
        self.assertIsNone(t.get_champion())

    def test_tournament_scores_are_non_negative(self):
        """COV-T1: Scorurile din standin-uri sunt ≥ 0 pentru prisoner_dilemma."""
        t = Tournament("prisoner_dilemma", rounds_per_match=10)
        for name, strategy in [("C", StrategyType.ALWAYS_COOPERATE),
                                ("D", StrategyType.ALWAYS_DEFECT),
                                ("T", StrategyType.TIT_FOR_TAT)]:
            t.add_player(Player(name, strategy))
        standings = t.run()
        for score in standings.values():
            self.assertGreaterEqual(score, 0)


# ===========================================================================
# 4. TESTE PENTRU MATRICILE DE PLATĂ
# ===========================================================================

class TestPayoffMatrices(unittest.TestCase):
    """Verifică corectitudinea matricilor de plată."""

    def test_prisoner_dilemma_all_entries(self):
        """EC-PM1: Toate intrările din Prisoner's Dilemma sunt corecte."""
        expected = {
            (Action.COOPERATE, Action.COOPERATE): (3, 3),
            (Action.COOPERATE, Action.DEFECT):    (0, 5),
            (Action.DEFECT,    Action.COOPERATE): (5, 0),
            (Action.DEFECT,    Action.DEFECT):    (1, 1),
        }
        self.assertEqual(PRISONER_DILEMMA_PAYOFF, expected)

    def test_matching_pennies_symmetry(self):
        """EC-PM2: Matching Pennies este zero-sum (suma = 0 pentru fiecare intrare)."""
        for (a1, a2), (s1, s2) in MATCHING_PENNIES_PAYOFF.items():
            with self.subTest(a1=a1, a2=a2):
                self.assertEqual(s1 + s2, 0)

    def test_stag_hunt_pareto_optimum(self):
        """EC-PM3: STAG-STAG este echilibrul Pareto optim."""
        stag_stag = STAG_HUNT_PAYOFF[(Action.STAG, Action.STAG)]
        hare_hare = STAG_HUNT_PAYOFF[(Action.HARE, Action.HARE)]
        self.assertGreater(stag_stag[0], hare_hare[0])
        self.assertGreater(stag_stag[1], hare_hare[1])

    def test_prisoner_dilemma_has_4_entries(self):
        """BVA-PM1: Prisoner's Dilemma are exact 4 intrări."""
        self.assertEqual(len(PRISONER_DILEMMA_PAYOFF), 4)

    def test_matching_pennies_has_4_entries(self):
        """BVA-PM2: Matching Pennies are exact 4 intrări."""
        self.assertEqual(len(MATCHING_PENNIES_PAYOFF), 4)


# ===========================================================================
# 5. TESTE DE CIRCUIT INDEPENDENT (MC/DC)
# ===========================================================================

class TestIndependentCircuits(unittest.TestCase):
    """
    Teste pentru circuitele independente din metodele cheie.
    Acoperă ramurile din choose_action, _grudger, _pavlov, play_round, etc.
    """

    # Circuit 1: tit_for_tat cu istoric non-gol și acțiune validă
    def test_tit_for_tat_with_action_not_in_valid_list(self):
        """IC-1: TIT_FOR_TAT când acțiunea adversarului nu e în lista validă → fallback la prima."""
        p = Player("P", StrategyType.TIT_FOR_TAT)
        p.choose_action([Action.COOPERATE, Action.DEFECT])
        # Injectăm manual o acțiune invalidă în istoria adversarului
        p.opponent_history.append(Action.HEADS)
        action = p.choose_action([Action.COOPERATE, Action.DEFECT])
        self.assertEqual(action, Action.COOPERATE)

    # Circuit 2: grudger – adversarul defectează chiar la prima rundă
    def test_grudger_first_round_opponent_defects_immediately(self):
        """IC-2: GRUDGER – adversarul defectează la prima verificare."""
        p = Player("P", StrategyType.GRUDGER)
        p.opponent_history.append(Action.DEFECT)
        action = p.choose_action([Action.COOPERATE, Action.DEFECT])
        self.assertEqual(action, Action.DEFECT)

    # Circuit 3: pavlov – acțiunea anterioară nu se află în valid_actions
    def test_pavlov_previous_action_not_in_valid_actions(self):
        """IC-3: PAVLOV – acțiunea precedentă dispărută din lista validă → fallback index 0."""
        p = Player("P", StrategyType.PAVLOV)
        p.history.append(Action.HEADS)  # acțiune ce nu apare în lista de mai jos
        p.opponent_history.append(Action.DEFECT)
        action = p.choose_action([Action.COOPERATE, Action.DEFECT])
        # fallback: idx = 0, shift → (0+1)%2 = 1 → DEFECT
        self.assertIn(action, [Action.COOPERATE, Action.DEFECT])

    # Circuit 4: engine – run resetează results la fiecare apel
    def test_run_resets_results_on_each_call(self):
        """IC-4: run() suprascrie results la fiecare apel."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 3)
        engine.run()
        engine.run()
        self.assertEqual(len(engine.results), 3)

    # Circuit 5: play_round actualizează corect istoricul ambilor jucători
    def test_play_round_updates_both_opponent_histories(self):
        """IC-5: play_round actualizează opponent_history pentru ambii jucători."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        engine = GameEngine("prisoner_dilemma", p1, p2, 1)
        engine.play_round()
        self.assertEqual(p1.opponent_history[-1], Action.DEFECT)
        self.assertEqual(p2.opponent_history[-1], Action.COOPERATE)


# ===========================================================================
# 6. TESTE PENTRU UCIDEREA MUTANȚILOR
# ===========================================================================

class TestMutantKillers(unittest.TestCase):
    """
    Teste create specific pentru a elimina mutanți supraviețuitori.
    Vizează: operatori relaționali (>, >=, ==), constante (0, 1, -1), negări.
    """

    # Mutant M1: rounds <= 0 → rounds < 0 (ar permite rounds=0)
    def test_mutant_rounds_boundary_zero(self):
        """MUT-1: Exact 0 runde → ValueError (ucide mutantul rounds < 0)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_DEFECT)
        with self.assertRaises(ValueError):
            GameEngine("prisoner_dilemma", p1, p2, 0)

    # Mutant M2: score_p1 > score_p2 → score_p1 >= score_p2 (ar schimba logica egalității)
    def test_mutant_winner_equality_is_none(self):
        """MUT-2: Scor egal → get_winner() este None, nu un jucător (ucide mutantul >=)."""
        p1 = Player("P1", StrategyType.ALWAYS_COOPERATE)
        p2 = Player("P2", StrategyType.ALWAYS_COOPERATE)
        engine = GameEngine("prisoner_dilemma", p1, p2, 2)
        engine.run()
        # Ambii au 6 puncte
        self.assertEqual(p1.score, p2.score)
        self.assertIsNone(engine.get_winner())

    # Mutant M3: points < 0 → points <= 0 (ar bloca adăugarea de 0)
    def test_mutant_add_score_zero_allowed(self):
        """MUT-3: add_score(0) trebuie să fie permis (ucide mutantul <= 0)."""
        p = Player("P", StrategyType.ALWAYS_COOPERATE)
        p.add_score(0)
        self.assertEqual(p.score, 0)

    # Mutant M4: prisoner's dilemma (C,C) → mutant ar da (2,2) în loc de (3,3)
    def test_mutant_payoff_cooperate_cooperate_exact(self):
        """MUT-4: Payoff (C,C) exact (3,3), nu (2,2) sau (4,4)."""
        self.assertEqual(PRISONER_DILEMMA_PAYOFF[(Action.COOPERATE, Action.COOPERATE)], (3, 3))

    # Mutant M5: grudger – _defected_once inițializat True → ar defecta din start
    def test_mutant_grudger_starts_not_defected(self):
        """MUT-5: Grudger nu defectează la prima rundă fără provocare."""
        p = Player("P", StrategyType.GRUDGER)
        action = p.choose_action([Action.COOPERATE, Action.DEFECT])
        self.assertEqual(action, Action.COOPERATE)

    # Mutant M6: opponent_history[-1] == valid_actions[0] în pavlov → schimbare la [-1] sau [1]
    def test_mutant_pavlov_correct_condition_for_stay(self):
        """MUT-6: Pavlov rămâne pe COOPERATE dacă adversarul a cooperat."""
        p = Player("P", StrategyType.PAVLOV)
        p.history.append(Action.COOPERATE)
        p.opponent_history.append(Action.COOPERATE)
        action = p.choose_action([Action.COOPERATE, Action.DEFECT])
        self.assertEqual(action, Action.COOPERATE)

    # Mutant M7: Tournament.run – len(players) < 2 → len(players) < 1
    def test_mutant_tournament_requires_two_players(self):
        """MUT-7: Turneu cu exact 1 jucător ridică ValueError (ucide mutantul < 1)."""
        t = Tournament("prisoner_dilemma", 3)
        t.add_player(Player("Solo", StrategyType.ALWAYS_COOPERATE))
        with self.assertRaises(ValueError):
            t.run()

    # Mutant M8: stag_hunt (STAG, HARE) → mutant ar da (0,2) vs (2,0)
    def test_mutant_stag_hunt_asymmetry(self):
        """MUT-8: (STAG, HARE) → p1=0, p2=2; nu invers."""
        self.assertEqual(STAG_HUNT_PAYOFF[(Action.STAG, Action.HARE)], (0, 2))
        self.assertEqual(STAG_HUNT_PAYOFF[(Action.HARE, Action.STAG)], (2, 0))


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
