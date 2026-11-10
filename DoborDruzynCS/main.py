#!/usr/bin/env python3
"""
Działający przykład: optymalny skład 5-osobowej drużyny (IGL, Support, Rifler, Sniper)
z (wyimaginowanej) bazy danych 30 zawodników.

Bez zewnętrznych zależności — tylko biblioteka standardowa Pythona 3.9+.
Wyimaginowana baza to SQLite w pamięci o takiej samej strukturze, jaka będzie w PostgreSQL.
Aby przejść na prawdziwy PostgreSQL, zobacz funkcję `polacz_postgres()` na dole pliku:
reszta kodu pozostaje bez zmian.

Algorytm: dokładne przeszukiwanie „podziału i ograniczeń” (branch & bound):
  * sloty wypełniane są po kolei, najsilniejsi kandydaci — jako pierwsi;
  * gałąź jest odcinana, gdy nawet w najlepszym razie nie pobije już znalezionego wyniku;
  * naruszenia limitów ról są odcinane od razu.
Dzięki temu sprawdzane są nie wszystkie kombinacje, a tylko obiecujące,
a wynik jest gwarantowanie optymalny.

Ocena składu = suma ocen − waga_balansu × (różnica między najsilniejszą
a najsłabszą pozycją pod względem średniej oceny).
"""
from __future__ import annotations

import itertools
import math
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Ustawienia
# --------------------------------------------------------------------------- #

@dataclass
class KonfiguracjaSkladu:
    # ilu zawodników potrzeba na każdą pozycję (razem 5)
    sloty: dict = field(default_factory=lambda: {"Przód": 2, "Środek": 1, "Tył": 2})
    # minimum / maksimum zawodników każdej roli w składzie
    rola_min: dict = field(default_factory=lambda: {"IGL": 1, "Support": 1, "Rifler": 1, "Sniper": 1})
    rola_max: dict = field(default_factory=lambda: {"IGL": 1, "Support": 2, "Rifler": 3, "Sniper": 1})
    # waga balansu między pozycjami: 0 = tylko suma ocen, więcej = bardziej wyrównany skład
    waga_balansu: float = 0.5
    # dla dużych baz: ilu najlepszych zawodników zostawić dla każdej pary (rola, pozycja)
    kandydatow_na_grupe: int = 200


@dataclass(frozen=True)
class Zawodnik:
    id: int
    imie: str
    rola: str
    ocena: float
    pozycje: tuple


# --------------------------------------------------------------------------- #
# Wyimaginowana baza danych (30 zmyślonych zawodników)
# --------------------------------------------------------------------------- #

ZAPYTANIE_SQL = "SELECT id, imie, rola, ocena, pozycje FROM zawodnicy"

DANE_DEMO = [
    # IGL
    (1,  "Wojciech Wilczyński", "IGL",    84, "Środek"),
    (2,  "Marek Zawisza",       "IGL",    79, "Środek,Tył"),
    (3,  "Kamil Dąbrowski",     "IGL",    88, "Tył,Środek"),
    (4,  "Piotr Sowa",          "IGL",    72, "Środek"),
    (5,  "Łukasz Mazur",        "IGL",    81, "Przód,Środek"),
    (6,  "Dawid Rybak",         "IGL",    76, "Tył"),
    # Support
    (7,  "Tomasz Jastrząb",     "Support", 82, "Środek,Tył"),
    (8,  "Bartek Nowicki",      "Support", 77, "Przód,Środek"),
    (9,  "Michał Zając",        "Support", 85, "Tył"),
    (10, "Adam Bielik",         "Support", 74, "Środek"),
    (11, "Szymon Lis",          "Support", 80, "Przód"),
    (12, "Jakub Kruk",          "Support", 79, "Tył,Środek"),
    (13, "Filip Orzeł",         "Support", 71, "Przód,Tył"),
    (14, "Hubert Sikora",       "Support", 83, "Środek"),
    # Rifler
    (15, "Oskar Burza",         "Rifler", 93, "Przód"),
    (16, "Mateusz Pioruń",      "Rifler", 90, "Przód,Środek"),
    (17, "Kacper Żmija",        "Rifler", 87, "Przód"),
    (18, "Patryk Cień",         "Rifler", 86, "Środek,Tył"),
    (19, "Igor Szczerba",       "Rifler", 91, "Przód,Tył"),
    (20, "Damian Ryś",          "Rifler", 78, "Środek"),
    (21, "Krzysztof Gradowski", "Rifler", 83, "Przód,Środek,Tył"),
    (22, "Paweł Sokół",         "Rifler", 89, "Środek,Tył"),
    (23, "Mikołaj Kuna",        "Rifler", 75, "Tył"),
    (24, "Sebastian Wydra",     "Rifler", 80, "Przód"),
    # Sniper
    (25, "Radosław Orlik",      "Sniper", 92, "Tył"),
    (26, "Konrad Szpak",        "Sniper", 88, "Środek,Tył"),
    (27, "Artur Krogulec",      "Sniper", 85, "Przód,Tył"),
    (28, "Marcin Puchacz",      "Sniper", 79, "Tył"),
    (29, "Rafał Sęp",           "Sniper", 90, "Środek"),
    (30, "Jan Kruczek",         "Sniper", 73, "Przód,Środek"),
]


