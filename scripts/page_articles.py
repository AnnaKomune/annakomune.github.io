#!/usr/bin/env python3
"""Regenere la liste d'articles de /articles/ a partir de data/articles.json.

La page est ecrite en dur (et non remplie par du JavaScript) pour que les
moteurs de recherche voient les titres, les extraits, les dates et les
couvertures sans avoir a executer de script.

Deux zones de la page sont remplacees, entre balises reperes :
  <!-- ARTICLES:DEBUT --> ... <!-- ARTICLES:FIN -->        la liste visible
  <!-- ARTICLES-LD:DEBUT --> ... <!-- ARTICLES-LD:FIN -->  les donnees structurees
Tout le reste de la page (design, textes, navigation) est laisse intact.

Utilisable seul :  python3 scripts/page_articles.py
"""
import html
import json
import re
import unicodedata
import urllib.parse
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DATA_FILE = RACINE / "data" / "articles.json"
PAGE_FILE = RACINE / "articles" / "index.html"
SITEMAP_FILE = RACINE / "sitemap.xml"

SITE = "https://www.komunemedia.fr"
DEBUT = "<!-- ARTICLES:DEBUT (genere par scripts/page_articles.py) -->"
FIN = "<!-- ARTICLES:FIN -->"
LD_DEBUT = "<!-- ARTICLES-LD:DEBUT (genere par scripts/page_articles.py) -->"
LD_FIN = "<!-- ARTICLES-LD:FIN -->"

CDN = "https://substackcdn.com/image/fetch/"
MOIS = ("janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre")
MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre")

# Couvertures de secours pour les rares articles sans image.
TEINTES = ("cover-pink", "cover-sky", "cover-gold", "cover-green", "cover-purple", "cover-blue", "cover-dark")
MOTS = ("Komune", "Lire", "Focus", "Récit", "Décryptage", "Regards", "À voir")


def vignette(url, largeur):
    """Demande au CDN de Substack une version redimensionnee de la couverture.

    L'adresse d'origine n'est jamais modifiee dans data/articles.json : on ne
    fabrique ici que l'adresse d'affichage, pour ne pas charger des images de
    2 Mo dans une grille de vignettes."""
    if not url:
        return ""
    if url.startswith(CDN):
        return CDN + "w_%d,c_limit," % largeur + url[len(CDN):]
    if url.startswith("https://substackcdn.com/"):
        return url  # deja une vignette (miniatures YouTube par exemple)
    return CDN + "w_%d,c_limit,f_auto,q_auto:good,fl_progressive:steep/" % largeur + urllib.parse.quote(url, safe="")


