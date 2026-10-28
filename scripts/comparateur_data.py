# -*- coding: utf-8 -*-
"""Reconstruit comparateur/data.js a partir des trois classeurs de la redaction.

Usage :
    python3 scripts/comparateur_data.py \\
        --comparateur COMPARATEUR_V2.xlsx \\
        --candidats CANDIDATS.xlsx \\
        --sortie comparateur/data.js

Ce qui est REGENERE depuis les classeurs : CANDIDATS, LOIS, ATTENTE.
Ce qui est REPRIS tel quel du data.js existant : FICHES, SOURCES, JEU, QUICK,
PARCOURS, MEDEF, JOUEURS, ainsi que les champs redactionnels des lois deja en
ligne (soustitre, chapo, detail, engros, liens, cle) que les classeurs ne
portent pas.

Regle de publication : seules les lignes dont l'etat vaut exactement
"Pret pour publication" sortent dans LOIS. Les autres vont dans ATTENTE.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

import openpyxl

ETAT_PUBLIE = "Prêt pour publication"

# ---------------------------------------------------------------- vocabulaire
# Les valeurs des listes deroulantes du classeur, traduites dans les codes que
# la page attend. Toute valeur inconnue leve une erreur plutot que de passer.
CODES_VOTE = {
    "Pour": "pour",
    "Contre": "contre",
    "Abstention": "abstention",
    "N'a pas pris part": "npppv",
    "Non concerné": "na",
    "Non applicable": "na",
    "Divisé": "divise",
    "Sans objet": "na",
    "à relever": "na",
}

CODES_ALIGNEMENT = {
    "✅ Aligné": ("aligne", "✅", "Aligné"),
    "⚠️ Partiellement aligné": ("partiel", "⚠️", "Partiellement aligné"),
    "❌ Non aligné": ("non-aligne", "❌", "Non aligné"),
    "🔀 Position hétérogène": ("heterogene", "🔀", "Position hétérogène"),
    "➖ Non testable": ("non-testable", "➖", "Non testable"),
    "à relever": ("non-testable", "➖", "Non testable"),
}

# Les identifiants de la page sont stables : ils servent de cle au jeu, aux
# reponses rapides et aux liens partages. Cette table les attache a
# l'identifiant du classeur, qui lui peut changer de nom de fiche.
IDENTIFIANTS = {
    "SAN-02": "aide-a-mourir", "SAN-03": "pma", "SAN-05": "gaillot",
    "SAN-09": "sante-mentale", "SAN-10": "padhue",
    "V1-15": "rist", "V1-16": "valletoux", "V1-17": "neuder", "V1-18": "garot",
    "V1-19": "ivg-constitution", "V1-23": "plfss-2022", "V1-24": "plfss-2023",
    "V1-25": "plfss-2024", "V1-26": "plfss-2025", "V1-27": "plfss-2026",
    "V1-28": "jomier", "V1-29": "endometriose",
    "T03-023": "retraites", "T16-165": "mineurs-reseaux",
    "ECO-01": "climat-resilience", "ECO-02": "aper", "ECO-03": "industrie-verte",
    "ECO-04": "duplomb", "ECO-05": "zfe-zan", "ECO-07": "gremillet",
    "ECO-09": "ecophyto",
}

# Thematique du classeur vers l'identifiant de sujet de la page.
SUJETS = {
    "4. Santé": "sante",
    "5. Écologie & climat": "ecologie",
    "3. Travail, emploi & retraites": "retraites",
    "16. Numérique & libertés": "numerique",
}


def slug(texte):
    """Identifiant d'URL a partir d'un nom propre."""
    t = unicodedata.normalize("NFD", str(texte or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t


def initiales(nom):
    mots = [m for m in re.split(r"[\s\-]+", str(nom or "")) if m]
    return "".join(m[0].upper() for m in mots)[:3]


def sigle(parti):
    """Le nom court d'un parti, tel qu'il prefixe le bloc « parti ».

    « La France insoumise (LFI) » donne « LFI ». « Sans parti (apparenté
    Renaissance) » donne « Groupe Renaissance » : c'est le groupe qui est
    affiche a titre de repere, pas un parti dont le candidat serait membre.
    """
    p = propre(parti)
    m = re.search(r"\(([^)]+)\)\s*$", p)
    if not m:
        return p
    if p.lower().startswith("sans parti"):
        # On garde l'etiquette entiere : le groupe n'est qu'un repere, et le
        # dire evite de laisser croire a une appartenance.
        return p
    return m.group(1).strip()


def bloc(prefixe, texte):
    """Un bloc « Nom : **premiere ligne** » suivi du reste, comme en ligne."""
    t = propre(texte)
    if not t:
        return ""
    lignes = t.split("\n")
    tete = lignes[0].strip()
    reste = "\n".join(lignes[1:]).strip()
    # L'annee de publication reste visible, mais hors du gras : elle date la
    # promesse, elle n'en fait pas partie.
    annee = ""
    m = re.search(r"\s*(\((?:19|20)\d\d[^)]*\)|\(position permanente\))\s*$", tete)
    if m:
        annee = " " + m.group(1)
        tete = tete[:m.start()].rstrip()
    out = "%s : **%s**%s" % (prefixe, tete, annee)
    return out + ("\n\n" + reste if reste else "")


def deux_blocs(prefixe_personne, prefixe_parti, texte_personne, texte_parti):
    morceaux = [bloc(prefixe_personne, texte_personne), bloc(prefixe_parti, texte_parti)]
    return "\n\n".join(m for m in morceaux if m)


# La redaction n'utilise jamais le tiret cadratin a l'affichage. Le classeur en
# contient : on les convertit a la sortie, sans toucher au classeur lui-meme.
TIRETS = {"\u2014": "-", "\u2013": "-"}


def propre(valeur):
    """Une cellule du classeur, en chaine, sans espaces superflus."""
    if valeur is None:
        return ""
    t = str(valeur).replace("\r\n", "\n").strip()
    for long, court in TIRETS.items():
        t = t.replace(long, court)
    return t


def feuille(classeur, nom):
    """Les lignes d'un onglet, en dictionnaires indexes par l'en-tete."""
    ws = classeur[nom]
    lignes = ws.iter_rows(values_only=True)
    entetes = [("" if c is None else str(c).strip()) for c in next(lignes)]
    out = []
    for brut in lignes:
        if brut is None or not any(c is not None and propre(c) for c in brut):
            continue
        d = {}
        for i, cle in enumerate(entetes):
            if cle:
                d[cle] = propre(brut[i]) if i < len(brut) else ""
        out.append(d)
    return out


# ---------------------------------------------------------------- candidats
def construit_candidats(cand3, fiches, ancien):
    """Les 31 candidat·es, avec l'habillage visuel conserve d'une version a l'autre."""
    par_id = {c["id"]: c for c in ancien}
    # Habillage disponible pour les nouvelles entrees, pris dans la charte.
    reserve = [("purple", "#f6efff", "#7b2ff2"), ("green", "#eafff3", "#0f8a4d"),
               ("gold", "#fffaea", "#c98f00"), ("sky", "#eef4ff", "#0000ff"),
               ("pink", "#f3edff", "#5423df")]
    inclinaisons = ["-4deg", "3deg", "-3deg", "5deg", "-5deg", "4deg"]

    fiche_par_nom = {f.get("Aucun", ""): f for f in fiches}
    out = []
    for i, c in enumerate(cand3):
        nom = c.get("Candidat", "")
        if not nom:
            continue
        cid = slug(nom)
        # Un identifiant deja en ligne ne change jamais : il sert de cle ailleurs.
        for ancien_id, vieux in par_id.items():
            if vieux["nom"] == nom:
                cid = ancien_id
                break
        vieux = par_id.get(cid, {})
        f = fiche_par_nom.get(nom, {})
        teinte, bg, ombre = reserve[i % len(reserve)]
        out.append({
            "id": cid,
            "nom": nom,
            "court": vieux.get("court") or nom.split()[-1],
            "initiales": vieux.get("initiales") or initiales(nom),
            "teinte": vieux.get("teinte") or teinte,
            "parti": c.get("Parti", ""),
            "groupeAN": vieux.get("groupeAN", "-"),
            "groupeSenat": vieux.get("groupeSenat", "-"),
            "parlementaire": "Oui" if c.get("Parl. en cours") == "✅" else "Non",
            "chambre": vieux.get("chambre") or f.get("Mandat parlementaire actuel", ""),
            "mandats": vieux.get("mandats") or f.get("Mandats parlementaires passés", ""),
            "vigilance": c.get("Fenêtre de votes personnels", "") or vieux.get("vigilance", ""),
            "photo": vieux.get("photo", ""),
            "bg": vieux.get("bg") or bg,
            "shadow": vieux.get("shadow") or ombre,
            "tilt": vieux.get("tilt") or inclinaisons[i % len(inclinaisons)],
            "actif": bool(vieux.get("actif", False)),
        })
    return out