def utworz_baze_demo() -> sqlite3.Connection:
    pol = sqlite3.connect(":memory:")
    pol.execute("""
        CREATE TABLE zawodnicy (
            id      INTEGER PRIMARY KEY,
            imie    TEXT NOT NULL,
            rola    TEXT NOT NULL,
            ocena   REAL NOT NULL,
            pozycje TEXT NOT NULL      -- po przecinku: 'Przód,Środek'
        )
    """)
    pol.executemany("INSERT INTO zawodnicy VALUES (?, ?, ?, ?, ?)", DANE_DEMO)
    pol.commit()
    return pol


def pobierz_zawodnikow(pol, zapytanie: str = ZAPYTANIE_SQL) -> list:
    """Działa zarówno z sqlite3, jak i z psycopg2 (pozycje: tekst po przecinku lub tablica)."""
    kursor = pol.cursor()
    kursor.execute(zapytanie)
    zawodnicy = []
    for zid, imie, rola, ocena, pozycje in kursor.fetchall():
        if isinstance(pozycje, str):
            pozycje = pozycje.replace("{", "").replace("}", "").split(",")
        poz = tuple(p.strip() for p in pozycje if p and p.strip())
        if poz:
            zawodnicy.append(Zawodnik(zid, imie, rola, float(ocena), poz))
    return zawodnicy


# --------------------------------------------------------------------------- #
# Algorytm
# --------------------------------------------------------------------------- #

def wynik(sklad: list, konf: KonfiguracjaSkladu) -> float:
    """sklad: lista (pozycja, zawodnik)."""
    suma = sum(z.ocena for _, z in sklad)
    srednie = []
    for poz, potrzeba in konf.sloty.items():
        srednie.append(sum(z.ocena for pz, z in sklad if pz == poz) / potrzeba)
    return suma - konf.waga_balansu * (max(srednie) - min(srednie))


def przytnij_kandydatow(zawodnicy: list, konf: KonfiguracjaSkladu) -> dict:
    """Dla każdej pozycji — posortowana lista kandydatów (top-N na rolę)."""
    grupy = defaultdict(list)                        # (rola, pozycja) -> zawodnicy
    for z in zawodnicy:
        if z.rola not in konf.rola_max:
            continue
        for poz in z.pozycje:
            if poz in konf.sloty:
                grupy[(z.rola, poz)].append(z)

    wg_pozycji = defaultdict(dict)                   # pozycja -> {id: Zawodnik}
    for (rola, poz), grupa in grupy.items():
        grupa.sort(key=lambda z: -z.ocena)
        for z in grupa[: konf.kandydatow_na_grupe]:
            wg_pozycji[poz][z.id] = z
    return {poz: sorted(d.values(), key=lambda z: -z.ocena) for poz, d in wg_pozycji.items()}


