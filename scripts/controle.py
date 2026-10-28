# -*- coding: utf-8 -*-
"""Controle de pre-publication du comparateur.

Usage :
    python3 scripts/controle.py \
        --comparateur COMPARATEUR_V2.xlsx \
        --fenetres donnees/fenetres.json \
        [--rapport sortie/controle.csv]

Rend 0 si aucune regle bloquante n'est enfreinte, 1 sinon. Une ligne bloquee ne
part pas en ligne, meme si tout le reste est pret : c'est la regle qui a manque
sur les onze lignes ecologie publiees avec cinq candidats sur trente et un.

Deux niveaux :
  BLOQUANT        la ligne ne peut pas etre publiee.
  A REGULARISER   deja en ligne ou sans risque immediat, mais a reprendre.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import openpyxl

PRET = u"Prêt pour publication"
VOTES = (u"Pour", u"Contre", u"Abstention", u"N'a pas pris part")
ABSENCE = u"Aucune position publique identifiée"

VOCABULAIRE = {
    u"État": {u"Prêt pour publication", u"En cours", u"À documenter"},
    u"Vote personnel": {u"Pour", u"Contre", u"Abstention", u"N'a pas pris part",
                        u"Non concerné", u"Sans objet", u""},
    u"Vote du groupe": {u"Pour", u"Contre", u"Abstention", u"Divisé",
                        u"Non applicable", u"Sans objet", u""},
    u"Alignement personne": {u"✅ Aligné", u"⚠️ Partiellement aligné", u"❌ Contraire",
                             u"➖ Non testable", u"🔀 Position hétérogène", u""},
    u"Alignement parti": {u"✅ Aligné", u"⚠️ Partiellement aligné", u"❌ Contraire",
                          u"➖ Non testable", u"🔀 Position hétérogène", u""},
}

JJMMAAAA = re.compile(r"\b\d{1,2}(?:er)?\s+\w+\s+\d{4}\b|\b\d{1,2}[/.-]\d{1,2}[/.-]\d{4}\b")


def propre(v):
    return str(v).replace("\r\n", "\n").strip() if v is not None else ""


def iso(s):
    from datetime import date
    return date(*(int(x) for x in s.split("-"))) if s else None


def lit_date(texte):
    from datetime import date
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b", propre(texte))
    if not m:
        return None
    j, mo, a = (int(x) for x in m.groups())
    try:
        return date(a, mo, j)
    except ValueError:
        return None


def onglet(wb, nom):
    ws = wb[nom]
    it = ws.iter_rows(values_only=True)
    e = [propre(c) for c in next(it)]
    i = {k: n for n, k in enumerate(e)}
    out = []
    for r in it:
        if not r or not r[0]:
            continue
        out.append({k: (propre(r[i[k]]) if i[k] < len(r) else "") for k in i if k})
    return out


def pouvait_voter(fiche, jour):
    for e in fiche["empeches"]:
        if iso(e["debut"]) <= jour <= iso(e["fin"]):
            return False
    for f in fiche["fenetres"]:
        fin = iso(f["fin"])
        if iso(f["debut"]) <= jour and (fin is None or jour <= fin):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparateur", required=True)
    ap.add_argument("--fenetres")
    ap.add_argument("--rapport")
    a = ap.parse_args()

    wb = openpyxl.load_workbook(a.comparateur, read_only=True, data_only=True)
    textes = onglet(wb, "1_TEXTES")
    pos = onglet(wb, "2_POSITIONS")
    cands = onglet(wb, "3_CANDIDATS")
    wb.close()
    noms = {c["Candidat"] for c in cands}
    dates = {t["Texte_ID"]: lit_date(t.get("Date", "")) for t in textes}
    ref = {}
    if a.fenetres:
        ref = json.loads(Path(a.fenetres).read_text(encoding="utf-8"))["candidats"]

    anomalies = []

    def note(niveau, regle, tid, cand, detail):
        anomalies.append({"niveau": niveau, "règle": regle, "Texte_ID": tid,
                          "Candidat": cand, "détail": detail})

    # R8 perimetre
    par_texte = {}
    for p in pos:
        par_texte.setdefault(p["Texte_ID"], []).append(p)
    for tid, bloc in sorted(par_texte.items()):
        vus = [b["Candidat"] for b in bloc]
        doublons = sorted({n for n in vus if vus.count(n) > 1})
        if doublons:
            note("BLOQUANT", "R8 périmètre", tid, "", u"candidats en double : %s" % ", ".join(doublons))
        absents = sorted(noms - set(vus))
        if absents:
            note("BLOQUANT", "R8 périmètre", tid, "",
                 u"%d candidat·es manquant·es : %s" % (len(absents), ", ".join(absents[:5])))

    for p in pos:
        tid, cand, etat = p["Texte_ID"], p["Candidat"], p.get(u"État", "")
        pret = etat == PRET
        vote = p.get("Vote personnel", "")

        if not pret:
            continue

        # R2 vocabulaire. Hors des cellules pretes, « a relever » est un marqueur
        # de travail legitime : on ne controle que ce qui part en ligne.
        for col, permis in VOCABULAIRE.items():
            v = p.get(col, "")
            if v and v not in permis:
                note("BLOQUANT", "R2 vocabulaire", tid, cand,
                     u"%s : %r hors liste" % (col, v[:40]))

        # R3 aucun residu
        for col, v in p.items():
            if v == u"à relever":
                note("BLOQUANT", u"R3 résidu", tid, cand, u"« à relever » dans %s" % col)

        # R4 un vote exige son releve
        if vote in VOTES and not p.get(u"Lien du relevé"):
            note("BLOQUANT", u"R4 source du vote", tid, cand,
                 u"vote « %s » sans lien de relevé" % vote)

        # R5 un non concerne exige sa cause, datee
        if vote == u"Non concerné":
            c = p.get(u"Cause si non concerné", "")
            if not c:
                note("BLOQUANT", "R5 cause", tid, cand, u"« Non concerné » sans cause")
            elif not JJMMAAAA.search(c):
                note(u"À RÉGULARISER", "R5 cause", tid, cand,
                     u"cause sans date : %s" % c[:60])

        # R6 rien sans source
        pp = p.get("PROMESSE de la personne", "")
        if pp and not p.get(u"Source promesse — PERSONNE"):
            if pp.startswith(ABSENCE):
                note(u"À RÉGULARISER", "R6 source", tid, cand,
                     u"absence de position affirmée sans nommer le document consulté")
            else:
                note("BLOQUANT", "R6 source", tid, cand, u"promesse sans source")
        pq = p.get("PROMESSE du parti", "")
        if pq and not pq.startswith(ABSENCE) and not p.get(u"Source promesse — PARTI"):
            note("BLOQUANT", "R6 source", tid, cand, u"promesse du parti sans source")

        # R7 coherence vote / fenetre de mandat
        fiche = ref.get(cand)
        jour = dates.get(tid)
        if fiche and jour and fiche["etat"] != "a_borner":
            if vote in VOTES and not pouvait_voter(fiche, jour):
                note("BLOQUANT", u"R7 cohérence mandat", tid, cand,
                     u"vote « %s » alors qu'il ou elle ne siégeait pas le %s"
                     % (vote, jour.strftime("%d/%m/%Y")))
            if vote == u"Non concerné" and pouvait_voter(fiche, jour):
                note(u"À RÉGULARISER", u"R7 cohérence mandat", tid, cand,
                     u"« Non concerné » alors qu'un mandat couvre le %s : à confirmer "
                     u"si le scrutin s'est tenu dans l'autre chambre"
                     % jour.strftime("%d/%m/%Y"))

    # R1 une ligne complete ou rien
    publiables, bloquees = [], []
    bloqueurs = {x["Texte_ID"] for x in anomalies if x["niveau"] == "BLOQUANT"}
    for tid, bloc in sorted(par_texte.items()):
        prets = [b for b in bloc if b.get(u"État") == PRET]
        if not prets:
            continue
        if len(prets) < len(noms):
            note("BLOQUANT", u"R1 ligne complète", tid, "",
                 u"%d cellules prêtes sur %d : la ligne ne part pas" % (len(prets), len(noms)))
            bloquees.append(tid)
        elif tid in bloqueurs:
            bloquees.append(tid)
        else:
            publiables.append(tid)

    bloquants = [x for x in anomalies if x["niveau"] == "BLOQUANT"]
    regulariser = [x for x in anomalies if x["niveau"] != "BLOQUANT"]

    print(u"textes : %d   cellules : %d   candidat·es : %d" % (len(textes), len(pos), len(noms)))
    print(u"\nlignes publiables : %d   %s" % (len(publiables), ", ".join(publiables)))
    print(u"lignes bloquées   : %d   %s" % (len(bloquees), ", ".join(bloquees)))
    print(u"\nanomalies bloquantes : %d" % len(bloquants))
    par_regle = {}
    for x in bloquants:
        par_regle[x[u"règle"]] = par_regle.get(x[u"règle"], 0) + 1
    for r, n in sorted(par_regle.items()):
        print(u"   %-24s %d" % (r, n))
    for x in bloquants[:25]:
        print(u"   %-24s %-10s %-24s %s" % (x[u"règle"], x["Texte_ID"], x["Candidat"][:24], x[u"détail"][:70]))
    if len(bloquants) > 25:
        print(u"   ... %d autres, voir le rapport" % (len(bloquants) - 25))

    print(u"\nà régulariser : %d" % len(regulariser))
    par_regle = {}
    for x in regulariser:
        par_regle[x[u"règle"]] = par_regle.get(x[u"règle"], 0) + 1
    for r, n in sorted(par_regle.items()):
        print(u"   %-24s %d" % (r, n))

    if a.rapport:
        Path(a.rapport).parent.mkdir(parents=True, exist_ok=True)
        with open(a.rapport, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["niveau", u"règle", "Texte_ID", "Candidat", u"détail"],
                               delimiter=";")
            w.writeheader()
            for x in anomalies:
                w.writerow(x)
        print(u"\nrapport : %s" % a.rapport)

    return 1 if bloquants else 0


if __name__ == "__main__":
    sys.exit(main())