# ---------------------------------------------------------------- votes
def vote(valeur, cause=""):
    brut = propre(valeur)
    if not brut:
        return None
    if brut not in CODES_VOTE:
        raise ValueError("valeur de vote inconnue : %r" % brut)
    d = {"code": CODES_VOTE[brut], "label": brut, "brut": brut}
    if cause:
        d["raison"] = cause
    return d


def alignement(valeur):
    brut = propre(valeur)
    if not brut:
        return None
    if brut not in CODES_ALIGNEMENT:
        raise ValueError("valeur d'alignement inconnue : %r" % brut)
    code, icone, label = CODES_ALIGNEMENT[brut]
    return {"code": code, "icon": icone, "label": label, "brut": brut}


def liens_depuis(texte):
    """Les URL d'une cellule « Lien source primaire », avec leur intitule."""
    out = []
    for bloc in re.split(r"\n\s*\n|\n", propre(texte)):
        bloc = bloc.strip()
        if not bloc:
            continue
        m = re.search(r"https?://\S+", bloc)
        if not m:
            continue
        url = m.group(0).rstrip(".,;")
        label = bloc[:m.start()].strip().rstrip(":").strip() or "Source"
        out.append({"label": label, "url": url})
    return out


def coupe_presentation(texte):
    """Separe le corps de la presentation de son avertissement ⚠️ final."""
    t = propre(texte)
    i = t.find("⚠️")
    if i <= 0:
        return t, ""
    return t[:i].strip(), t[i:].strip()