def zbuduj_sklad(zawodnicy: list, konf: KonfiguracjaSkladu):
    """Zwraca (sklad, wynik, statystyki) lub (None, komunikat o błędzie, None)."""
    wg_pozycji = przytnij_kandydatow(zawodnicy, konf)
    sloty = [poz for poz, n in konf.sloty.items() for _ in range(n)]

    for poz in konf.sloty:
        if len(wg_pozycji.get(poz, [])) < konf.sloty[poz]:
            return None, f"Za mało zawodników na pozycję {poz}", None

    # górne ograniczenie udziału pozostałych slotów: najlepsza ocena na pozycji (bez balansu)
    najlepszy_na = {poz: wg_pozycji[poz][0].ocena for poz in konf.sloty}
    sufiks = [0.0] * (len(sloty) + 1)
    for i in range(len(sloty) - 1, -1, -1):
        sufiks[i] = sufiks[i + 1] + najlepszy_na[sloty[i]]

    najlepszy = {"wynik": float("-inf"), "sklad": None}
    stat = {"wezly": 0, "odciete_ograniczeniem": 0, "odciete_rolami": 0, "liscie": 0}
    uzyci: set = set()
    licznik_rol: Counter = Counter()
    wybrani: list = []

    def dfs(i: int, start: int, suma: float) -> None:
        stat["wezly"] += 1
        if i == len(sloty):
            stat["liscie"] += 1
            if all(licznik_rol[r] >= m for r, m in konf.rola_min.items()):
                w = wynik(wybrani, konf)
                if w > najlepszy["wynik"]:
                    najlepszy["wynik"], najlepszy["sklad"] = w, list(wybrani)
            return

        # ograniczenie: nawet idealny dobór (bez kary) nie pobije znalezionego -> odcinamy
        if suma + sufiks[i] <= najlepszy["wynik"]:
            stat["odciete_ograniczeniem"] += 1
            return
        # role, których brakuje do minimum, muszą zmieścić się w pozostałych slotach
        brak = sum(max(0, m - licznik_rol[r]) for r, m in konf.rola_min.items())
        if brak > len(sloty) - i:
            stat["odciete_rolami"] += 1
            return

        poz = sloty[i]
        kandydaci = wg_pozycji[poz]
        # dla identycznych pozycji ustalamy kolejność, by nie liczyć permutacji dwukrotnie
        pierwszy = start if i > 0 and sloty[i - 1] == poz else 0
        for idx in range(pierwszy, len(kandydaci)):
            z = kandydaci[idx]
            if z.id in uzyci or licznik_rol[z.rola] >= konf.rola_max[z.rola]:
                continue
            uzyci.add(z.id)
            licznik_rol[z.rola] += 1
            wybrani.append((poz, z))
            dfs(i + 1, idx + 1, suma + z.ocena)
            wybrani.pop()
            licznik_rol[z.rola] -= 1
            uzyci.discard(z.id)

    dfs(0, 0, 0.0)

    if najlepszy["sklad"] is None:
        return None, "Brak rozwiązania: limity ról/pozycji są niezgodne z dostępnymi zawodnikami", None
    return najlepszy["sklad"], najlepszy["wynik"], stat


def pelny_przeglad(zawodnicy: list, konf: KonfiguracjaSkladu):
    """Pełne przeszukanie — tylko do weryfikacji poprawności (wolne przy dużych danych)."""
    sloty = [poz for poz, n in konf.sloty.items() for _ in range(n)]
    najl_w, najl_s = float("-inf"), None
    for zestaw in itertools.combinations(zawodnicy, len(sloty)):
        role = Counter(z.rola for z in zestaw)
        if any(role[r] < m for r, m in konf.rola_min.items()):
            continue
        if any(role[r] > konf.rola_max.get(r, 0) for r in role):
            continue
        for perm in set(itertools.permutations(sloty)):      # możliwe przypisania do slotów
            if any(perm[i] not in z.pozycje for i, z in enumerate(zestaw)):
                continue
            sklad = list(zip(perm, zestaw))
            w = wynik(sklad, konf)
            if w > najl_w:
                najl_w, najl_s = w, sklad
    return najl_s, najl_w


# --------------------------------------------------------------------------- #
# Wyświetlanie i uruchomienie
# --------------------------------------------------------------------------- #

def wypisz_baze(zawodnicy: list) -> None:
    print(f"Zawodnicy w bazie: {len(zawodnicy)}")
    for rola in ("IGL", "Support", "Rifler", "Sniper"):
        print(f"\n  [{rola}]")
        for z in sorted((z for z in zawodnicy if z.rola == rola), key=lambda z: -z.ocena):
            print(f"    #{z.id:<3}{z.imie:<22}{z.ocena:>5.0f}   {', '.join(z.pozycje)}")


def wypisz_sklad(sklad: list, w: float, konf: KonfiguracjaSkladu) -> None:
    kolejnosc = {p: i for i, p in enumerate(konf.sloty)}
    sklad = sorted(sklad, key=lambda t: (kolejnosc[t[0]], -t[1].ocena))
    print(f"\n{'Pozycja':<9}{'Zawodnik':<22}{'Rola':<9}{'Ocena':>7}")
    print("-" * 47)
    for poz, z in sklad:
        print(f"{poz:<9}{z.imie:<22}{z.rola:<9}{z.ocena:>7.0f}")
    print("-" * 47)
    print(f"Suma ocen: {sum(z.ocena for _, z in sklad):.0f}")
    for poz, potrzeba in konf.sloty.items():
        sr = sum(z.ocena for pz, z in sklad if pz == poz) / potrzeba
        print(f"  średnia ocena {poz}: {sr:.1f}")
    print(f"Wynik końcowy (z uwzględnieniem balansu): {w:.2f}")


