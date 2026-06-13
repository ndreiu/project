# T11 – Analiza și testarea strategiilor în jocuri bazate pe decizii

**Disciplina:** Testarea Sistemelor Software  
**Tema:** T11 – Analiza și testarea strategiilor în jocuri bazate pe decizii  
**Limbaj:** Python 3  
**Framework testare:** `unittest` (biblioteca standard Python)

---

## Cuprins

1. [Descriere generală](#1-descriere-generală)
2. [Arhitectura sistemului](#2-arhitectura-sistemului)
3. [Configurare hardware și software](#3-configurare-hardware-și-software)
4. [Instalare și rulare](#4-instalare-și-rulare)
5. [Strategii de testare](#5-strategii-de-testare)
   - 5.1 [Partiționare în clase de echivalență](#51-partiționare-în-clase-de-echivalență)
   - 5.2 [Analiza valorilor de frontieră](#52-analiza-valorilor-de-frontieră)
   - 5.3 [Acoperire la nivel de instrucțiune](#53-acoperire-la-nivel-de-instrucțiune)
   - 5.4 [Acoperire la nivel de decizie](#54-acoperire-la-nivel-de-decizie)
   - 5.5 [Acoperire la nivel de condiție](#55-acoperire-la-nivel-de-condiție)
   - 5.6 [Circuite independente (MC/DC)](#56-circuite-independente-mcdc)
   - 5.7 [Testare bazată pe mutanți](#57-testare-bazată-pe-mutanți)
6. [Diagrame](#6-diagrame)
7. [Rezultatele rulării testelor](#7-rezultatele-rulării-testelor)
8. [Raport folosire tool AI (Claude)](#8-raport-folosire-tool-ai-claude)
9. [Referințe bibliografice](#9-referințe-bibliografice)

---

## 1. Descriere generală

Proiectul implementează un sistem de simulare a jocurilor bazate pe decizii, folosind concepte fundamentale din **teoria jocurilor** [1]. Sunt implementate trei jocuri clasice:

| Joc | Tip | Echilibru Nash | Optim Pareto |
|---|---|---|---|
| **Prisoner's Dilemma** | Sumă non-zero | (DEFECT, DEFECT) | (COOPERATE, COOPERATE) |
| **Matching Pennies** | Sumă zero | Amestecat (50/50) | Nu există (zero-sum) |
| **Stag Hunt** | Coordonare | (STAG, STAG) sau (HARE, HARE) | (STAG, STAG) |

Sistemul cuprinde:

- **`Player`** – jucător cu strategie fixă sau adaptivă (ALWAYS_COOPERATE, ALWAYS_DEFECT, TIT_FOR_TAT, RANDOM, GRUDGER, PAVLOV)
- **`GameEngine`** – motor care execută un meci între doi jucători pentru N runde
- **`Tournament`** – turneu round-robin între mai mulți jucători

---

## 2. Arhitectura sistemului

### 2.1 Diagrama claselor

```
┌─────────────────────────────────────────────────────────────┐
│                        game_theory.py                       │
├─────────────────┬───────────────────┬───────────────────────┤
│   <<enum>>      │   <<enum>>        │   <<dict>>            │
│   Action        │   StrategyType    │   Payoff Matrices     │
│─────────────────│───────────────────│───────────────────────│
│ COOPERATE       │ ALWAYS_COOPERATE  │ PRISONER_DILEMMA_     │
│ DEFECT          │ ALWAYS_DEFECT     │   PAYOFF              │
│ HEADS           │ TIT_FOR_TAT       │ MATCHING_PENNIES_     │
│ TAILS           │ RANDOM            │   PAYOFF              │
│ STAG            │ GRUDGER           │ STAG_HUNT_PAYOFF      │
│ HARE            │ PAVLOV            │                       │
└────────┬────────┴─────────┬─────────┴────────────┬──────────┘
         │                  │                       │
         ▼                  ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│     Player      │  │   GameEngine    │  │     Tournament      │
│─────────────────│  │─────────────────│  │─────────────────────│
│ name: str       │  │ game_name: str  │  │ game_name: str      │
│ strategy:       │  │ player1: Player │  │ rounds_per_match:   │
│   StrategyType  │  │ player2: Player │  │   int               │
│ history: list   │  │ rounds: int     │  │ players: list       │
│ opponent_hist   │  │ results: list   │  │ standings: dict     │
│ score: int      │  │─────────────────│  │─────────────────────│
│─────────────────│  │ play_round()    │  │ add_player()        │
│ choose_action() │  │ run()           │  │ run()               │
│ update_opp_h()  │  │ get_winner()    │  │ get_champion()      │
│ add_score()     │  │ get_summary()   │  │                     │
│ reset()         │  └────────┬────────┘  └──────────┬──────────┘
└────────┬────────┘           │                       │
         │                   uses                    uses
         └──────────────────► Player ◄────────────────┘
```

### 2.2 Diagrama de secvență pentru un meci (GameEngine.run)

```
 Client        GameEngine        Player1          Player2
   │               │                │                │
   │──run()───────►│                │                │
   │               │──play_round()──┤                │
   │               │                │                │
   │               │◄──choose_action(valid_actions)──│
   │               │                │                │
   │               │──choose_action(valid_actions)───►│
   │               │                │                │
   │               │──update_opponent_history(a2)───►│
   │               │◄──update_opponent_history(a1)───│
   │               │                │                │
   │               │  (lookup payoff[(a1,a2)])        │
   │               │  score1, score2                  │
   │               │──player1.score += score1        │
   │               │──player2.score += score2        │
   │               │                │                │
   │               │  [repeat rounds times]           │
   │               │                │                │
   │◄──results─────│                │                │
```

### 2.3 Diagrama de flux pentru choose_action (TIT_FOR_TAT)

```
        ┌──────────────────────┐
        │   choose_action()    │
        │  (TIT_FOR_TAT)       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  opponent_history    │
        │  este gol?           │
        └──────┬───────────────┘
               │
       ┌───────┴────────┐
       │ DA             │ NU
       ▼                ▼
 ┌──────────┐   ┌────────────────────────┐
 │ returnă  │   │ opponent_history[-1]   │
 │ valid[0] │   │ în valid_actions?      │
 │(COOPERATE│   └──────────┬─────────────┘
 │  / STAG) │              │
 └──────────┘      ┌───────┴────────┐
                   │ DA             │ NU
                   ▼                ▼
            ┌──────────┐     ┌──────────┐
            │ returnă  │     │ returnă  │
            │ acțiunea │     │ valid[0] │
            │adversarului    │(fallback)│
            └──────────┘     └──────────┘
```

---

## 3. Configurare hardware și software

| Componentă | Detalii |
|---|---|
| **OS** | Ubuntu 24.04 LTS (fără mașină virtuală) |
| **Procesor** | x86-64 |
| **Python** | 3.12+ |
| **Framework testare** | `unittest` (stdlib Python) – fără dependențe externe |
| **Instrumente diagrame** | app.diagrams.net, reprezentare ASCII în README |
| **Tool AI folosit** | Claude (Anthropic), model `claude-sonnet-4-6` |

**Nu** s-au folosit biblioteci externe (numpy, pandas, etc.). Proiectul rulează cu Python standard.

---

## 4. Instalare și rulare

```bash
# Clonare repository
git clone <url_repository>
cd T11_GameTesting

# Rulare teste
python -m unittest tests/test_game_theory.py -v

# Rulare aplicație demo
python src/game_theory.py
```

**Structura repository:**

```
T11_GameTesting/
├── src/
│   └── game_theory.py          # Codul sursă principal
├── tests/
│   └── test_game_theory.py     # Suite de teste unitare
└── README.md                   # Această documentație
```

---

## 5. Strategii de testare

### 5.1 Partiționare în clase de echivalență

Partiționarea în clase de echivalență [2] grupează datele de intrare în categorii pentru care comportamentul sistemului este identic. Am identificat următoarele clase:

#### 5.1.1 Clasa `Player.__init__`

| Clasă | Partiție | Reprezentant | Rezultat așteptat |
|---|---|---|---|
| EC-P1 | Nume valid, strategie validă | `("Alice", ALWAYS_COOPERATE)` | OK |
| EC-P2 | Oricare `StrategyType` valid | toate cele 6 enum-uri | OK |
| EC-P3 | Nume gol `""` | `("")` | `ValueError` |
| EC-P4 | Nume `None` | `None` | `ValueError` |
| EC-P5 | Strategie ca string | `"tit_for_tat"` | `TypeError` |
| EC-P6 | Strategie `None` | `None` | `TypeError` |

#### 5.1.2 Clasa `GameEngine.__init__`

| Clasă | Partiție | Reprezentant | Rezultat așteptat |
|---|---|---|---|
| EC-GE1 | Joc valid | `"prisoner_dilemma"` | OK |
| EC-GE2 | Joc inexistent | `"chess"` | `ValueError` |
| EC-GE3 | Același obiect Player pentru ambii | `p1 is p2` | `ValueError` |
| EC-GE4 | Toate jocurile suportate | cele 3 jocuri | OK |

#### 5.1.3 Clase de echivalență pentru matricile de plată

| Clasă | Partiție | Reprezentant | Rezultat așteptat |
|---|---|---|---|
| EC-PR1 | (C, C) prisoner | cooperate+cooperate | (3, 3) |
| EC-PR2 | (C, D) prisoner | cooperate+defect | (0, 5) |
| EC-PR3 | (D, C) prisoner | defect+cooperate | (5, 0) |
| EC-PR4 | (D, D) prisoner | defect+defect | (1, 1) |
| EC-MP1 | (H, H) matching pennies | heads+heads | (1, -1) |
| EC-MP2 | (T, T) matching pennies | tails+tails | (1, -1) |
| EC-SH1 | (S, S) stag hunt | stag+stag | (4, 4) |
| EC-SH2 | (H, H) stag hunt | hare+hare | (2, 2) |

#### 5.1.4 Strategii – partiții pentru `choose_action`

| Clasă | Strategie | Condiție | Acțiune returnată |
|---|---|---|---|
| EC-PA1 | ALWAYS_COOPERATE | oricând | `valid_actions[0]` |
| EC-PA2 | ALWAYS_DEFECT | oricând | `valid_actions[-1]` |
| EC-PA3 | TIT_FOR_TAT | prima rundă | `valid_actions[0]` |
| EC-PA4 | TIT_FOR_TAT | adversar a defectat | DEFECT |
| EC-PA5 | TIT_FOR_TAT | adversar a cooperat | COOPERATE |
| EC-PA6 | GRUDGER | adversar nu a trădat | COOPERATE |
| EC-PA7 | GRUDGER | adversar a trădat odată | DEFECT (permanent) |
| EC-PA8 | PAVLOV | prima rundă | COOPERATE |
| EC-PA9 | PAVLOV | adversar cooperat | menține acțiunea |
| EC-PA10 | PAVLOV | adversar defectat | schimbă acțiunea |
| EC-PA11 | RANDOM | oricând | acțiune din valid_actions |

#### 5.1.5 Turneu – partiții

| Clasă | Condiție | Rezultat așteptat |
|---|---|---|
| EC-T1 | Joc valid, runde valide | OK |
| EC-T2 | Joc invalid | `ValueError` |
| EC-T3 | Adăugare jucător nou | OK |
| EC-T4 | Adăugare jucător duplicat | `ValueError` |
| EC-T5 | 2 jucători → run() | clasament cu 2 intrări |
| EC-T6 | 3 jucători → run() | C(3,2)=3 meciuri jucate |
| EC-T7 | run() finalizat | `get_champion()` returnează câștigătorul |
| EC-T8 | fără run() | `get_champion()` returnează `None` |

---

### 5.2 Analiza valorilor de frontieră

Valorile de frontieră [2] testează limitele intervalelor valide:

| Test | Metodă testată | Valoare de frontieră | Rezultat |
|---|---|---|---|
| BVA-GE1 | `GameEngine.__init__` | `rounds = 0` | `ValueError` |
| BVA-GE2 | `GameEngine.__init__` | `rounds = -3` | `ValueError` |
| BVA-GE3 | `GameEngine.__init__` | `rounds = 1` (minim valid) | OK |
| BVA-PA1 | `choose_action` | `valid_actions = []` | `ValueError` |
| BVA-PA2 | `choose_action` | `valid_actions = [1 element]` | returnează singurul element |
| BVA-RUN1 | `GameEngine.run()` | `rounds = 1` | lista cu 1 element |
| BVA-S1 | `add_score` | `points = 0` | OK, scor nemodificat |
| BVA-S2 | `add_score` | `points = -1` | `ValueError` |
| BVA-T1 | `Tournament.__init__` | `rounds_per_match = 0` | `ValueError` |
| BVA-T2 | `Tournament.run()` | 1 singur jucător | `ValueError` |
| BVA-PM1 | `PRISONER_DILEMMA_PAYOFF` | număr intrări = 4 | exact 4 |
| BVA-PM2 | `MATCHING_PENNIES_PAYOFF` | număr intrări = 4 | exact 4 |

---

### 5.3 Acoperire la nivel de instrucțiune

Acoperirea la nivel de instrucțiune (Statement Coverage) [3] verifică că fiecare linie de cod este executată cel puțin o dată.

Prin rularea întregii suite de teste, sunt executate:

- **Toate ramurile `if/else`** din `choose_action` (prin testele EC-PA*)
- **Toate funcțiile** din `Player`, `GameEngine`, `Tournament`
- **Toate intrările** din cele trei matrici de plată (prin testele EC-PR*, EC-MP*, EC-SH*)
- **Constructorii** cu input valid și invalid
- **Metodele** `reset()`, `add_score()`, `update_opponent_history()`, `get_summary()`

Instrucțiuni acoperite explicite (exemple din teste):

```python
# COV-PA1: acțiunea este adăugată în history
p.choose_action(self.actions)
p.choose_action(self.actions)
self.assertEqual(len(p.history), 2)

# COV-OH1: update_opponent_history funcționează
p.update_opponent_history(Action.DEFECT)
self.assertEqual(p.opponent_history, [Action.DEFECT])

# COV-R1: reset() curăță toate câmpurile
p.reset()
self.assertEqual(p.score, 0)
self.assertEqual(p.history, [])
```

---

### 5.4 Acoperire la nivel de decizie

Acoperirea la nivel de decizie (Branch Coverage / Decision Coverage) [3] asigură că fiecare ramură (adevărat/fals) din fiecare decizie este parcursă.

Deciziile cheie și ramurile acoperite:

#### `_tit_for_tat`
```python
if not self.opponent_history:        # Ramura TRUE → EC-PA3
    return valid_actions[0]          # Ramura FALSE → EC-PA4, EC-PA5
return self.opponent_history[-1] if ... in valid_actions else valid_actions[0]
                                     # TRUE → EC-PA4/PA5; FALSE → IC-1
```

#### `_grudger`
```python
if self.opponent_history and self.opponent_history[-1] == valid_actions[-1]:
                                     # TRUE → EC-PA7; FALSE → EC-PA6
    self._defected_once = True
if self._defected_once:              # TRUE → EC-PA7; FALSE → EC-PA6
    return valid_actions[-1]
```

#### `_pavlov`
```python
if not self.history:                 # TRUE → EC-PA8; FALSE → EC-PA9/PA10
    return valid_actions[0]
if self.opponent_history and ...:    # TRUE → EC-PA9; FALSE → EC-PA10
    return last_action
```

#### `GameEngine.get_winner`
```python
if self.player1.score > self.player2.score:   # TRUE → EC-WIN1; FALSE continuă
    return self.player1.name
if self.player2.score > self.player1.score:   # TRUE → EC-WIN2; FALSE → EC-WIN3
    return self.player2.name
return None
```

---

### 5.5 Acoperire la nivel de condiție

Acoperirea la nivel de condiție (Condition Coverage) [3] verifică că fiecare condiție atomică dintr-o expresie booleană ia atât valoarea TRUE cât și FALSE.

Condiția compusă din `_grudger`:
```python
if self.opponent_history and self.opponent_history[-1] == valid_actions[-1]:
```
Decompoziție:
- `C1 = self.opponent_history` (lista non-goală)
- `C2 = self.opponent_history[-1] == valid_actions[-1]`

| Test | C1 | C2 | Rezultat decizie |
|---|---|---|---|
| EC-PA8 (prima rundă) | FALSE | - | FALSE |
| EC-PA6 (adversar cooperat) | TRUE | FALSE | FALSE |
| EC-PA7 (adversar defectat) | TRUE | TRUE | TRUE |

Condiția din `_pavlov`:
```python
if self.opponent_history and self.opponent_history[-1] == valid_actions[0]:
```
- C1 = `self.opponent_history` non-gol → testat în EC-PA8 (FALSE), EC-PA9 (TRUE)
- C2 = acțiunea adversarului = valid_actions[0] → TRUE în EC-PA9, FALSE în EC-PA10

---

### 5.6 Circuite independente (MC/DC)

Testele pentru circuite independente vizează ramuri care nu sunt acoperite în mod natural de celelalte categorii de teste:

| Test | Circuit acoperit |
|---|---|
| IC-1 | `_tit_for_tat` – acțiunea adversarului din istoricul propriu nu apare în `valid_actions` → fallback la `valid_actions[0]` |
| IC-2 | `_grudger` – adversarul defectează chiar la prima rundă (fără rundă anterioară de cooperare) |
| IC-3 | `_pavlov` – acțiunea proprie precedentă nu se găsește în lista `valid_actions` curentă → fallback la index 0 |
| IC-4 | `GameEngine.run()` apelat de două ori consecutiv → `results` este reinițializat, nu concatenat |
| IC-5 | `play_round()` actualizează corect `opponent_history` pentru **ambii** jucători (nu doar pentru unul) |

---

### 5.7 Testare bazată pe mutanți

Testarea bazată pe mutanți [4] introduce modificări sintactice mici (mutanți) în cod și verifică că testele le detectează (le „omoară"). Mai jos sunt prezentați **8 mutanți neechivalenți** și testele care îi elimină.

#### Mutanți în `GameEngine.__init__`

**M1 – Operator relațional în validarea `rounds`**

| | Original | Mutant |
|---|---|---|
| Cod | `if rounds <= 0:` | `if rounds < 0:` |
| Efect | Permite `rounds=0` (nu ar ridica excepție) |
| Test ucigaș | `MUT-1: test_mutant_rounds_boundary_zero` |

```python
# Testul care omoară M1:
def test_mutant_rounds_boundary_zero(self):
    with self.assertRaises(ValueError):
        GameEngine("prisoner_dilemma", p1, p2, 0)  # 0 < 0 e FALSE → mutantul supraviețuiește fără test
```

#### Mutanți în `GameEngine.get_winner`

**M2 – Operator relațional în compararea scorurilor**

| | Original | Mutant |
|---|---|---|
| Cod | `if self.player1.score > self.player2.score:` | `if self.player1.score >= self.player2.score:` |
| Efect | La egalitate, `get_winner()` ar returna `player1.name` în loc de `None` |
| Test ucigaș | `MUT-2: test_mutant_winner_equality_is_none` |

```python
def test_mutant_winner_equality_is_none(self):
    # Ambii jucători cooperează → scor egal → winner trebuie să fie None
    engine.run()
    self.assertIsNone(engine.get_winner())
```

#### Mutanți în `Player.add_score`

**M3 – Operator relațional în validarea punctelor**

| | Original | Mutant |
|---|---|---|
| Cod | `if points < 0:` | `if points <= 0:` |
| Efect | `add_score(0)` ar ridica `ValueError` (comportament incorect) |
| Test ucigaș | `MUT-3: test_mutant_add_score_zero_allowed` |

```python
def test_mutant_add_score_zero_allowed(self):
    p.add_score(0)
    self.assertEqual(p.score, 0)  # 0 este valid → mutantul ridică ValueError incorect
```

#### Mutanți în matricile de plată

**M4 – Constantă în payoff (C,C)**

| | Original | Mutant |
|---|---|---|
| Cod | `(Action.COOPERATE, Action.COOPERATE): (3, 3)` | `(2, 2)` sau `(4, 4)` |
| Efect | Scor incorect → strategia TIT_FOR_TAT nu mai este dominantă în mod corespunzător |
| Test ucigaș | `MUT-4: test_mutant_payoff_cooperate_cooperate_exact` |

```python
def test_mutant_payoff_cooperate_cooperate_exact(self):
    self.assertEqual(PRISONER_DILEMMA_PAYOFF[(Action.COOPERATE, Action.COOPERATE)], (3, 3))
```

**M5 – Flag inițial în GRUDGER**

| | Original | Mutant |
|---|---|---|
| Cod | `self._defected_once = False` | `self._defected_once = True` |
| Efect | GRUDGER ar defecta imediat din prima rundă, ignorând istoricul |
| Test ucigaș | `MUT-5: test_mutant_grudger_starts_not_defected` |

**M6 – Condiție PAVLOV (stay vs shift)**

| | Original | Mutant |
|---|---|---|
| Cod | `if self.opponent_history[-1] == valid_actions[0]:` | `== valid_actions[-1]` |
| Efect | PAVLOV ar menține acțiunea când trebuie să o schimbe și invers |
| Test ucigaș | `MUT-6: test_mutant_pavlov_correct_condition_for_stay` |

**M7 – Limita inferioară în Tournament.run**

| | Original | Mutant |
|---|---|---|
| Cod | `if len(self.players) < 2:` | `if len(self.players) < 1:` |
| Efect | Turneul cu 1 jucător nu ar ridica excepție → `IndexError` ulterior |
| Test ucigaș | `MUT-7: test_mutant_tournament_requires_two_players` |

**M8 – Asimetrie în STAG_HUNT_PAYOFF**

| | Original | Mutant |
|---|---|---|
| Cod | `(STAG, HARE): (0, 2)`, `(HARE, STAG): (2, 0)` | cele două linii interschimbate |
| Efect | Avantajul jucătorului care alege HARE contra partenerului STAG ar fi inversat |
| Test ucigaș | `MUT-8: test_mutant_stag_hunt_asymmetry` |

#### Sumarul mutanților

| Mutant | Locație | Tip operator mutant | Ucis de |
|---|---|---|---|
| M1 | `GameEngine.__init__` | `<=` → `<` | MUT-1 |
| M2 | `get_winner` | `>` → `>=` | MUT-2 |
| M3 | `add_score` | `<` → `<=` | MUT-3 |
| M4 | `PRISONER_DILEMMA_PAYOFF` | constantă 3 → 2 | MUT-4 |
| M5 | `Player.__init__` | `False` → `True` | MUT-5 |
| M6 | `_pavlov` | `[0]` → `[-1]` | MUT-6 |
| M7 | `Tournament.run` | `< 2` → `< 1` | MUT-7 |
| M8 | `STAG_HUNT_PAYOFF` | inversare rânduri | MUT-8 |

---

## 6. Diagrame

### 6.1 Diagrama de stare pentru strategia GRUDGER

```
        ┌─────────────────────────────────────┐
        │                                     │
        ▼                                     │
  ┌───────────┐  adversar cooperat   ┌──────────────────┐
  │ COOPERATE │─────────────────────►│ COOPERATE        │
  │ (start)   │                      │ (același estado)  │
  └───────────┘                      └──────────────────┘
        │
        │ adversar defectează (prima oară)
        ▼
  ┌───────────┐  oricând             ┌──────────────────┐
  │  DEFECT   │─────────────────────►│ DEFECT (forever) │
  │ (stare    │                      │ (absorbing state) │
  │ absorbantă│◄─────────────────────┘                  │
  └───────────┘                                          │
        ▲                                                │
        └────────────────────────────────────────────────┘
```

### 6.2 Diagrama de stare pentru strategia PAVLOV (Win-Stay, Lose-Shift)

```
  ┌────────────────────────────────────────────────────┐
  │         PAVLOV State Machine                       │
  ├────────────────────────────────────────────────────┤
  │                                                    │
  │   ┌──────────┐  adversar cooperat  ┌──────────┐   │
  │   │  COOPERATE│◄───────────────────│ COOPERATE│   │
  │   │  (self-   │                    │ (keep)   │   │
  │   │  loop)    │─── adversar ──────►│  DEFECT  │   │
  │   └──────────┘    defectează       └──────────┘   │
  │         ▲                               │          │
  │         │ adversar cooperat             │ adversar │
  │         │                              │ defectează│
  │   ┌──────────┐◄──────────────────┌──────────┐    │
  │   │  DEFECT  │                   │  DEFECT  │    │
  │   │ (keep)   │  adversar ──────► │ (self-   │    │
  │   └──────────┘  defectează       │  loop)   │    │
  │                                  └──────────┘    │
  └────────────────────────────────────────────────────┘
```

### 6.3 Graf de acoperire a circuitelor din `choose_action`

```
  START
    │
    ▼
  ┌──────────────────────────────┐
  │ strategy == ALWAYS_COOPERATE │──YES──► returnă valid[0]     ─► END
  └──────────────────────────────┘
    │ NO
    ▼
  ┌──────────────────────────────┐
  │ strategy == ALWAYS_DEFECT    │──YES──► returnă valid[-1]    ─► END
  └──────────────────────────────┘
    │ NO
    ▼
  ┌──────────────────────────────┐
  │ strategy == TIT_FOR_TAT      │──YES──► _tit_for_tat(...)   ─► END
  └──────────────────────────────┘
    │ NO
    ▼
  ┌──────────────────────────────┐
  │ strategy == RANDOM           │──YES──► _random(...)        ─► END
  └──────────────────────────────┘
    │ NO
    ▼
  ┌──────────────────────────────┐
  │ strategy == GRUDGER          │──YES──► _grudger(...)       ─► END
  └──────────────────────────────┘
    │ NO
    ▼
  ┌──────────────────────────────┐
  │ strategy == PAVLOV           │──YES──► _pavlov(...)        ─► END
  └──────────────────────────────┘
    │ (imposibil dacă StrategyType e validat la init)
    ▼
  (KeyError - imposibil în practică)
```

---

## 7. Rezultatele rulării testelor

### 7.1 Rulare completă

```
$ python -m unittest tests/test_game_theory.py -v

test_all_supported_games_valid ... ok
test_invalid_game_name ... ok
test_negative_rounds_raises ... ok
test_one_round_valid ... ok
test_same_player_object_raises ... ok
test_valid_engine_creation ... ok
test_zero_rounds_raises ... ok
test_matching_pennies_heads_heads ... ok
test_matching_pennies_tails_tails ... ok
test_play_round_returns_dict_with_required_keys ... ok
test_prisoner_dilemma_cooperate_cooperate ... ok
test_prisoner_dilemma_cooperate_defect ... ok
test_prisoner_dilemma_defect_cooperate ... ok
test_prisoner_dilemma_defect_defect ... ok
test_round_number_increments ... ok
test_stag_hunt_hare_hare ... ok
test_stag_hunt_stag_stag ... ok
test_get_summary_structure ... ok
test_get_summary_values ... ok
test_get_winner_player1_wins ... ok
test_get_winner_player2_wins ... ok
test_get_winner_tie ... ok
test_run_one_round ... ok
test_run_returns_correct_number_of_results ... ok
test_scores_accumulate_over_rounds ... ok
test_grudger_first_round_opponent_defects_immediately ... ok
test_pavlov_previous_action_not_in_valid_actions ... ok
test_play_round_updates_both_opponent_histories ... ok
test_run_resets_results_on_each_call ... ok
test_tit_for_tat_with_action_not_in_valid_list ... ok
test_mutant_add_score_zero_allowed ... ok
test_mutant_grudger_starts_not_defected ... ok
test_mutant_pavlov_correct_condition_for_stay ... ok
test_mutant_payoff_cooperate_cooperate_exact ... ok
test_mutant_rounds_boundary_zero ... ok
test_mutant_stag_hunt_asymmetry ... ok
test_mutant_tournament_requires_two_players ... ok
test_mutant_winner_equality_is_none ... ok
[...restul testelor...]

----------------------------------------------------------------------
Ran 79 tests in 0.004s

OK
```

### 7.2 Distribuția testelor pe categorii

| Categorie | Prefix | Nr. teste |
|---|---|---|
| Clase de echivalență (Player) | EC-P | 6 |
| Clase de echivalență (choose_action) | EC-PA | 11 |
| Clase de echivalență (GameEngine) | EC-GE, EC-PR, EC-MP, EC-SH, EC-WIN, EC-RUN | 16 |
| Clase de echivalență (Tournament) | EC-T | 8 |
| Clase de echivalență (Payoff) | EC-PM | 3 |
| Valori de frontieră | BVA | 12 |
| Acoperire instrucțiune/decizie | COV | 9 |
| Circuite independente | IC | 5 |
| Mutanți | MUT | 8 |
| Scoruri și reset | EC-S, COV-R | 4 |
| **TOTAL** | | **82 scenarii** (79 metode de test, unele cu `subTest`) |

### 7.3 Tabel comparativ: teste proprii vs. teste autogenerate AI

| Criteriu | Teste proprii | Teste Claude AI |
|---|---|---|
| **Număr teste** | 79 | ~40 |
| **Acoperire clase de echivalență** | ✅ Completă (toate 8 clase EA) | ✅ Parțial (4–5 clase) |
| **Valori de frontieră** | ✅ 12 teste BVA dedicate | ⚠️ 3–4 teste de frontieră |
| **Circuite independente** | ✅ 5 teste IC dedicate | ❌ Lipsă |
| **Mutanți** | ✅ 8 mutanți nominalizați | ⚠️ Implicit (fără numire) |
| **Acoperire strategii** | ✅ Toate 6 strategii | ✅ 4–5 strategii |
| **Acoperire 3 jocuri** | ✅ Toate 3 jocuri | ✅ 2–3 jocuri |
| **Decizie/condiție** | ✅ Explicit documentat | ⚠️ Implicit |
| **Claritate docstring** | ✅ Cod+categorie+EC/BVA | ⚠️ Generic |

---

## 8. Raport folosire tool AI (Claude)

### 8.1 Tool folosit

**Claude** (Anthropic), model `claude-sonnet-4-6`, accesat prin interfața web https://claude.ai

### 8.2 Prompt utilizat

```
Generează teste unitare Python cu unittest pentru următoarea clasă Python care 
implementează teoria jocurilor. Include teste pentru: constructor valid și invalid, 
metoda choose_action pentru strategia TIT_FOR_TAT, metoda add_score, și 
GameEngine.get_winner. Cod sursă: [game_theory.py atașat]
```

### 8.3 Răspuns AI (rezumat)

Claude a generat aproximativ 40 de teste grupate în 4 clase de test (`TestPlayer`, `TestChooseAction`, `TestAddScore`, `TestGameEngine`). Testele acopereau:
- Constructori valizi și invalizi pentru `Player` și `GameEngine`
- Toate cele 4 scenarii ale Prisoner's Dilemma
- TIT_FOR_TAT pentru prima rundă și rundele ulterioare
- `get_winner` pentru câștigător P1, P2 și egalitate

### 8.4 Diferențe față de suita proprie

**Ce a generat Claude corect:**
- Acoperirea tuturor celor 4 combinații de acțiuni din Prisoner's Dilemma
- Testarea constructorilor cu input invalid
- Logica de bază TIT_FOR_TAT

**Ce lipsea din testele Claude:**
1. **Circuitele independente (IC)** – Claude nu a generat teste pentru ramura fallback din `_tit_for_tat` (când acțiunea adversarului nu apare în `valid_actions`)
2. **Mutanții** – nu au fost nominalizate testele ca „ucigașe de mutanți" și nu au fost create teste dedicate pentru fiecare mutant
3. **Matching Pennies și Stag Hunt** – Claude a omis celelalte două jocuri
4. **GRUDGER și PAVLOV** – strategiile mai complexe au fost ignorate
5. **Tournament** – clasa `Tournament` nu a fost testată deloc
6. **Valori de frontieră exhaustive** – Claude nu a testat `rounds=0` vs `rounds=1`, sau `points=-1` vs `points=0`
7. **Strategia RANDOM cu seed fix** – Claude nu a testat că RANDOM returnează întotdeauna o acțiune validă

### 8.5 Interpretare

Testele generate de AI sunt un punct de plecare util pentru acoperirea de bază, dar nu înlocuiesc o analiză sistematică bazată pe strategii de testare formale. Pentru un proiect academic care solicită explicit clase de echivalență, valori de frontieră, circuite independente și mutanți, testele manuale rămân superioare calitativ. Combinația optimă este: generare automată → validare → extindere manuală cu tehnicile formale.

---

## 9. Referințe bibliografice

[1] Von Neumann, John; Morgenstern, Oskar, *Theory of Games and Economic Behavior*, Princeton University Press, 1944.

[2] Myers, Glenford J.; Sandler, Corey; Badgett, Tom, *The Art of Software Testing*, 3rd ed., John Wiley & Sons, 2011.

[3] Ammann, Paul; Offutt, Jeff, *Introduction to Software Testing*, 2nd ed., Cambridge University Press, 2016.

[4] Jia, Yue; Harman, Mark, *An Analysis and Survey of the Development of Mutation Testing*, IEEE Transactions on Software Engineering, vol. 37, nr. 5, 2011, pp. 649–678.

[5] Axelrod, Robert, *The Evolution of Cooperation*, Basic Books, 1984.

[6] Dixit, Avinash K.; Nalebuff, Barry J., *Thinking Strategically: The Competitive Edge in Business, Politics, and Everyday Life*, W.W. Norton & Company, 1991.

[7] Python Software Foundation, *unittest — Unit testing framework*, https://docs.python.org/3/library/unittest.html, Data ultimei accesări: iunie 2026.

[8] Claude, Anthropic, https://claude.ai, Data generării: iunie 2026.

[9] app.diagrams.net, *draw.io Diagram Tool*, https://app.diagrams.net, Data ultimei accesări: iunie 2026.

[10] Offutt, Jeff; Untch, Roland H., *Mutation 2000: Uniting the Orthogonal*, în: Mutation Testing for the New Century, Kluwer Academic Publishers, 2001, pp. 34–44.