# ---------------------------------------------------------------- lois
def construit_lois(textes, positions, candidats, ancien):
    par_id = {l["id"]: l for l in ancien}
    # Les identifiants de la page sont stables : on retrouve la loi par son
    # identifiant de classeur quand il a deja servi, sinon par son nom.
    cle_site = {}
    for l in ancien:
        cle_site[l["nom"]] = l["id"]

    nom_vers_cid = {c["nom"]: c["id"] for c in candidats}
    court_par_id = {c["id"]: c["court"] for c in candidats}
    par_texte = {}
    for p in positions:
        par_texte.setdefault(p["Texte_ID"], []).append(p)

    out = []
    for t in textes:
        if propre(t.get("État")) != ETAT_PUBLIE:
            continue
        tid = t["Texte_ID"]
        nom = " ".join(t.get("Nom de la fiche", "").split())
        lid = IDENTIFIANTS.get(tid) or cle_site.get(nom) or slug(nom)[:40]
        vieux = par_id.get(lid, {})

        corps, avertissement = coupe_presentation(t.get("Présentation du texte"))
        votes = {}
        for p in par_texte.get(tid, []):
            cid = nom_vers_cid.get(p["Candidat"])
            if not cid:
                raise ValueError("candidat hors perimetre sur %s : %r" % (tid, p["Candidat"]))
            sources = []
            for s in (p.get("Source promesse — PERSONNE"),
                      p.get("Source promesse — PARTI")):
                if s and s not in sources:
                    sources.append(s)
            court = court_par_id[cid]
            sig = sigle(p.get("Parti"))
            # Le commentaire editorial justifie le verdict : il suit les actes
            # plutot que de rester invisible.
            commentaire = propre(p.get("Commentaire éditorial"))
            actes = deux_blocs(court, sig, p.get("ACTES de la personne"),
                               p.get("ACTES du parti"))
            if commentaire:
                actes = (actes + "\n\n" if actes else "") + "ℹ️ " + commentaire
            votes[cid] = {
                "perso": vote(p.get("Vote personnel"), p.get("Cause si non concerné")),
                "groupe": vote(p.get("Vote du groupe")),
                "detail": p.get("Détail chiffré du groupe", ""),
                "promesse": deux_blocs(court, sig, p.get("PROMESSE de la personne"),
                                       p.get("PROMESSE du parti")),
                "actes": actes,
                "alignCandidat": alignement(p.get("Alignement personne")),
                "alignParti": alignement(p.get("Alignement parti")),
                "sources": sources,
            }

        out.append({
            "id": lid,
            "sujet": SUJETS.get(t.get("Thème", ""), "sante"),
            "sousTheme": t.get("Sous-thème", ""),
            "tags": t.get("Tags", ""),
            "nom": nom,
            "statut": vieux.get("statut") or statut_depuis(t),
            "intitule": t.get("Intitulé exact", ""),
            "date": t.get("Date", ""),
            "chambre": t.get("Chambre", ""),
            "initiative": t.get("Initiative", ""),
            "soustitre": vieux.get("soustitre") or soustitre_depuis(nom),
            "chapo": corps or vieux.get("chapo", ""),
            "detail": avertissement or vieux.get("detail", ""),
            "liens": liens_depuis(t.get("Lien source primaire")) or vieux.get("liens", []),
            "releve": t.get("Détail du scrutin / résumé", ""),
            "engros": vieux.get("engros") or soustitre_depuis(nom),
            "cle": bool(vieux.get("cle", False)),
            "votes": votes,
            "aRelever": vieux.get("aRelever", []),
        })
    return out