def sans_accent(valeur):
    valeur = unicodedata.normalize("NFD", valeur or "")
    valeur = "".join(c for c in valeur if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", valeur).strip().lower()


def e(valeur):
    return html.escape(valeur or "", quote=True)


def date_lisible(iso):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    if not m:
        return ""
    an, mois, jour = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return "%d %s %d" % (jour, MOIS_FR[mois - 1], an)


def extrait_court(valeur, limite=190):
    texte = re.sub(r"\s+", " ", (valeur or "")).strip()
    if len(texte) > limite:
        return texte[:limite - 3].rstrip() + "…"
    return texte


def carte(article, rang, vedette):
    titre = (article.get("title") or "").strip()
    url = (article.get("url") or "").strip()
    image = (article.get("image") or "").strip()
    extrait = extrait_court(article.get("excerpt") or "")
    iso = (article.get("date") or "")[:10]

    if image:
        petite, grande = vignette(image, 900 if vedette else 560), vignette(image, 1200 if vedette else 900)
        couverture = (
            '<div class="article-cover cover-photo">'
            '<img src="%s" srcset="%s 560w, %s 900w" sizes="%s" alt="" %s decoding="async"></div>'
        ) % (
            e(petite), e(vignette(image, 560)), e(vignette(image, 900)),
            "(max-width: 700px) 92vw, (max-width: 1100px) 46vw, 31vw" if not vedette else "(max-width: 700px) 92vw, 48vw",
            'fetchpriority="high"' if rang == 0 else 'loading="lazy"',
        )
    else:
        couverture = (
            '<div class="article-cover %s"><div class="cover-meta">'
            '<span class="cover-number">%02d</span><span class="cover-label">Komune Média</span>'
            '<span class="cover-word">%s</span></div></div>'
        ) % (TEINTES[rang % len(TEINTES)], rang + 1, MOTS[rang % len(MOTS)])

    date_html = ('<p class="article-date"><time datetime="%s">%s</time></p>' % (e(iso), e(date_lisible(iso)))) if iso else ""
    cherche = sans_accent(titre + " " + (article.get("excerpt") or ""))

    return (
        '        <a class="article-card%s" href="%s" target="_blank" rel="noopener" data-cherche="%s">\n'
        '          <div class="article-card-inner">\n'
        '            %s\n'
        '            <div class="article-body">\n'
        '              %s\n'
        '              <h3 class="article-title">%s</h3>\n'
        '              <p class="article-excerpt">%s</p>\n'
        '              <span class="article-read">Lire l\'article sur Substack ↗</span>\n'
        '            </div>\n'
        '          </div>\n'
        '        </a>'
    ) % (" featured" if vedette else "", e(url), e(cherche), couverture, date_html, e(titre), e(extrait))


def bloc_liste(articles):
    """La liste visible, groupee par annee (une section et un h2 par annee)."""
    annees = []
    for article in articles:
        an = (article.get("date") or "")[:4] or "Archives"
        if not annees or annees[-1][0] != an:
            annees.append((an, []))
        annees[-1][1].append(article)

    morceaux = []
    rang = 0
    for an, lot in annees:
        cartes = []
        for article in lot:
            cartes.append(carte(article, rang, vedette=(rang == 0)))
            rang += 1
        pluriel = "s" if len(lot) > 1 else ""
        morceaux.append(
            '    <section class="annee" data-annee="%s" aria-labelledby="annee-%s">\n'
            '      <div class="annee-tete">\n'
            '        <h2 id="annee-%s">%s</h2>\n'
            '        <p class="annee-compte"><span data-compte-annee>%d</span> article%s</p>\n'
            '      </div>\n'
            '      <div class="articles-grid">\n%s\n      </div>\n'
            '    </section>' % (e(an), e(an), e(an), e(an), len(lot), pluriel, "\n".join(cartes))
        )
    return "\n".join(morceaux)


def bloc_donnees(articles):
    """Donnees structurees : le blog, le fil d'Ariane, et la liste ordonnee des articles."""
    liste = []
    for i, article in enumerate(articles, start=1):
        entree = {"@type": "ListItem", "position": i,
                  "url": (article.get("url") or "").strip(),
                  "name": (article.get("title") or "").strip()}
        liste.append(entree)

    graphe = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Blog",
                "@id": SITE + "/articles/#blog",
                "url": SITE + "/articles/",
                "name": "Les articles de Komune Média",
                "description": "Décryptages, enquêtes et débunks des mots publiés par Komune Média.",
                "inLanguage": "fr-FR",
                "publisher": {
                    "@type": "Organization",
                    "name": "Komune Média",
                    "url": SITE + "/",
                    "logo": {"@type": "ImageObject", "url": SITE + "/img/logo-rose-vert.webp"},
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Nos articles", "item": SITE + "/articles/"},
                ],
            },
            {
                "@type": "ItemList",
                "@id": SITE + "/articles/#liste",
                "name": "Tous les articles de Komune Média",
                "numberOfItems": len(articles),
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "itemListElement": liste,
            },
        ],
    }
    return ('  <script type="application/ld+json">\n' +
            json.dumps(graphe, ensure_ascii=False, indent=2) + "\n  </script>")


def remplacer(page, debut, fin, contenu, ou):
    i = page.find(debut)
    j = page.find(fin)
    if i < 0 or j < 0 or j < i:
        raise SystemExit("Balises reperes introuvables dans articles/index.html (%s)." % ou)
    return page[:i + len(debut)] + "\n" + contenu + "\n" + page[j:]


def maj_sitemap(articles):
    if not SITEMAP_FILE.exists() or not articles:
        return False
    recent = max((a.get("date") or "")[:10] for a in articles)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", recent):
        return False
    texte = SITEMAP_FILE.read_text(encoding="utf-8")
    motif = re.compile(r"(<loc>%s/articles/</loc>\s*<lastmod>)(\d{4}-\d{2}-\d{2})(</lastmod>)" % re.escape(SITE))
    neuf = motif.sub(lambda m: m.group(1) + recent + m.group(3), texte, count=1)
    if neuf != texte:
        SITEMAP_FILE.write_text(neuf, encoding="utf-8")
        return True
    return False


def ecrire_page(articles=None):
    if articles is None:
        articles = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    articles = [a for a in articles if (a.get("title") or "").strip() and (a.get("url") or "").strip()]
    articles.sort(key=lambda a: (a.get("date") or ""), reverse=True)

    page = PAGE_FILE.read_text(encoding="utf-8")
    page = remplacer(page, DEBUT, FIN, bloc_liste(articles), "liste")
    page = remplacer(page, LD_DEBUT, LD_FIN, bloc_donnees(articles), "donnees structurees")
    # Le compteur affiche sous la barre de recherche.
    page = re.sub(r'(<span id="compte-total">)\d+(</span>)', r"\g<1>%d\g<2>" % len(articles), page)
    # L'image de partage : la couverture du dernier article publie.
    derniere = next((vignette(a.get("image"), 1200) for a in articles if (a.get("image") or "").strip()), "")
    if derniere:
        for cle in ('property="og:image"', 'name="twitter:image"'):
            page = re.sub(r'(<meta %s content=")[^"]*(">)' % re.escape(cle),
                          lambda m: m.group(1) + html.escape(derniere, quote=True) + m.group(2), page, count=1)

    change = False
    if page != PAGE_FILE.read_text(encoding="utf-8"):
        PAGE_FILE.write_text(page, encoding="utf-8")
        change = True
    if maj_sitemap(articles):
        change = True
    print("articles/index.html : %d articles écrits en dur." % len(articles))
    return change


if __name__ == "__main__":
    ecrire_page()
