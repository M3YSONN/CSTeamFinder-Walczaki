"""Funkcja oceny drużyny, algorytm genetyczny i dobór wężykiem (snake draft).

Ocena drużyny:  F = 0.40·R + 0.30·S + 0.20·P + 0.10·K     (każdy składnik w [0, 1])

  R – role:        1.0, jeśli jest IGL i Sniper; −0.5 za brak każdej z ról,
                   −0.25 za każdego nadmiarowego IGL-a / snajpera (marnowanie ról).
  S – statystyki:  jak blisko średni rating drużyny jest średniej wszystkich graczy
                   (cel: równe składy). S = 1 − |śr_drużyny − śr_ogólna| / odch_std.
  P – pozycje:     dla każdej mapy liczymy, ilu graczy można obsadzić na RÓŻNYCH
                   pozycjach (maksymalne skojarzenie gracz→pozycja), dzielimy przez 5
                   (lub liczbę pozycji na mapie, jeśli jest ich mniej) i uśredniamy po mapach.
  K – komunikacja: odsetek par graczy z tego samego kraju (0 = wszyscy z różnych
                   krajów, 1 = cała piątka z jednego kraju).

Ocena całego podziału (funkcja przystosowania w AG):
  fitness = średnia(F) − LAMBDA · (max(F) − min(F))
Pierwszy człon nagradza dobre drużyny, drugi karze za nierówne składy.
"""
from __future__ import annotations

import random
import statistics
from itertools import combinations

from db import Dane

WAGI = {"R": 0.40, "S": 0.30, "P": 0.20, "K": 0.10}
ROZMIAR_DRUZYNY = 5
KARA_BRAK_ROLI = 0.5
KARA_NADMIAR_ROLI = 0.25
LAMBDA = 0.5

ROLE_IGL = {"igl"}
ROLE_SNIPER = {"sniper", "awp"}


def _normalizuj_kraj(kraj: str) -> str:
    return " ".join(kraj.lower().split())


def _skojarzenie(zbiory: list[frozenset]) -> int:
    """Maks. liczba graczy, którym można dać różne pozycje (algorytm ścieżek powiększających)."""
    przypisanie: dict[int, int] = {}   # pozycja -> indeks gracza

    def powieksz(i: int, odwiedzone: set) -> bool:
        for p in zbiory[i]:
            if p not in odwiedzone:
                odwiedzone.add(p)
                if p not in przypisanie or powieksz(przypisanie[p], odwiedzone):
                    przypisanie[p] = i
                    return True
        return False

    wynik = 0
    for i, z in enumerate(zbiory):
        if not z:          # brak danych o pozycji -> nie liczymy kolizji
            wynik += 1
        elif powieksz(i, set()):
            wynik += 1
    return wynik


class Ocena:
    def __init__(self, dane: Dane, rozmiar: int = ROZMIAR_DRUZYNY):
        self.rozmiar = rozmiar
        g = dane.gracze
        self.igl = [x.rola.lower() in ROLE_IGL for x in g]
        self.sniper = [x.rola.lower() in ROLE_SNIPER for x in g]
        self.rating = [x.rating for x in g]
        self.kraj = [_normalizuj_kraj(x.kraj) for x in g]
        self.srednia = statistics.mean(self.rating)
        self.odchylenie = statistics.pstdev(self.rating) or 1.0

        mapy = sorted(dane.mapy)
        self.pozycje = [[frozenset(x.pozycje.get(m, ())) for m in mapy] for x in g]
        self.limit_map = [min(rozmiar, len(dane.pozycje_na_mapie.get(m, ())) or rozmiar)
                          for m in mapy]
        self._cache: dict[tuple, dict] = {}

    # ---- ocena jednej drużyny ----
    def druzyna(self, sklad) -> dict:
        klucz = tuple(sorted(sklad))
        if klucz in self._cache:
            return self._cache[klucz]

        n_igl = sum(self.igl[i] for i in klucz)
        n_snp = sum(self.sniper[i] for i in klucz)
        R = 1.0
        R -= KARA_BRAK_ROLI * (n_igl == 0) + KARA_BRAK_ROLI * (n_snp == 0)
        R -= KARA_NADMIAR_ROLI * (max(0, n_igl - 1) + max(0, n_snp - 1))
        R = max(0.0, R)

        sr = sum(self.rating[i] for i in klucz) / len(klucz)
        S = max(0.0, 1 - abs(sr - self.srednia) / self.odchylenie)

        p_mapy = []
        for m, limit in enumerate(self.limit_map):
            obsadzeni = _skojarzenie([self.pozycje[i][m] for i in klucz])
            p_mapy.append(min(1.0, obsadzeni / limit))
        P = sum(p_mapy) / len(p_mapy) if p_mapy else 1.0

        pary = list(combinations(klucz, 2))
        K = sum(self.kraj[a] == self.kraj[b] for a, b in pary) / len(pary) if pary else 0.0

        F = WAGI["R"] * R + WAGI["S"] * S + WAGI["P"] * P + WAGI["K"] * K
        wynik = {"R": R, "S": S, "P": P, "K": K, "F": F, "sr_rating": sr,
                 "igl": n_igl, "sniper": n_snp}
        self._cache[klucz] = wynik
        return wynik

    # ---- ocena całego podziału ----
    def podzial(self, druzyny) -> tuple[float, list[dict]]:
        oceny = [self.druzyna(d) for d in druzyny]
        f = [o["F"] for o in oceny]
        fitness = sum(f) / len(f) - LAMBDA * (max(f) - min(f))
        return fitness, oceny


