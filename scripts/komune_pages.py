#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere, sur komunemedia.fr :
   - une page par article      /articles/<identifiant>/
   - une page par journaliste  /journalistes/<nom>/
   - la liste des journalistes /journalistes/
   et met le plan du site a jour.

Le corps de chaque article est recupere une seule fois depuis Substack puis
conserve dans data/corps/. Les passages suivants ne retelechargent que les
articles nouveaux.
"""
import html
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import corps_substack  # noqa: E402
import page_articles as pa  # noqa: E402

RACINE = ICI.parent
SITE = "https://www.komunemedia.fr"
DATA = RACINE / "data"
CORPS = DATA / "corps"
DOSSIER_ARTICLES = RACINE / "articles"
DOSSIER_JOURNALISTES = RACINE / "journalistes"
SITEMAP = RACINE / "sitemap.xml"

ORG = {"@type": "NewsMediaOrganization", "@id": SITE + "/#organisation", "name": "Komune Média",
       "url": SITE + "/", "sameAs": ["https://komunemedia.substack.com/",
                                     "https://www.instagram.com/komune.media/"],
       "logo": {"@type": "ImageObject", "url": SITE + "/img/logo-rose-vert.webp"}}


# ---------------------------------------------------------------- outils
def e(v):
    return html.escape(str(v or ""), quote=True)


def slugue(n):
    x = unicodedata.normalize("NFD", n or "")
    x = "".join(c for c in x if unicodedata.category(c) != "Mn").lower()
    x = x.replace("’", " ").replace("'", " ").replace(".", " ")
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")


def identifiant(article):
    """L'identifiant de l'article, repris de son adresse Substack."""
    return (article.get("url") or "").rstrip("/").rsplit("/p/", 1)[-1]


def initiales(nom):
    bouts = [m for m in re.split(r"[ \-]+", nom or "") if m]
    return "".join(b[0].upper() for b in bouts[:2])


def texte_nu(h, limite=None):
    t = re.sub(r"<[^>]+>", " ", h or "")
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:limite].rsplit(" ", 1)[0] + "…") if limite and len(t) > limite else t


def charge(nom, defaut):
    f = DATA / nom
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else defaut


# ---------------------------------------------------------------- donnees
def registre():
    """Les journalistes, et qui signe quoi."""
    aut = charge("auteurs.json", {"fusions": {}, "auteurs": {}})
    sig = charge("signatures.json", {})
    fus = aut.get("fusions", {})
    par_article = {k: [fus.get(n, n) for n in v] for k, v in sig.items()}
    return aut.get("auteurs", {}), par_article


def fiche(auteurs, nom):
    o = auteurs.get(nom) or {}
    return {"nom": nom, "slug": o.get("slug") or slugue(nom),
            "role": o.get("role") or "Journaliste",
            "bio": o.get("bio") or [], "photo": o.get("photo") or "",
            "liens": o.get("liens") or []}


# ---------------------------------------------------------------- morceaux communs
def nav(ou, profondeur=2):
    r = "../" * profondeur
    liens = [("", "Accueil"), ("articles/", "Articles"),
             ("comparateur/", "Le comparateur présidentielles 2027"),
             ("journalistes/", "Nos journalistes"), ("equipe/", "L'équipe"),
             ("soutenir/", "Nous soutenir")]
    out = []
    for cible, nom in liens:
        actif = (cible.rstrip("/") == ou)
        out.append('      <a class="site-link%s" href="%s%s"%s>%s</a>' % (
            " is-current" if actif else "", r, cible,
            ' aria-current="page"' if actif else "", e(nom)))
    return ('    <nav class="site-nav" aria-label="Navigation du site">\n'
            '      <a class="site-brand" href="%s" aria-label="Komune Média - retour à l\'accueil">'
            '<img src="%simg/logo-rose-vert.webp" alt="Komune Média" width="360" height="137"></a>\n'
            '      <div class="site-liens">\n%s\n      </div>\n    </nav>' % (r, r, "\n".join(out)))


def pied(profondeur=2):
    r = "../" * profondeur
    return ('    <footer class="site-pied">\n      <div class="site-foot-brand">\n'
            '        <img src="%simg/logo-brun-or.webp" alt="Komune Média" width="360" height="137" loading="lazy" decoding="async">\n'
            '        <span>© Komune Média - Le média indépendant qui décrypte la société avec un regard antiraciste</span>\n'
            '      </div>\n    </footer>' % r)


def tete(titre, description, url, image, extra_meta="", profondeur=2, robots="index, follow, max-image-preview:large, max-snippet:-1"):
    r = "../" * profondeur
    img = image or (SITE + "/img/og-comparateur.png")
    return (
        '<!doctype html>\n<html lang="fr">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <meta name="description" content="%s">\n'
        '  <title>%s</title>\n'
        '  <link rel="canonical" href="%s">\n'
        '  <meta name="robots" content="%s">\n'
        '  <meta property="og:site_name" content="Komune Média">\n'
        '  <meta property="og:locale" content="fr_FR">\n'
        '  <meta property="og:url" content="%s">\n'
        '  <meta property="og:title" content="%s">\n'
        '  <meta property="og:description" content="%s">\n'
        '  <meta property="og:image" content="%s">\n'
        '  <meta name="twitter:card" content="summary_large_image">\n'
        '  <meta name="twitter:image" content="%s">\n'
        '%s'
        '  <link rel="icon" type="image/png" href="%simg/favicon.png">\n'
        '  <link rel="apple-touch-icon" href="%simg/favicon.png">\n'
        '  <link rel="alternate" type="application/rss+xml" title="La newsletter de Komune Média" href="https://komunemedia.substack.com/feed">\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link rel="preconnect" href="https://substackcdn.com" crossorigin>\n'
        '  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@10..48,400;10..48,500;10..48,600;10..48,700;10..48,800&family=Oswald:wght@400;700&display=swap" rel="stylesheet">\n'
        '  <link rel="stylesheet" href="%sarticles/article.css">\n'
        % (e(description), e(titre), e(url), robots, e(url), e(titre), e(description),
           e(img), e(img), extra_meta, r, r, r))


def ld(graphe):
    return ('  <script type="application/ld+json">\n'
            + json.dumps(graphe, ensure_ascii=False, indent=2) + "\n  </script>\n")


def fil(elements, profondeur=2):
    r = "../" * profondeur
    out = []
    for i, (lien, nom) in enumerate(elements):
        if lien is None:
            out.append('<span aria-current="page">%s</span>' % e(nom))
        else:
            out.append('<a href="%s%s">%s</a>' % (r, lien, e(nom)))
        if i < len(elements) - 1:
            out.append('<span aria-hidden="true">›</span>')
    return '    <nav class="fil" aria-label="Fil d\'Ariane">%s</nav>' % "".join(out)


def signature_html(fiches, profondeur=2):
    r = "../" * profondeur
    out = []
    for f in fiches:
        rond = ('<img src="%s" alt="" width="40" height="40" loading="lazy" decoding="async">' % e(f["photo"])
                if f["photo"] else '<span class="ini" aria-hidden="true">%s</span>' % e(initiales(f["nom"])))
        out.append('<a class="art-signature" href="%sjournalistes/%s/" rel="author">%s'
                   '<span>%s<small>%s</small></span></a>' % (r, e(f["slug"]), rond, e(f["nom"]), e(f["role"])))
    return "".join(out)


def carte(article, auteurs, par_article, profondeur=2):
    r = "../" * profondeur
    ident = identifiant(article)
    img = pa.vignette(article.get("image"), 560)
    vis = ('<div class="carte-img"><img src="%s" alt="" loading="lazy" decoding="async"></div>' % e(img)) if img else ""
    noms = [fiche(auteurs, n)["nom"] for n in par_article.get(ident, [])]
    return ('<a class="carte" href="%sarticles/%s/">%s<div class="carte-corps">'
            '<span class="carte-date">%s</span>'
            '<span class="carte-titre">%s</span>'
            '%s</div></a>' % (
                r, e(ident), vis, e(pa.date_lisible((article.get("date") or "")[:10])),
                e(article.get("title") or ""),
                ('<span class="carte-sig">%s</span>' % e(" et ".join(noms))) if noms else ""))


# ---------------------------------------------------------------- page d'article
def page_article(article, corps, auteurs, par_article, precedent, suivant, memes):
    ident = identifiant(article)
    titre = (article.get("title") or "").strip()
    chapo = (article.get("excerpt") or "").strip()
    iso = (article.get("date") or "")[:10]
    image = (article.get("image") or "").strip()
    url = "%s/articles/%s/" % (SITE, ident)
    fiches = [fiche(auteurs, n) for n in par_article.get(ident, [])]

    description = texte_nu(chapo or corps, 158) or titre
    titre_page = "%s - Komune Média" % titre
    if fiches:
        titre_page = "%s - %s - Komune Média" % (titre, fiches[0]["nom"])

    auteurs_ld = [{"@type": "Person", "name": f["nom"],
                   "url": "%s/journalistes/%s/" % (SITE, f["slug"]),
                   "jobTitle": f["role"],
                   "worksFor": {"@id": SITE + "/#organisation"}} for f in fiches]
    if not auteurs_ld:
        auteurs_ld = [{"@type": "Organization", "name": "Komune Média", "url": SITE + "/"}]

    graphe = {"@context": "https://schema.org", "@graph": [ORG, {
        "@type": "NewsArticle",
        "@id": url + "#article",
        "headline": titre[:110],
        "name": titre,
        "description": description,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "datePublished": iso,
        "dateModified": iso,
        "inLanguage": "fr-FR",
        "isAccessibleForFree": True,
        "author": auteurs_ld,
        "publisher": {"@id": SITE + "/#organisation"},
        "articleSection": "Société",
        "wordCount": len(texte_nu(corps).split()),
    }, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Nos articles", "item": SITE + "/articles/"},
            {"@type": "ListItem", "position": 3, "name": titre, "item": url}]}]}
    if image:
        graphe["@graph"][1]["image"] = [pa.vignette(image, 1200)]

    meta = ('  <meta property="og:type" content="article">\n'
            '  <meta property="article:published_time" content="%s">\n' % e(iso))
    for f in fiches:
        meta += '  <meta property="article:author" content="%s">\n' % e(f["nom"])
    if precedent:
        meta += '  <link rel="prev" href="%s/articles/%s/">\n' % (SITE, identifiant(precedent))
    if suivant:
        meta += '  <link rel="next" href="%s/articles/%s/">\n' % (SITE, identifiant(suivant))

    couverture = ""
    if image:
        couverture = ('      <figure class="art-couverture"><img src="%s" srcset="%s 900w, %s 1400w" '
                      'sizes="(max-width: 1100px) 94vw, 1100px" alt="" '
                      'fetchpriority="high" decoding="async"></figure>\n' % (
                          e(pa.vignette(image, 1400)), e(pa.vignette(image, 900)), e(pa.vignette(image, 1400))))

    voisins = []
    if precedent:
        voisins.append('      <a class="voisin" href="../%s/"><p class="eyebrow">Article précédent</p>'
                       '<b>%s</b></a>' % (e(identifiant(precedent)), e(precedent.get("title") or "")))
    if suivant:
        voisins.append('      <a class="voisin" href="../%s/"><p class="eyebrow">Article suivant</p>'
                       '<b>%s</b></a>' % (e(identifiant(suivant)), e(suivant.get("title") or "")))

    suite = ""
    if memes:
        suite = ('    <section class="suite">\n      <h2>Du même auteur</h2>\n'
                 '      <div class="cartes">\n        %s\n      </div>\n    </section>\n'
                 % "\n        ".join(carte(a, auteurs, par_article) for a in memes))

    return (
        tete(titre_page, description, url, pa.vignette(image, 1200) if image else "", meta)
        + ld(graphe)
        + "</head>\n<body>\n  <div class=\"page\">\n"
        + nav("articles") + "\n"
        + fil([("", "Accueil"), ("articles/", "Nos articles"), (None, titre)]) + "\n"
        + '    <main class="canvas">\n'
        + '      <article>\n'
        + '      <header class="art-tete panel">\n'
        + '        <p class="eyebrow">Article de Komune Média</p>\n'
        + '        <h1>%s</h1>\n' % e(titre)
        + ('        <p class="art-chapo">%s</p>\n' % e(chapo) if chapo else "")
        + '        <div class="art-meta">%s<time class="art-date" datetime="%s">%s</time></div>\n' % (
            signature_html(fiches), e(iso), e(pa.date_lisible(iso)))
        + '      </header>\n'
        + couverture
        + '      <div class="art-corps panel">\n%s\n      </div>\n' % corps
        + '      </article>\n'
        + '      <div class="art-pied">\n'
        + '        <div class="encart sombre"><h2>Cet article vous a appris quelque chose&nbsp;?</h2>'
        + '<p>Komune est un média indépendant, sans publicité et sans actionnaire. Nos enquêtes vivent de vos dons.</p>'
        + '<a class="bouton" href="../../soutenir/">Nous soutenir 💛</a></div>\n'
        + '        <div class="encart jaune"><h2>La newsletter</h2>'
        + '<p>Un décryptage chaque semaine sur l\'immigration, le racisme et les discriminations, directement dans votre boîte mail.</p>'
        + '<a class="bouton" href="https://komunemedia.substack.com/subscribe" target="_blank" rel="noopener noreferrer">S\'abonner gratuitement</a></div>\n'
        + '        <div class="encart blanc"><h2>Lire ailleurs</h2>'
        + '<p>Cet article a d\'abord paru dans notre newsletter. Vous pouvez le lire et le commenter là-bas.</p>'
        + '<a class="bouton clair" href="%s" target="_blank" rel="noopener noreferrer">Voir sur Substack ↗</a></div>\n' % e(article.get("url") or "")
        + '      </div>\n'
        + ('      <div class="voisins">\n%s\n      </div>\n' % "\n".join(voisins) if voisins else "")
        + suite
        + '    </main>\n'
        + pied() + "\n  </div>\n</body>\n</html>\n")



# ---------------------------------------------------------------- pages journalistes
def page_journaliste(f, articles, auteurs, par_article):
    url = "%s/journalistes/%s/" % (SITE, f["slug"])
    n = len(articles)

    description = ("%s, %s à Komune Média. %d article%s publié%s : %s." % (
        f["nom"], f["role"].lower(), n, "s" if n > 1 else "", "s" if n > 1 else "",
        texte_nu(", ".join(a.get("title") or "" for a in articles[:3]), 90)))[:158]

    personne = {"@type": "Person", "@id": url + "#personne", "name": f["nom"],
                "url": url, "jobTitle": f["role"],
                "worksFor": {"@id": SITE + "/#organisation"},
                "knowsAbout": ["immigration", "racisme", "antiracisme", "discriminations",
                               "droits LGBT", "féminisme", "droits humains"]}
    if f["photo"]:
        personne["image"] = f["photo"]
    if f["bio"]:
        personne["description"] = texte_nu(" ".join(f["bio"]), 280)
    if f["liens"]:
        personne["sameAs"] = f["liens"]

    graphe = {"@context": "https://schema.org", "@graph": [ORG, personne, {
        "@type": "ProfilePage",
        "@id": url + "#page",
        "url": url,
        "name": "%s - journaliste à Komune Média" % f["nom"],
        "mainEntity": {"@id": url + "#personne"},
        "inLanguage": "fr-FR"}, {
        "@type": "ItemList",
        "name": "Les articles de %s" % f["nom"],
        "numberOfItems": n,
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "itemListElement": [{"@type": "ListItem", "position": i + 1,
                             "url": "%s/articles/%s/" % (SITE, identifiant(a)),
                             "name": a.get("title") or ""} for i, a in enumerate(articles)]}, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Nos journalistes", "item": SITE + "/journalistes/"},
            {"@type": "ListItem", "position": 3, "name": f["nom"], "item": url}]}]}

    rond = ('<img src="%s" alt="%s" width="170" height="170" decoding="async">' % (e(f["photo"]), e(f["nom"]))
            if f["photo"] else '<span class="ini" aria-hidden="true">%s</span>' % e(initiales(f["nom"])))
    bio = "".join('<p>%s</p>' % e(p) for p in f["bio"])

    return (
        tete("%s - journaliste à Komune Média" % f["nom"], description, url,
             f["photo"] or "", '  <meta property="og:type" content="profile">\n')
        + ld(graphe)
        + "</head>\n<body>\n  <div class=\"page\">\n"
        + nav("journalistes") + "\n"
        + fil([("", "Accueil"), ("journalistes/", "Nos journalistes"), (None, f["nom"])]) + "\n"
        + '    <main class="canvas">\n'
        + '      <header class="jour-tete panel">\n'
        + '        <div class="jour-photo">%s</div>\n' % rond
        + '        <div>\n          <p class="eyebrow">Journaliste à Komune Média</p>\n'
        + '          <h1>%s</h1>\n' % e(f["nom"])
        + '          <p><span class="jour-role">%s</span></p>\n' % e(f["role"])
        + ('          <div class="jour-bio">%s</div>\n' % bio if bio else "")
        + '          <p class="jour-compte">%d article%s publié%s sur komunemedia.fr</p>\n' % (
            n, "s" if n > 1 else "", "s" if n > 1 else "")
        + '        </div>\n      </header>\n'
        + '      <section class="suite">\n        <h2>Ses articles</h2>\n'
        + '        <div class="cartes">\n          %s\n        </div>\n      </section>\n'
        % "\n          ".join(carte(a, auteurs, par_article) for a in articles)
        + '    </main>\n'
        + pied() + "\n  </div>\n</body>\n</html>\n")


def page_liste_journalistes(fiches_comptees):
    url = SITE + "/journalistes/"
    noms = ", ".join(f["nom"] for f, _ in fiches_comptees[:8])
    description = ("Les journalistes de Komune Média : %s et %d autres. Qui écrit quoi, article par article."
                   % (noms, max(0, len(fiches_comptees) - 8)))[:158]
    graphe = {"@context": "https://schema.org", "@graph": [ORG, {
        "@type": "CollectionPage", "@id": url + "#page", "url": url,
        "name": "Les journalistes de Komune Média", "inLanguage": "fr-FR",
        "about": [{"@type": "Person", "name": f["nom"],
                   "url": "%s/journalistes/%s/" % (SITE, f["slug"])} for f, _ in fiches_comptees]}, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Nos journalistes", "item": url}]}]}

    cartes = []
    for f, n in fiches_comptees:
        rond = ('<img src="%s" alt="" loading="lazy" decoding="async">' % e(f["photo"])
                if f["photo"] else e(initiales(f["nom"])))
        cartes.append('        <a class="jour-carte" href="%s/"><span class="rond">%s</span>'
                      '<span><b>%s</b><small>%s · %d article%s</small></span></a>'
                      % (e(f["slug"]), rond, e(f["nom"]), e(f["role"]), n, "s" if n > 1 else ""))

    return (
        tete("Les journalistes de Komune Média", description, url, "", "", profondeur=1)
        + ld(graphe)
        + "</head>\n<body>\n  <div class=\"page\">\n"
        + nav("journalistes", profondeur=1) + "\n"
        + fil([("", "Accueil"), (None, "Nos journalistes")], profondeur=1) + "\n"
        + '    <main class="canvas">\n'
        + '      <header class="art-tete panel">\n'
        + '        <p class="eyebrow">L\'équipe qui écrit</p>\n'
        + '        <h1>Nos journalistes</h1>\n'
        + '        <p class="art-chapo">Komune Média est écrit par %d journalistes. '
          'Chaque article est signé, et chaque signature mène à la liste de ce que la personne a publié.</p>\n'
          % len(fiches_comptees)
        + '      </header>\n'
        + '      <div class="jours">\n%s\n      </div>\n' % "\n".join(cartes)
        + '    </main>\n'
        + pied(profondeur=1) + "\n  </div>\n</body>\n</html>\n")


# ---------------------------------------------------------------- recuperation des corps
def recupere_corps(slug, chercheur):
    """Telecharge l'article sur Substack et en garde le corps nettoye."""
    brut = chercheur("https://komunemedia.substack.com/p/" + slug).decode("utf-8", "replace")
    return corps_substack.nettoie(brut), corps_substack.signature_brute(brut)


