# -*- coding: utf-8 -*-
"""Reconstruit programmes/data.js et programmes/textes.js depuis le referentiel.

Usage :
    python3 scripts/programmes_data.py \\
        --referentiel KOMUNE_PROMESSES_PROGRAMMES_DECLARATIONS.xlsx \\
        --dossier programmes

Les deux fichiers sont des tables indexees : les libelles qui se repetent
(themes, sous-themes, tags, documents, URL, parties, chapitres) sont stockes une
fois et les mesures n'en portent que le rang. C'est ce qui tient la taille du
fichier malgre les milliers de lignes.
"""
import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import openpyxl

ONGLET = "01_MESURES_PROGRAMMATIQUES"
ONGLET_ETAT = "05_ETAT_DES_PROGRAMMES"

# Une version qui correspond a une election porte un libelle court. « passe »
# distingue les corpus d'une election anterieure de ceux de la campagne en cours.
SCRUTINS = {
    "2022": ("Prés. 2022", 1),
    "2022, présidentielle": ("Prés. 2022", 1),
    "2024, européennes": ("Euro. 2024", 1),
    "2024, législatives": ("Légis. 2024", 1),
    "2025, législatives partielles": ("Légis. part. 2025", 1),
    "2026, municipales": ("Munic. 2026", 1),
}


def propre(v):
    if v is None:
        return ""
    return str(v).replace("\r\n", "\n").strip()


def affiche(v):
    """Une valeur destinee a l'ecran : la redaction n'affiche jamais de tiret
    cadratin. Le classeur en contient, on les convertit a la sortie sans y
    toucher. Les en-tetes de colonnes, eux, restent intacts : ce sont des cles."""
    return propre(v).replace("\u2014", "-").replace("\u2013", "-")


def slug(texte):
    t = unicodedata.normalize("NFD", propre(texte))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()


class Table(object):
    """Une table de libelles : rend le rang, en ajoutant la valeur au besoin."""

    def __init__(self):
        self.valeurs = []
        self._rang = {}

    def rang(self, valeur):
        cle = json.dumps(valeur, ensure_ascii=False, sort_keys=True)
        if cle not in self._rang:
            self._rang[cle] = len(self.valeurs)
            self.valeurs.append(valeur)
        return self._rang[cle]


def numero_theme(libelle):
    """« 5. Écologie & climat » rend 5."""
    m = re.match(r"\s*(\d+)\s*\.", propre(libelle))
    return int(m.group(1)) if m else 0


def libelle_theme(libelle):
    return re.sub(r"^\s*\d+\s*\.\s*", "", propre(libelle))


def source(version):
    v = propre(version)
    if v.startswith("2027"):
        return "Prés. 2027", 0
    if v in SCRUTINS:
        return SCRUTINS[v]
    return v, 0


def lignes(ws, entete_attendue=None):
    """Les lignes d'un onglet. entete_attendue permet de sauter les lignes de
    presentation qui precedent le tableau."""
    it = ws.iter_rows(values_only=True)
    entetes = None
    for brut in it:
        cellules = [propre(c) for c in (brut or [])]
        if entete_attendue is None or entete_attendue in cellules:
            entetes = cellules
            break
    if entetes is None:
        return
    for brut in it:
        if brut is None or not any(c is not None and propre(c) for c in brut):
            continue
        yield {k: (affiche(brut[i]) if i < len(brut) else "")
               for i, k in enumerate(entetes) if k}