def statut_depuis(t):
    """Le statut affiche, lu dans l'intitule exact quand il le porte."""
    intitule = propre(t.get("Intitulé exact")).upper()
    for mot, label in (("ADOPTÉ", "Adopté"), ("REJETÉ", "Rejeté"),
                       ("PROMULGUÉE", "Promulguée"), ("EN ATTENTE", "En attente")):
        if intitule.startswith(mot):
            return label
    return propre(t.get("Statut du texte")) or "Adopté"


def soustitre_depuis(nom):
    """La partie du nom de fiche qui suit le tiret, sans le reformuler."""
    for sep in (" — ", " - "):
        if sep in nom:
            reste = nom.split(sep, 1)[1].strip()
            return reste[0].upper() + reste[1:] + ("" if reste.endswith(".") else ".")
    return nom


def construit_attente(textes, lois_publiees):
    publies = {l["nom"] for l in lois_publiees}
    out = []
    for t in textes:
        nom = t.get("Nom de la fiche", "")
        if not nom or nom in publies:
            continue
        if propre(t.get("État")) != "En cours":
            continue
        out.append({
            "id": IDENTIFIANTS.get(t["Texte_ID"]) or slug(nom)[:40],
            "sujet": SUJETS.get(t.get("Thème", ""), "sante"),
            "sousTheme": t.get("Sous-thème", ""),
            "nom": " ".join(nom.split()),
        })
    return out


# ---------------------------------------------------------------- sortie
def lit_ancien(chemin):
    t = Path(chemin).read_text(encoding="utf-8")
    return json.loads(t[t.find("{"):].rstrip().rstrip(";"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparateur", required=True)
    ap.add_argument("--candidats", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()

    ancien = lit_ancien(a.sortie)
    wbc = openpyxl.load_workbook(a.comparateur, read_only=True, data_only=True)
    wbk = openpyxl.load_workbook(a.candidats, read_only=True, data_only=True)
    textes = feuille(wbc, "1_TEXTES")
    positions = feuille(wbc, "2_POSITIONS")
    cand3 = feuille(wbc, "3_CANDIDATS")
    fiches = feuille(wbk, "Candidats")

    candidats = construit_candidats(cand3, fiches, ancien["CANDIDATS"])
    lois = construit_lois(textes, positions, candidats, ancien["LOIS"])
    attente = construit_attente(textes, lois)

    neuf = dict(ancien)
    neuf["CANDIDATS"] = candidats
    neuf["LOIS"] = lois
    neuf["ATTENTE"] = attente

    # Le jeu, les reponses rapides et les fiches ne peuvent pointer que vers
    # une loi publiee : ce qui pointe ailleurs est mis de cote, pas supprime.
    vivants = {l["id"] for l in lois}
    neuf["JEU"] = [j for j in ancien["JEU"]
                   if not (j.get("lois") and not (set(j["lois"]) & vivants))]
    neuf["QUICK"] = [q for q in ancien["QUICK"]
                     if not (q.get("lois") and not (set(q["lois"]) & vivants))]
    sujets_vivants = {l["sujet"] for l in lois}
    neuf["FICHES"] = [f for f in ancien["FICHES"] if f["sujet"] in sujets_vivants]

    corps = json.dumps(neuf, ensure_ascii=False, separators=(",", ":"))
    Path(a.sortie).write_text("window.KOMUNE_DATA = " + corps + ";\n", encoding="utf-8")

    print("candidats : %d" % len(candidats))
    print("lois publiees : %d  (%s)" % (len(lois), ", ".join(l["id"] for l in lois)))
    print("en attente : %d" % len(attente))
    print("jeu : %d -> %d | reponses rapides : %d -> %d | fiches : %d -> %d" % (
        len(ancien["JEU"]), len(neuf["JEU"]), len(ancien["QUICK"]), len(neuf["QUICK"]),
        len(ancien["FICHES"]), len(neuf["FICHES"])))
    wbc.close()
    wbk.close()


if __name__ == "__main__":
    main()