def corps_de(article, chercheur, signatures):
    """Le corps d'un article, pris dans data/corps/ ou telecharge une fois pour toutes."""
    slug = identifiant(article)
    fichier = CORPS / (slug + ".html")
    if fichier.exists() and fichier.stat().st_size > 400:
        return fichier.read_text(encoding="utf-8"), False
    if chercheur is None:
        return "", False
    try:
        corps, sig = recupere_corps(slug, chercheur)
    except Exception as exc:  # noqa: BLE001 - un article injoignable n'arrete pas le reste
        print("  %s : injoignable (%s), on reessaiera au prochain passage." % (slug, exc))
        return "", False
    if len(texte_nu(corps)) < 200:
        print("  %s : corps trop court, on ne cree pas la page." % slug)
        return "", False
    CORPS.mkdir(parents=True, exist_ok=True)
    fichier.write_text(corps, encoding="utf-8")
    if sig and slug not in signatures:
        signatures[slug] = sig
    return corps, True


# ---------------------------------------------------------------- plan du site
def plan_du_site(articles, fiches_comptees):
    """Reecrit sitemap.xml : les pages fixes, puis les articles et les journalistes."""
    if not SITEMAP.exists():
        return False
    texte = SITEMAP.read_text(encoding="utf-8")
    debut = texte.find("<urlset")
    fin = texte.rfind("</urlset>")
    if debut < 0 or fin < 0:
        return False
    entete = texte[debut:texte.find(">", debut) + 1]

    fixes = []
    for m in re.finditer(r"  <url>\s*<loc>(.*?)</loc>.*?</url>\n", texte, re.S):
        if "/articles/" in m.group(1) and m.group(1) != SITE + "/articles/":
            continue
        if "/journalistes/" in m.group(1):
            continue
        fixes.append(m.group(0))

    recent = max([(a.get("date") or "")[:10] for a in articles] or [""])
    bouts = list(fixes)
    bouts.append("  <url>\n    <loc>%s/journalistes/</loc>\n    <lastmod>%s</lastmod>\n"
                 "    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"
                 % (SITE, recent))
    for f, _ in fiches_comptees:
        bouts.append("  <url>\n    <loc>%s/journalistes/%s/</loc>\n    <lastmod>%s</lastmod>\n"
                     "    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"
                     % (SITE, f["slug"], recent))
    for a in articles:
        iso = (a.get("date") or "")[:10]
        img = ""
        if (a.get("image") or "").strip():
            img = ("    <image:image>\n      <image:loc>%s</image:loc>\n"
                   "      <image:title>%s</image:title>\n    </image:image>\n"
                   % (html.escape(pa.vignette(a["image"], 1200), quote=False),
                      html.escape(a.get("title") or "", quote=False)))
        bouts.append("  <url>\n    <loc>%s/articles/%s/</loc>\n    <lastmod>%s</lastmod>\n"
                     "    <changefreq>yearly</changefreq>\n    <priority>0.8</priority>\n%s  </url>\n"
                     % (SITE, identifiant(a), iso, img))

    neuf = ('<?xml version="1.0" encoding="UTF-8"?>\n' + entete + "\n" + "".join(bouts) + "</urlset>\n")
    if neuf != texte:
        SITEMAP.write_text(neuf, encoding="utf-8")
        return True
    return False


