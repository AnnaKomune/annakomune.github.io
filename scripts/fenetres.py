# -*- coding: utf-8 -*-
"""Construit le referentiel des fenetres de mandat : donnees/fenetres.json.

Usage :
    python3 scripts/fenetres.py --comparateur COMPARATEUR_V2.xlsx --sortie donnees/fenetres.json

La colonne « Fenetre de votes personnels » de l'onglet 3_CANDIDATS est ecrite en
prose. Ce script ne la lit pas automatiquement : les bornes ci-dessous ont ete
relevees a la main depuis cette prose.

Deux sorties, et la distinction compte :
  --sortie   le referentiel publie. Il ne porte QUE les bornes de dates. Le
             depot est public : la prose de travail de la redaction n'y entre
             pas.
  --audit    la meme chose avec, pour chaque fiche, le verbatim dont les bornes
             sont tirees, pour verifier d'un coup d'oeil. Ce fichier reste sur
             le poste de la redaction et ne se publie jamais.

Trois etats possibles :
  jamais    aucun mandat parlementaire, a aucun moment. Toujours « non concerne ».
  borne     les fenetres sont datees, le derive est autorise.
  a_borner  la prose ne donne pas de dates sures. AUCUN derive n'est produit, la
            cellule reste a ecrire a la main. C'est volontaire : mieux vaut un
            trou signale qu'une date inventee.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import openpyxl

JAMAIS = "jamais"
BORNE = "borne"
A_BORNER = "a_borner"

# chambre : AN = Assemblee nationale, SENAT = Senat, PE = Parlement europeen.
# debut et fin au format AAAA-MM-JJ ; fin = null signifie « toujours en cours ».
# Les trous (periode ministerielle, suppleance) sont des fenetres a part, de
# type « empeche », avec le motif qui sera affiche au lecteur.
FICHES = {
    "Jean-Luc Mélenchon": (BORNE, [
        ("AN", "2017-06-18", "2022-06-21", None),
        ("SENAT", "1986-10-02", "2000-03-27", None),
        ("PE", "2009-07-14", "2017-06-18", "votes europeens uniquement"),
    ], [("2000-03-27", "2002-05-06", "membre du gouvernement")]),
    "Marine Le Pen": (BORNE, [
        ("AN", "2017-06-18", None, None),
        ("PE", "2004-07-20", "2017-06-18", "votes europeens uniquement"),
    ], []),
    "Gabriel Attal": (A_BORNER, [
        ("AN", "2024-07-07", None, None),
    ], [], u"la prose borne la periode recente mais ne dit pas si les mandats "
        u"anterieurs a 2024 ouvrent des votes. A trancher avant tout derive."),
    "Édouard Philippe": (A_BORNER, [], [],
        u"« ni depute ni senateur depuis 2020 » ne dit rien de la periode "
        u"anterieure. A borner avant tout derive."),
    "Bruno Retailleau": (BORNE, [
        ("SENAT", "2004-09-26", None, None),
    ], [("2024-09-21", "2025-10-12", "membre du gouvernement")]),
    "David Lisnard": (JAMAIS, [], [], u"N'a jamais ete depute ni senateur."),
    "Xavier Bertrand": (A_BORNER, [], [],
        u"la fiche demande elle-meme de borner precisement les trois fenetres "
        u"2002-2004, 2009-2010 et 2012-2016 avant publication."),
    "Fabien Roussel": (BORNE, [
        ("AN", "2017-06-21", "2024-06-09", None),
    ], []),
    "Marine Tondelier": (JAMAIS, [], [], u"N'a exerce aucun mandat parlementaire."),
    "François Ruffin": (BORNE, [
        ("AN", "2017-06-18", None, None),
    ], []),
    "Karim Bouamrane": (JAMAIS, [], [], u"Aucun mandat de depute ou de senateur enregistre."),
    "Delphine Batho": (BORNE, [
        ("AN", "2007-06-17", None, None),
    ], [("2012-05-16", "2013-08-03", "membre du gouvernement")]),
    "Nathalie Arthaud": (JAMAIS, [], [], u"Aucun mandat local ou national."),
    "Anasse Kazib": (JAMAIS, [], [], u"N'a jamais exerce de fonction legislative ou executive."),
    "Selma Labib": (JAMAIS, [], [], u"Aucun mandat de depute ou de senateur enregistre."),
    "Lydie Massard": (A_BORNER, [], [],
        u"des votes au Parlement europeen sont cites sans dates de mandat. A borner."),
    "Antoine Mikolajczak": (JAMAIS, [], [], u"Aucun mandat."),
    "Clara Egger": (JAMAIS, [], [], u"Aucun mandat."),
    "Manolo Mlekuz": (JAMAIS, [], [], u"Aucun mandat."),
    "Florian Philippot": (A_BORNER, [], [],
        u"des votes au Parlement europeen sont cites sans dates de mandat. A borner."),
    "François Asselineau": (A_BORNER, [], [],
        u"la case est vide dans le classeur : rien a deriver."),
    "Nicolas Dupont-Aignan": (BORNE, [
        ("AN", "1997-06-01", "2024-06-09", None),
    ], []),
    "Juan Branco": (JAMAIS, [], [], u"Aucun mandat."),
    "Francis Lalanne": (JAMAIS, [], [], u"N'a jamais exerce de mandat."),
    "Benoît Mathieu": (JAMAIS, [], [], u"Aucun mandat."),
    "Raphaël Glucksmann": (A_BORNER, [], [],
        u"des votes au Parlement europeen sont cites sans dates de mandat. A borner."),
    "Bernard Cazeneuve": (A_BORNER, [], [],
        u"la fiche ecarte ses votes sans donner de bornes. A trancher."),
    "Éric Zemmour": (JAMAIS, [], [], u"N'a jamais occupe de mandat electif."),
    "Olivier Becht": (BORNE, [
        ("AN", "2017-06-18", "2022-08-04", None),
        ("AN", "2024-02-12", None, None),
    ], [("2022-07-04", "2024-01-11", "membre du gouvernement")]),
    "Mira Markovic": (JAMAIS, [], [], u"Aucun mandat parlementaire."),
    "Natacha Polony": (JAMAIS, [], [], u"Aucun mandat electif."),
}

CHAMBRES = {"AN": u"l'Assemblée nationale", "SENAT": u"au Sénat", "PE": u"au Parlement européen"}


def verbatim(chemin):
    """La prose d'origine, pour que chaque borne reste verifiable."""
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    ws = wb["3_CANDIDATS"]
    it = ws.iter_rows(values_only=True)
    entetes = [str(c).strip() if c is not None else "" for c in next(it)]
    i = entetes.index(u"Fenêtre de votes personnels")
    out = {}
    for r in it:
        if not r or not r[0]:
            continue
        v = r[i] if i < len(r) else None
        out[str(r[0]).strip()] = (str(v).replace("\r\n", "\n").strip() if v is not None else "")
    wb.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparateur", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--audit", help=u"copie locale avec le verbatim. Ne jamais publier.")
    a = ap.parse_args()

    prose = verbatim(a.comparateur)
    manquants = sorted(set(prose) - set(FICHES))
    surplus = sorted(set(FICHES) - set(prose))
    assert not manquants, u"candidats du classeur absents du referentiel : %s" % manquants
    assert not surplus, u"candidats du referentiel absents du classeur : %s" % surplus

    fiches = {}
    for nom, bloc in FICHES.items():
        etat, fen, trous = bloc[0], bloc[1], bloc[2]
        note = bloc[3] if len(bloc) > 3 else ""
        fiches[nom] = {
            "etat": etat,
            "fenetres": [{"chambre": c, "debut": d, "fin": f, "note": n or ""} for c, d, f, n in fen],
            "empeches": [{"debut": d, "fin": f, "motif": m} for d, f, m in trous],
            "note": note,
        }

    sortie = {
        "maj": date.today().isoformat(),
        "source": u"COMPARATEUR_V2.xlsx, onglet 3_CANDIDATS, colonne « Fenêtre de votes personnels »",
        "candidats": fiches,
    }
    corps = json.dumps(sortie, ensure_ascii=False, indent=1, sort_keys=True)
    for n in prose:
        extrait = prose[n][:40]
        assert not extrait or extrait not in corps, \
            u"du verbatim s'est glisse dans le fichier publie : %s" % n
    Path(a.sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(a.sortie).write_text(corps, encoding="utf-8")

    if a.audit:
        complet = dict(sortie)
        complet["avertissement"] = (u"Copie de verification. Contient la prose de "
                                    u"travail de la redaction : ne pas publier.")
        complet["candidats"] = {n: dict(f, verbatim=prose[n]) for n, f in fiches.items()}
        Path(a.audit).parent.mkdir(parents=True, exist_ok=True)
        Path(a.audit).write_text(
            json.dumps(complet, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    compte = {}
    for f in fiches.values():
        compte[f["etat"]] = compte.get(f["etat"], 0) + 1
    print(u"candidats : %d" % len(fiches))
    for e in (JAMAIS, BORNE, A_BORNER):
        print(u"  %-9s %d" % (e, compte.get(e, 0)))
    reste = sorted(n for n, f in fiches.items() if f["etat"] == A_BORNER)
    if reste:
        print(u"a borner avant tout derive : %s" % ", ".join(reste))
    print(u"\npublie  : %s  (bornes seules)" % a.sortie)
    if a.audit:
        print(u"local   : %s  (avec le verbatim, ne pas publier)" % a.audit)


if __name__ == "__main__":
    main()
