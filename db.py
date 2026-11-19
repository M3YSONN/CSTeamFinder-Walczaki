"""Warstwa dostępu do bazy danych: połączenie + wczytanie graczy z pozycjami."""
from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Gracz:
    id: int
    imie: str
    nazwisko: str
    nick: str
    wiek: int
    kraj: str
    rating: float
    rola: str
    # id_mapy -> zbiór id_pozycji (docelowo dokładnie jedna pozycja na mapę)
    pozycje: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))


@dataclass
class Dane:
    gracze: list[Gracz]
    mapy: dict[int, str]                  # id_mapy -> nazwa_mapy
    nazwy_pozycji: dict[int, str]         # id_pozycji -> nazwa_pozycji
    pozycje_na_mapie: dict[int, set[int]]  # id_mapy -> zbiór id_pozycji


SQL_GRACZE = """
    SELECT id_gracza, imie, nazwisko, nick, wiek, kraj, rating, rola
    FROM GRACZE
    ORDER BY id_gracza
"""

# GRACZ_POZYCJE nie ma kolumny id_mapy -> mapę bierzemy przez JOIN z POZYCJE
SQL_GRACZ_POZYCJE = """
    SELECT gp.id_gracza, p.id_mapy, p.id_pozycji
    FROM GRACZ_POZYCJE gp
    JOIN POZYCJE p ON p.id_pozycji = gp.id_pozycji
"""

SQL_MAPY = "SELECT id_mapy, nazwa_mapy FROM MAPY ORDER BY id_mapy"
SQL_POZYCJE = "SELECT id_pozycji, id_mapy, nazwa_pozycji FROM POZYCJE"


def polacz(typ: str = "postgres", **cfg):
    """Zwraca połączenie DB-API 2.0 do wybranej bazy.

    typ = "postgres" -> host, port, user, haslo, baza   (pip install psycopg2-binary)
    typ = "mysql"    -> host, port, user, haslo, baza   (pip install pymysql)
    typ = "sqlite"   -> plik
    Hasło, jeśli nie podane, brane jest ze zmiennej środowiskowej DB_PASSWORD.
    """
    haslo = cfg.get("haslo") or os.environ.get("DB_PASSWORD", "")

    if typ == "postgres":
        import psycopg2
        return psycopg2.connect(
            host=cfg.get("host") or "localhost", port=int(cfg.get("port") or 5432),
            user=cfg.get("user") or "postgres", password=haslo, dbname=cfg["baza"],
        )
    if typ == "mysql":
        import pymysql
        return pymysql.connect(
            host=cfg.get("host") or "localhost", port=int(cfg.get("port") or 3306),
            user=cfg.get("user") or "root", password=haslo,
            database=cfg["baza"], charset="utf8mb4",
        )
    if typ == "sqlite":
        return sqlite3.connect(cfg.get("plik") or "cs2.db")
    raise ValueError(f"Nieznany typ bazy: {typ}")


def wczytaj_dane(conn) -> Dane:
    cur = conn.cursor()

    cur.execute(SQL_GRACZE)
    gracze = {
        r[0]: Gracz(id=r[0], imie=(r[1] or "").strip(), nazwisko=(r[2] or "").strip(),
                    nick=(r[3] or "").strip(), wiek=r[4], kraj=(r[5] or "").strip(),
                    rating=float(r[6] or 0), rola=(r[7] or "").strip())
        for r in cur.fetchall()
    }

    cur.execute(SQL_GRACZ_POZYCJE)
    for id_gracza, id_mapy, id_pozycji in cur.fetchall():
        if id_gracza in gracze:
            gracze[id_gracza].pozycje[id_mapy].add(id_pozycji)

    cur.execute(SQL_MAPY)
    mapy = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute(SQL_POZYCJE)
    nazwy_pozycji, pozycje_na_mapie = {}, defaultdict(set)
    for id_pozycji, id_mapy, nazwa in cur.fetchall():
        nazwy_pozycji[id_pozycji] = nazwa
        pozycje_na_mapie[id_mapy].add(id_pozycji)

    cur.close()
    return Dane(list(gracze.values()), mapy, nazwy_pozycji, dict(pozycje_na_mapie))


def sprawdz_dane(dane: Dane) -> list[str]:
    """Zwraca listę ostrzeżeń o niespójnościach w danych (nie przerywa działania)."""
    uwagi = []
    for g in dane.gracze:
        brak = [dane.mapy[m] for m in dane.mapy if not g.pozycje.get(m)]
        wiele = [f"{dane.mapy[m]}×{len(p)}" for m, p in g.pozycje.items() if len(p) > 1]
        if brak or wiele:
            opis = []
            if brak:
                opis.append("brak pozycji na: " + ", ".join(brak))
            if wiele:
                opis.append("kilka pozycji na: " + ", ".join(wiele))
            uwagi.append(f"gracz {g.id} ({g.nick}) – " + "; ".join(opis))
    for m, pozycje in dane.pozycje_na_mapie.items():
        if len(pozycje) < 5:
            uwagi.append(f"mapa {dane.mapy.get(m, m)} ma tylko {len(pozycje)} pozycje "
                         f"(5 graczy nie zmieści się bez powtórzeń)")
    rolki = {g.rola.lower() for g in dane.gracze}
    if "igl" not in rolki:
        uwagi.append("w bazie nie ma żadnego gracza z rolą IGL")
    if not rolki & {"sniper", "awp"}:
        uwagi.append("w bazie nie ma żadnego gracza z rolą Sniper/AWP")
    return uwagi
