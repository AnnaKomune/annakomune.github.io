# -*- coding: utf-8 -*-
"""Remplit les votes personnels a partir des scrutins officiels.

Usage :
    python3 scripts/scrutins.py \
        --releve donnees/scrutins-an.json \
        --comparateur COMPARATEUR_V2.xlsx \
        --sortie sortie/votes.csv

Le releve est produit par le navigateur, avec scripts/releve_scrutins.js : les
serveurs de l'Assemblee et du Senat ne sont pas joignables depuis l'atelier, il
faut passer par le Chrome de la redaction. Une fois le releve en main, ce script
tourne hors ligne.

Il ne corrige rien tout seul. Pour chaque cellule il dit :
  a remplir    la case est vide, le scrutin donne la valeur
  confirme     la case et le scrutin disent la meme chose
  DIVERGENCE   la case et le scrutin se contredisent. A trancher a la main.
"""
import argparse
import csv
import json
from pathlib import Path

import openpyxl

# Le vocabulaire de l'Assemblee vers celui du tableau.
POSITIONS = {
    "Pour": "Pour",
    "Contre": "Contre",
    "Abstention": "Abstention",
    "Non votant": u"N'a pas pris part",
    "Non-votant": u"N'a pas pris part",
    u"Non votant volontaire": u"N'a pas pris part",
}


def propre(v):
    return str(v).replace("\r\n", "\n").strip() if v is not None else ""


def positions(chemin):
    wb = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    ws = wb["2_POSITIONS"]
    it = ws.iter_rows(values_only=True)
    e = [propre(c) for c in next(it)]
    i = {k: n for n, k in enumerate(e)}
    out = {}
    for r in it:
        if not r or not r[0]:
            continue
        g = lambda k: propre(r[i[k]]) if k in i and i[k] < len(r) else ""
        out[(g("Texte_ID"), g("Candidat"))] = {
            "vote": g("Vote personnel"), "groupe": g("Vote du groupe"),
            "detail": g(u"Détail chiffré du groupe"), "lien": g(u"Lien du relevé"),
            "etat": g(u"État"),
        }
    wb.close()
    return out


def chiffre(groupes, sigle):
    """Le detail chiffre d'un groupe, dans la forme utilisee par le tableau."""
    pos = groupes.get(sigle) or {}
    bouts = [u"%s : %d" % (p, n[0]) for p, n in sorted(pos.items(), key=lambda x: -x[1][0])]
    return u"%s\n%s" % (sigle, u"\n".join(bouts)) if bouts else sigle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--releve", required=True)
    ap.add_argument("--comparateur", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()

    releve = json.loads(Path(a.releve).read_text(encoding="utf-8"))
    pos = positions(a.comparateur)

    par_texte = {}
    for s in releve:
        par_texte.setdefault(s["id"], []).append(s)

    lignes, divergences, multiples, inconnues = [], [], [], []
    for tid, scrs in sorted(par_texte.items()):
        if len(scrs) > 1:
            multiples.append((tid, [s["num"] for s in scrs]))
        for s in scrs:
            if s.get("erreur"):
                inconnues.append((tid, s.get("num"), s["erreur"]))
                continue
            for nom, position, sigle, fiche in s["trouves"]:
                valeur = POSITIONS.get(position)
                if valeur is None:
                    inconnues.append((tid, s["num"], u"position inconnue : %s" % position))
                    continue
                cur = pos.get((tid, nom))
                if cur is None:
                    inconnues.append((tid, s["num"], u"%s absent du tableau" % nom))
                    continue
                if not cur["vote"] or cur["vote"] == u"à relever":
                    statut = u"à remplir"
                elif cur["vote"] == valeur:
                    statut = u"confirmé"
                else:
                    statut = u"DIVERGENCE"
                    divergences.append((tid, s["num"], nom, cur["vote"], valeur))
                lignes.append({
                    "Texte_ID": tid, "Candidat": nom,
                    "Vote personnel": valeur,
                    "Groupe": sigle,
                    u"Détail chiffré du groupe": chiffre(s["groupes"], sigle),
                    u"Lien du relevé": s["source"],
                    "Scrutin": u"Scrutin public n°%s, %s" % (s["num"], s["meta"].get("seance", "")),
                    "Issue": s["meta"].get("issue", ""),
                    "statut": statut,
                    "valeur actuelle": cur["vote"],
                })

    Path(a.sortie).parent.mkdir(parents=True, exist_ok=True)
    champs = ["Texte_ID", "Candidat", "Vote personnel", "Groupe",
              u"Détail chiffré du groupe", u"Lien du relevé", "Scrutin", "Issue",
              "statut", "valeur actuelle"]
    with open(a.sortie, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, delimiter=";")
        w.writeheader()
        for l in lignes:
            w.writerow(l)

    compte = {}
    for l in lignes:
        compte[l["statut"]] = compte.get(l["statut"], 0) + 1
    print(u"scrutins relevés : %d  sur %d textes" % (len(releve), len(par_texte)))
    print(u"votes personnels identifiés : %d" % len(lignes))
    for k in (u"à remplir", u"confirmé", u"DIVERGENCE"):
        print(u"   %-12s %d" % (k, compte.get(k, 0)))
    if multiples:
        print(u"\ntextes à plusieurs scrutins : le tableau ne porte qu'un vote par candidat,")
        print(u"il faut choisir le scrutin de référence ou scinder la ligne.")
        for tid, nums in multiples:
            print(u"   %-10s %s" % (tid, ", ".join(u"n°" + n for n in nums)))
    if divergences:
        print(u"\nDIVERGENCES à trancher :")
        for tid, num, nom, actuel, propose in divergences:
            print(u"   %-10s n°%-6s %-24s tableau : %-16s scrutin : %s"
                  % (tid, num, nom, actuel, propose))
    if inconnues:
        print(u"\npoints à vérifier : %d" % len(inconnues))
        for x in inconnues[:12]:
            print(u"   %s" % (x,))
    print(u"\nfichier : %s" % a.sortie)


if __name__ == "__main__":
    main()
