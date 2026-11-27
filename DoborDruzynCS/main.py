from __future__ import annotations

import argparse
import os
import statistics
import time

from algorytm import Ocena, algorytm_genetyczny, dobor_wezykiem
from db import polacz, sprawdz_dane, wczytaj_dane


def argumenty():
    e = os.environ.get
    p = argparse.ArgumentParser(description="Dobór drużyn CS2 – algorytm genetyczny")
    g = p.add_argument_group("baza danych (domyślnie ze zmiennych środowiskowych DB_*)")
    g.add_argument("--typ", default=e("DB_TYP", "postgres"), choices=["postgres", "mysql", "sqlite"])
    g.add_argument("--host", default=e("DB_HOST", "localhost"))
    g.add_argument("--port", default=e("DB_PORT"))
    g.add_argument("--user", default=e("DB_USER", "postgres"))
    g.add_argument("--baza", default=e("DB_NAME", "cs2"))
    g.add_argument("--plik", default=e("DB_FILE", "cs2.db"), help="plik dla --typ sqlite")
    a = p.add_argument_group("algorytm genetyczny")
    a.add_argument("--rozmiar", type=int, default=5, help="graczy w drużynie")
    a.add_argument("--populacja", type=int, default=150)
    a.add_argument("--pokolenia", type=int, default=800)
    a.add_argument("--mutacja", type=float, default=0.5)
    a.add_argument("--krzyzowanie", type=float, default=0.9)
    a.add_argument("--seed", type=int, default=None, help="ziarno losowania (powtarzalność)")
    p.add_argument("--cicho", action="store_true", help="nie pokazuj ostrzeżeń o danych")
    return p.parse_args()


def wypisz_druzyny(tytul, druzyny, ocena, gracze, nazwy_map):
    fitness, oceny = ocena.podzial(druzyny)
    print(f"\n{'=' * 78}\n{tytul}   (fitness = {fitness:.4f})\n{'=' * 78}")
    for nr, (sklad, o) in enumerate(sorted(zip(druzyny, oceny), key=lambda x: -x[1]["F"]), 1):
        print(f"\nDrużyna {nr:2d} | F={o['F']:.3f} | R={o['R']:.2f} S={o['S']:.2f} "
              f"P={o['P']:.2f} K={o['K']:.2f} | śr. rating {o['sr_rating']:.3f}")
        for i in sorted(sklad, key=lambda i: -gracze[i].rating):
            g = gracze[i]
            print(f"     {g.nick:<12} {g.rola:<7} {g.rating:4.2f}  {g.kraj}")
    return fitness, oceny


def podsumowanie(nazwa, fitness, oceny):
    F = [o["F"] for o in oceny]
    sr = [o["sr_rating"] for o in oceny]
    return {
        "metoda": nazwa,
        "fitness": fitness,
        "śr. F": statistics.mean(F),
        "min F": min(F),
        "max F": max(F),
        "rozrzut F": max(F) - min(F),
        "rozrzut ratingu": max(sr) - min(sr),
        "odch. std ratingu": statistics.pstdev(sr),
        "bez IGL": sum(o["igl"] == 0 for o in oceny),
        "bez snipera": sum(o["sniper"] == 0 for o in oceny),
        "śr. R": statistics.mean(o["R"] for o in oceny),
        "śr. S": statistics.mean(o["S"] for o in oceny),
        "śr. P": statistics.mean(o["P"] for o in oceny),
        "śr. K": statistics.mean(o["K"] for o in oceny),
    }


def main():
    args = argumenty()

    conn = polacz(args.typ, host=args.host, port=args.port, user=args.user,
                  baza=args.baza, plik=args.plik)
    try:
        dane = wczytaj_dane(conn)
    finally:
        conn.close()

    gracze = dane.gracze
    liczba_druzyn = len(gracze) // args.rozmiar
    print(f"Wczytano {len(gracze)} graczy, {len(dane.mapy)} map, "
          f"{len(dane.nazwy_pozycji)} pozycji -> {liczba_druzyn} drużyn po {args.rozmiar}")
    if len(gracze) % args.rozmiar:
        print(f"Uwaga: {len(gracze) % args.rozmiar} graczy zostanie w rezerwie.")

    uwagi = sprawdz_dane(dane)
    if uwagi and not args.cicho:
        print(f"\n⚠ Wykryto {len(uwagi)} niespójności w danych (pierwsze 10):")
        for u in uwagi[:10]:
            print("   -", u)

    ocena = Ocena(dane, args.rozmiar)

    wezyk = dobor_wezykiem(ocena, liczba_druzyn)
    f_w, o_w = wypisz_druzyny("DOBÓR WĘŻYKIEM (snake draft wg ratingu)", wezyk, ocena,
                              gracze, dane.mapy)

    print("\nAlgorytm genetyczny...")
    t0 = time.perf_counter()
    ag, historia = algorytm_genetyczny(
        ocena, liczba_druzyn, populacja=args.populacja, pokolenia=args.pokolenia,
        p_mutacji=args.mutacja, p_krzyzowania=args.krzyzowanie, seed=args.seed)
    czas = time.perf_counter() - t0
    f_g, o_g = wypisz_druzyny(f"ALGORYTM GENETYCZNY ({len(historia) - 1} pokoleń, {czas:.1f} s)",
                              ag, ocena, gracze, dane.mapy)

    w, g = podsumowanie("Wężyk", f_w, o_w), podsumowanie("Genetyczny", f_g, o_g)
    print(f"\n{'=' * 50}\nPORÓWNANIE\n{'=' * 50}")
    print(f"{'miara':<20}{'Wężyk':>14}{'Genetyczny':>14}")
    for k in w:
        if k == "metoda":
            continue
        fmt = "{:>14d}" if isinstance(w[k], int) else "{:>14.4f}"
        print(f"{k:<20}" + fmt.format(w[k]) + fmt.format(g[k]))


if __name__ == "__main__":
    main()