# ---------------------------------------------------------------- orchestration
def ecrire_tout(articles=None, chercheur=None):
    if articles is None:
        articles = json.loads((DATA / "articles.json").read_text(encoding="utf-8"))
    articles = [a for a in articles if (a.get("title") or "").strip() and (a.get("url") or "").strip()]
    articles.sort(key=lambda a: (a.get("date") or ""), reverse=True)

    auteurs, par_article = registre()
    signatures = charge("signatures.json", {})

    # qui a ecrit quoi
    par_auteur = {}
    for a in articles:
        for nom in par_article.get(identifiant(a), []):
            par_auteur.setdefault(nom, []).append(a)

    DOSSIER_ARTICLES.mkdir(parents=True, exist_ok=True)
    DOSSIER_JOURNALISTES.mkdir(parents=True, exist_ok=True)

    neufs, ecrites = 0, 0
    for i, a in enumerate(articles):
        ident = identifiant(a)
        corps, telecharge = corps_de(a, chercheur, signatures)
        if telecharge:
            neufs += 1
            time.sleep(1.2)
        if not corps:
            continue
        noms = par_article.get(ident, [])
        memes = []
        for nom in noms:
            for autre in par_auteur.get(nom, []):
                if identifiant(autre) != ident and autre not in memes:
                    memes.append(autre)
        page = page_article(a, corps, auteurs, par_article,
                            articles[i + 1] if i + 1 < len(articles) else None,
                            articles[i - 1] if i > 0 else None,
                            memes[:3])
        dossier = DOSSIER_ARTICLES / ident
        dossier.mkdir(parents=True, exist_ok=True)
        cible = dossier / "index.html"
        if not cible.exists() or cible.read_text(encoding="utf-8") != page:
            cible.write_text(page, encoding="utf-8")
            ecrites += 1

    # les signatures relevees au passage sont conservees pour la redaction
    (DATA / "signatures.json").write_text(
        json.dumps(signatures, ensure_ascii=False, indent=1), encoding="utf-8")

    fiches_comptees = sorted(
        ((fiche(auteurs, nom), len(lot)) for nom, lot in par_auteur.items()),
        key=lambda x: (-x[1], x[0]["nom"]))
    for f, _ in fiches_comptees:
        dossier = DOSSIER_JOURNALISTES / f["slug"]
        dossier.mkdir(parents=True, exist_ok=True)
        page = page_journaliste(f, par_auteur[f["nom"]], auteurs, par_article)
        cible = dossier / "index.html"
        if not cible.exists() or cible.read_text(encoding="utf-8") != page:
            cible.write_text(page, encoding="utf-8")
    (DOSSIER_JOURNALISTES / "index.html").write_text(
        page_liste_journalistes(fiches_comptees), encoding="utf-8")

    plan_du_site([a for a in articles if (CORPS / (identifiant(a) + ".html")).exists()], fiches_comptees)

    print("Pages d'article ecrites : %d (dont %d corps telecharges)." % (ecrites, neufs))
    print("Pages de journaliste : %d." % len(fiches_comptees))
    return ecrites


if __name__ == "__main__":
    import sync_substack
    ecrire_tout(chercheur=sync_substack.recupere)