# ======================================================================
#  Dobór wężykiem (punkt odniesienia)
# ======================================================================
def dobor_wezykiem(ocena: Ocena, liczba_druzyn: int) -> list[list[int]]:
    """Gracze posortowani malejąco po ratingu; kolejność wyboru 1..n, n..1, 1..n, ..."""
    kolejnosc = sorted(range(len(ocena.rating)), key=lambda i: -ocena.rating[i])
    wybor = iter(kolejnosc)
    druzyny = [[] for _ in range(liczba_druzyn)]
    for runda in range(ocena.rozmiar):
        indeksy = range(liczba_druzyn) if runda % 2 == 0 else reversed(range(liczba_druzyn))
        for t in indeksy:
            druzyny[t].append(next(wybor))
    return druzyny


# ======================================================================
#  Algorytm genetyczny
# ======================================================================
def algorytm_genetyczny(ocena: Ocena, liczba_druzyn: int, *, populacja: int = 150,
                        pokolenia: int = 800, p_krzyzowania: float = 0.9,
                        p_mutacji: float = 0.5, elita: int = 2, turniej: int = 3,
                        cierpliwosc: int = 250, seed: int | None = None,
                        log=print) -> tuple[list[list[int]], list[float]]:
    """
    Chromosom: permutacja indeksów graczy. Drużyna t = geny [t·5, (t+1)·5).
    Gracze poza pierwszymi liczba_druzyn·5 pozycjami to rezerwa (gdy liczba graczy
    nie dzieli się przez 5).

    Selekcja:     turniejowa.
    Krzyżowanie:  drużynowe – dziecko dziedziczy losową część CAŁYCH drużyn z rodzica A,
                  resztę graczy dopisuje w kolejności z rodzica B (zachowuje dobre składy).
    Mutacja:      zamiana 1–3 graczy między różnymi drużynami (lub z rezerwą).
    Elitaryzm:    najlepsze osobniki przechodzą bez zmian.
    Stop:         po `pokolenia` lub gdy przez `cierpliwosc` pokoleń brak poprawy.
    """
    rng = random.Random(seed)
    n = len(ocena.rating)
    R = ocena.rozmiar
    if liczba_druzyn * R > n:
        raise ValueError("Za mało graczy na tyle drużyn")

    def dziel(chrom):
        return [chrom[t * R:(t + 1) * R] for t in range(liczba_druzyn)]

    def fit(chrom):
        return ocena.podzial(dziel(chrom))[0]

    def selekcja(pop, oceny):
        uczestnicy = rng.sample(range(len(pop)), turniej)
        return pop[max(uczestnicy, key=lambda i: oceny[i])]

    def krzyzowanie(a, b):
        druz_a = dziel(a)
        wybrane = [d for d in druz_a if rng.random() < 0.5]
        dziecko = [g for d in wybrane for g in d]
        uzyte = set(dziecko)
        dziecko += [g for g in b if g not in uzyte]
        return dziecko

    def mutacja(chrom):
        chrom = chrom[:]
        for _ in range(rng.randint(1, 3)):
            i = rng.randrange(liczba_druzyn * R)
            j = rng.randrange(n)
            while j // R == i // R:
                j = rng.randrange(n)
            chrom[i], chrom[j] = chrom[j], chrom[i]
        return chrom

    pop = [rng.sample(range(n), n) for _ in range(populacja)]
    oceny = [fit(c) for c in pop]
    najlepszy_idx = max(range(populacja), key=oceny.__getitem__)
    najlepszy, najlepsza_ocena = pop[najlepszy_idx][:], oceny[najlepszy_idx]
    historia = [najlepsza_ocena]
    bez_poprawy = 0

    for pok in range(1, pokolenia + 1):
        ranking = sorted(range(populacja), key=lambda i: -oceny[i])
        nowa = [pop[i][:] for i in ranking[:elita]]
        while len(nowa) < populacja:
            a, b = selekcja(pop, oceny), selekcja(pop, oceny)
            dziecko = krzyzowanie(a, b) if rng.random() < p_krzyzowania else a[:]
            if rng.random() < p_mutacji:
                dziecko = mutacja(dziecko)
            nowa.append(dziecko)
        pop = nowa
        oceny = [fit(c) for c in pop]

        idx = max(range(populacja), key=oceny.__getitem__)
        if oceny[idx] > najlepsza_ocena + 1e-12:
            najlepszy, najlepsza_ocena = pop[idx][:], oceny[idx]
            bez_poprawy = 0
        else:
            bez_poprawy += 1
        historia.append(najlepsza_ocena)

        if log and (pok % 100 == 0 or pok == 1):
            log(f"  pokolenie {pok:4d}: najlepszy fitness = {najlepsza_ocena:.4f}")
        if bez_poprawy >= cierpliwosc:
            if log:
                log(f"  stop po {pok} pokoleniach (brak poprawy przez {cierpliwosc})")
            break

    return dziel(najlepszy), historia