def construit(referentiel, dossier):
    wb = openpyxl.load_workbook(referentiel, read_only=True, data_only=True)
    mesures_brutes = list(lignes(wb[ONGLET]))

    themes = {}
    sous, tags, urls, qual, parts, chaps, docs = (Table() for _ in range(7))
    mesures, textes = [], {}
    compte_doc = {}

    for r in mesures_brutes:
        mid = r.get("ID mesure", "")
        if not mid:
            continue
        num = numero_theme(r.get("Thématique principale"))
        themes.setdefault(str(num), libelle_theme(r.get("Thématique principale")))

        ver = r.get("Version", "")
        src, passe = source(ver)
        cand = r.get("Candidat·e", "")
        fiche = {"doc": r.get("Document source", ""), "url": r.get("URL source", ""),
                 "parti": r.get("Parti", ""), "ver": ver, "src": src, "passe": passe}
        if cand:
            fiche["cand"] = cand
            fiche["cslug"] = slug(cand)
        idoc = docs.rang(fiche)
        compte_doc[idoc] = compte_doc.get(idoc, 0) + 1

        ipart = parts.rang(r.get("Partie", ""))
        ich = chaps.rang([ipart, r.get("Chapitre / Étape", "")])
        ist = sous.rang([num, r.get("Sous-thème", "")])
        iu = urls.rang(r.get("URL source", ""))
        iq = qual.rang(r.get("Qualité intitulé court", ""))
        itags = [tags.rang(x.strip()) for x in r.get("Tags", "").split("·") if x.strip()]

        double = numero_theme(r.get("Double étiquette")) or None

        mesures.append([mid, r.get("Réf. programme", ""),
                        r.get("Intitulé court (comparateur)", ""),
                        iq, num, ist, double, itags, idoc, ich, iu])

        # Le texte integral, et de quoi retrouver l'intitule long : sa longueur
        # quand il ouvre le texte, son libelle entier sinon.
        texte = r.get("Texte intégral (verbatim)", "")
        lng = r.get("Intitulé long", "")
        fin = {"t": texte}
        if lng and texte.startswith(lng):
            fin["n"] = len(lng)
        elif lng:
            fin["l"] = lng
        textes[mid] = fin

    for i, f in enumerate(docs.valeurs):
        f["n"] = compte_doc.get(i, 0)

    etat = []
    for r in lignes(wb[ONGLET_ETAT], "Candidat·e"):
        cand = r.get("Candidat·e", "")
        if not cand or cand.startswith("Candidat"):
            continue
        etat.append({
            "cand": cand,
            "parti": r.get("Parti", ""),
            "candidat2027": r.get("Candidat·e \npour 2027 ?") or r.get("Candidat·e pour 2027 ?", ""),
            "etat": r.get("État du programme 2027", ""),
            "consigne": r.get("Ce qui est consigné", ""),
            "n": r.get("Lignes au référentiel", ""),
        })
    wb.close()

    sortie = {
        "maj": date.today().isoformat(),
        "themes": {k: themes[k] for k in sorted(themes, key=int)},
        "sous": sous.valeurs,
        "tags": tags.valeurs,
        "urls": urls.valeurs,
        "qual": qual.valeurs,
        "parts": parts.valeurs,
        "chaps": chaps.valeurs,
        "docs": docs.valeurs,
        "cles": ["id", "ref", "court", "qual", "theme", "st", "theme2", "tags", "d", "ch", "u"],
        "mesures": mesures,
        "etat": etat,
    }

    dossier = Path(dossier)
    (dossier / "data.js").write_text(
        "window.KOMUNE_PROGRAMMES = "
        + json.dumps(sortie, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    (dossier / "textes.js").write_text(
        "window.KOMUNE_TEXTES = "
        + json.dumps(textes, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    print("mesures : %d" % len(mesures))
    print("documents : %d  (dont %d d'une election anterieure)"
          % (len(docs.valeurs), sum(1 for f in docs.valeurs if f["passe"])))
    print("themes : %d | sous-themes : %d | tags : %d | parties : %d | chapitres : %d"
          % (len(themes), len(sous.valeurs), len(tags.valeurs), len(parts.valeurs), len(chaps.valeurs)))
    print("etat des programmes : %d lignes" % len(etat))
    print("textes : %d (dont %d avec un intitule long distinct)"
          % (len(textes), sum(1 for v in textes.values() if "l" in v)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--referentiel", required=True)
    ap.add_argument("--dossier", required=True)
    a = ap.parse_args()
    construit(a.referentiel, a.dossier)


if __name__ == "__main__":
    main()
