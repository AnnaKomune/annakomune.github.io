# -*- coding: utf-8 -*-
"""Reconstruit candidats/data.js depuis CANDIDATS.xlsx.

Usage :
    python3 scripts/candidats_data.py \\
        --candidats CANDIDATS.xlsx \\
        --programmes programmes/data.js \\
        --sortie candidats/data.js

La colonne « Notes internes (non publié) » n'est jamais exportee : elle porte
les arbitrages et les points a verifier, qui ne sont pas publiables.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

import openpyxl

ONGLET = "Candidats"

# Colonne du classeur -> champ du fichier publie. Ce qui n'est pas dans cette
# table ne sort pas, a commencer par les notes internes.
CHAMPS = [
    ("parti", "Parti"),
    ("statut", "Statut de déclaration"),
    ("date", "Date de déclaration"),
    ("p_parl_now", "Parl. en cours"),
    ("p_parl_past", "Parl. passé"),
    ("p_gouv", "Gouv. (passé ou en cours)"),
    ("p_loc_now", "Local en cours"),
    ("p_loc_past", "Local passé"),
    ("parl_now", "Mandat parlementaire actuel"),
    ("parl_past", "Mandats parlementaires passés"),
    ("gouv", "Fonctions gouvernementales"),
    ("local", "Mandats locaux actuels et passés"),
    ("profession", "Profession"),
    ("fonctions", "Fonctions non électives (parti, groupe, organismes)"),
    ("prog", "Programme"),
    ("prog_url", "Lien programme"),
    ("site", "Site de campagne"),
    ("prog_detail", "Sources pour l'onglet \"Promesses\""),
    ("votes", "Fenêtre de votes personnels"),
    ("faits", "Faits importants"),
    ("judiciaire", "Situation judiciaire"),
    ("verif", "Statut de vérification"),
    ("sources", "Sources"),
]

INTERDIT = "Notes internes"

# Corrections demandees par le document de mise a jour (onglets 1_MESURES et
# 6_CONTROLES) et que les classeurs ne portent pas encore. Chacune est une
# consigne ecrite de la redaction, pas une initiative : Raphael Glucksmann a
# remporte la primaire le 11 octobre 2026, il n'y est donc plus candidat.
CORRECTIONS = {
    "Raphaël Glucksmann": {"statut": "déclaré"},
}


def propre(v):
    if v is None:
        return ""
    return str(v).replace("\r\n", "\n").strip()


def affiche(v):
    """Valeur destinee a l'ecran : jamais de tiret cadratin."""
    return propre(v).replace("—", "-").replace("–", "-")


def slug(texte):
    t = unicodedata.normalize("NFD", propre(texte))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()


def compte_mesures(chemin_programmes):
    """Combien de mesures chaque candidat·e porte en son nom propre."""
    t = Path(chemin_programmes).read_text(encoding="utf-8")
    p = json.loads(t[t.find("{"):].rstrip().rstrip(";"))
    c = Counter()
    for m in p["mesures"]:
        doc = p["docs"][m[8]]
        if doc.get("cand"):
            c[doc["cand"]] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidats", required=True)
    ap.add_argument("--programmes", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()

    compte = compte_mesures(a.programmes)
    wb = openpyxl.load_workbook(a.candidats, read_only=True, data_only=True)
    ws = wb[ONGLET]
    it = ws.iter_rows(values_only=True)
    entetes = [propre(c) for c in next(it)]
    assert any(e.startswith(INTERDIT) for e in entetes), \
        "la colonne des notes internes a disparu : verifier le classeur"
    index = {e: i for i, e in enumerate(entetes)}

    fiches = []
    for brut in it:
        if brut is None:
            continue
        nom = affiche(brut[0]) if brut else ""
        if not nom:
            continue
        f = {"nom": nom}
        for cle, colonne in CHAMPS:
            i = index.get(colonne)
            f[cle] = affiche(brut[i]) if i is not None and i < len(brut) else ""
        f.update(CORRECTIONS.get(nom, {}))
        f["slug"] = slug(nom)
        f["n_mesures"] = compte.get(nom, 0)
        fiches.append(f)
    wb.close()

    sortie = {"maj": date.today().isoformat(), "candidats": fiches}
    corps = json.dumps(sortie, ensure_ascii=False, separators=(",", ":"))
    assert INTERDIT not in corps, "des notes internes se sont glissees dans la sortie"
    Path(a.sortie).write_text("window.KOMUNE_CANDIDATS = " + corps + ";\n", encoding="utf-8")

    print("fiches : %d" % len(fiches))
    sans = [f["nom"] for f in fiches if not f["n_mesures"]]
    print("sans mesure au referentiel : %d  %s" % (len(sans), ", ".join(sans)))


if __name__ == "__main__":
    main()