def pokaz_prace_algorytmu(zawodnicy: list, konf: KonfiguracjaSkladu, stat: dict) -> None:
    n, k = len(zawodnicy), sum(konf.sloty.values())
    kombinacje = math.comb(n, k)
    przypisania = math.perm(n, k)
    print("\n=== Jak pracował algorytm ===")
    print(f"Wszystkich 5-osobowych zestawów z {n} zawodników: {kombinacje:,}".replace(",", " "))
    print(f"Wszystkich uporządkowanych obsad slotów:         {przypisania:,}".replace(",", " "))
    print(f"Węzłów faktycznie odwiedzonych przez algorytm:   {stat['wezly']:,}".replace(",", " "))
    print(f"  odcięte przez ograniczenie górne (za słabe):   {stat['odciete_ograniczeniem']}")
    print(f"  odcięte przez limity ról:                      {stat['odciete_rolami']}")
    print(f"  pełne obsady sprawdzone do końca:              {stat['liscie']}")
    print(f"Przeszukano ok. {100 * stat['wezly'] / przypisania:.4f}% przestrzeni obsad.")


def porownanie_naiwne(zawodnicy: list, konf: KonfiguracjaSkladu) -> None:
    """Pokazuje, czemu nie wystarczy wziąć po prostu 5 najlepszych."""
    top5 = sorted(zawodnicy, key=lambda z: -z.ocena)[: sum(konf.sloty.values())]
    role = Counter(z.rola for z in top5)
    print("\n=== Naiwny wybór: 5 najwyżej ocenianych ===")
    for z in top5:
        print(f"  {z.imie:<22}{z.rola:<9}{z.ocena:>5.0f}   {', '.join(z.pozycje)}")
    print(f"  Suma ocen: {sum(z.ocena for z in top5):.0f}   Role: {dict(role)}")
    braki = [r for r, m in konf.rola_min.items() if role[r] < m]
    nadmiar = [r for r, m in konf.rola_max.items() if role[r] > m]
    if braki:
        print(f"  ✘ brakuje ról: {', '.join(braki)}")
    if nadmiar:
        print(f"  ✘ za dużo ról: {', '.join(nadmiar)}")


def porownanie_wag(zawodnicy: list, konf: KonfiguracjaSkladu) -> None:
    print("\n=== Wpływ wagi balansu ===")
    print(f"{'waga':<6}{'suma':>6}{'rozrzut':>9}   skład (Przód | Środek | Tył)")
    for waga in (0, 2, 5, 15):
        k = KonfiguracjaSkladu(konf.sloty, konf.rola_min, konf.rola_max, waga, konf.kandydatow_na_grupe)
        sklad, _, _ = zbuduj_sklad(zawodnicy, k)
        srednie = [sum(z.ocena for pz, z in sklad if pz == p) / n for p, n in k.sloty.items()]
        opis = " | ".join(
            ", ".join(f"{z.imie.split()[1]}({z.rola[:3]}{z.ocena:.0f})" for pz, z in sklad if pz == p)
            for p in k.sloty
        )
        print(f"{waga:<6}{sum(z.ocena for _, z in sklad):>6.0f}{max(srednie) - min(srednie):>9.1f}   {opis}")


def polacz_postgres(dsn: str):
    """Dla prawdziwej bazy: pip install psycopg2-binary, a następnie
         pol = polacz_postgres("postgresql://user:haslo@host:5432/baza")
         zawodnicy = pobierz_zawodnikow(pol, "SELECT id, imie, rola, ocena, pozycje FROM zawodnicy")
    """
    import psycopg2
    return psycopg2.connect(dsn)


def main() -> None:
    konf = KonfiguracjaSkladu()
    pol = utworz_baze_demo()                   # <- tu później wstawisz polacz_postgres(...)
    zawodnicy = pobierz_zawodnikow(pol)

    wypisz_baze(zawodnicy)
    porownanie_naiwne(zawodnicy, konf)

    t0 = time.perf_counter()
    sklad, w, stat = zbuduj_sklad(zawodnicy, konf)
    czas = time.perf_counter() - t0
    if sklad is None:
        print("\n" + w)
        return

    print("\n=== Optymalny skład ===")
    wypisz_sklad(sklad, w, konf)
    pokaz_prace_algorytmu(zawodnicy, konf, stat)
    print(f"Czas działania algorytmu: {czas * 1000:.1f} ms")

    porownanie_wag(zawodnicy, konf)

    # autoweryfikacja: czy zgadza się z pełnym przeglądem?
    t0 = time.perf_counter()
    sklad_pp, wynik_pp = pelny_przeglad(zawodnicy, konf)
    czas_pp = time.perf_counter() - t0
    ok = sklad_pp is not None and abs(wynik_pp - w) < 1e-9
    print(f"\nWeryfikacja pełnym przeglądem ({czas_pp:.1f} s): {'zgodne ✔' if ok else 'NIEZGODNOŚĆ ✘'}")


if __name__ == "__main__":
    main()