#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrait le corps d'un article Substack et le nettoie.

On ne garde qu'une liste de balises connues : tout le reste du HTML de Substack
(boutons d'abonnement, sondages, partages, scripts) est ecarte. Le texte, lui,
n'est jamais modifie.
"""
import re
from html.parser import HTMLParser

# Les balises qu'on laisse passer. Le contenu des autres est conserve, mais la
# balise elle-meme disparait : on evite ainsi d'importer la mise en page de Substack.
GARDEES = {
    "p", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote",
    "figure", "figcaption", "img", "a", "strong", "b", "em", "i", "u", "s",
    "br", "hr", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub",
    "code", "pre", "small",
}
VIDES = {"img", "br", "hr"}
# Un h1 dans le corps ferait doublon avec le titre de la page.
RENOMMEES = {"h1": "h2"}
# Les blocs d'interface de Substack : on jette la branche entiere.
REJETEES = re.compile(
    r"subscription-widget|subscribe-widget|button-wrapper|captioned-button|"
    r"poll-embed|digest-post-embed|post-footer|publication-footer|subscribe-footer|"
    r"paywall|comments|share-dialog|tweet-actions|visibility-check|post-ufi|"
    r"audience-selector|footerWrapper|pencraft", re.I)
ATTRIBUTS = {"img": ("src", "alt", "width", "height"), "a": ("href",),
             "td": ("colspan", "rowspan"), "th": ("colspan", "rowspan")}


class Corps(HTMLParser):
    """Recupere le premier <div class="body markup"> et le reecrit proprement."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.dans = False          # on est entre dans le corps de l'article
        self.profondeur = 0        # profondeur des div depuis l'entree
        self.saut = 0              # profondeur d'une branche rejetee
        self.pile = []             # balises ouvertes qu'on a conservees
        self.morceaux = []
        self.fini = False

    # --- utilitaires ---------------------------------------------------
    def _classe(self, attrs):
        d = dict(attrs)
        return (d.get("class") or "") + " " + (d.get("id") or "")

    def _ecrire(self, t):
        self.morceaux.append(t)

    # --- balises -------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if self.fini:
            return
        if not self.dans:
            if tag == "div" and "body" in self._classe(attrs) and "markup" in self._classe(attrs):
                self.dans = True
                self.profondeur = 1
            return
        if self.saut:
            if tag not in VIDES:
                self.saut += 1
            return
        if tag in ("script", "style", "form", "button", "svg", "iframe", "noscript"):
            self.saut = 1
            return
        if REJETEES.search(self._classe(attrs)):
            self.saut = 1
            return
        if tag == "div":
            self.profondeur += 1
        nom = RENOMMEES.get(tag, tag)
        if nom not in GARDEES:
            return
        bons = []
        for cle in ATTRIBUTS.get(nom, ()):
            val = dict(attrs).get(cle)
            if not val:
                continue
            if cle == "href" and val.startswith(("javascript:", "data:")):
                continue
            if cle in ("width", "height"):
                # Substack ecrit parfois une hauteur a virgule : l'attribut HTML
                # n'accepte qu'un entier.
                try:
                    val = str(int(round(float(val))))
                except ValueError:
                    continue
            bons.append('%s="%s"' % (cle, val.replace('"', "&quot;")))
        if nom == "img":
            bons += ['loading="lazy"', 'decoding="async"']
        if nom == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("http") and "komunemedia.fr" not in href:
                bons += ['target="_blank"', 'rel="noopener noreferrer"']
        self._ecrire("<%s%s>" % (nom, (" " + " ".join(bons)) if bons else ""))
        if nom not in VIDES:
            self.pile.append(nom)

    def handle_endtag(self, tag):
        if self.fini or not self.dans:
            return
        if self.saut:
            self.saut -= 1
            return
        if tag == "div":
            self.profondeur -= 1
            if self.profondeur <= 0:
                self.fini = True
                return
        nom = RENOMMEES.get(tag, tag)
        if nom in GARDEES and nom not in VIDES and self.pile and nom in self.pile:
            # on referme tout ce qui est reste ouvert au-dessus
            while self.pile:
                ouvert = self.pile.pop()
                self._ecrire("</%s>" % ouvert)
                if ouvert == nom:
                    break

    def handle_data(self, data):
        if self.dans and not self.saut and not self.fini:
            self._ecrire(data)

    def handle_entityref(self, name):
        if self.dans and not self.saut and not self.fini:
            self._ecrire("&%s;" % name)

    def handle_charref(self, name):
        if self.dans and not self.saut and not self.fini:
            self._ecrire("&#%s;" % name)

    def resultat(self):
        while self.pile:
            self._ecrire("</%s>" % self.pile.pop())
        return "".join(self.morceaux)


def signature_brute(texte_html):
    """La ligne de signature que la redaction place en tete d'article (crayon)."""
    plat = re.sub(r"<[^>]+>", " ", texte_html)
    plat = plat.replace("&#x27;", "'").replace("&rsquo;", "'").replace("&amp;", "&").replace("&nbsp;", " ")
    m = re.search(r"✍️?\s*([A-ZÉÈÀÂÎÔÛÇ][^,|\n<]{2,60})", plat)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


# Bloc de presentation que la redaction ajoute en fin de newsletter. Il fait
# double emploi avec les encarts du site et serait identique d'une page a
# l'autre, ce que les moteurs de recherche penalisent.
PRESENTATION = re.compile(
    r"<(h2|h3|h4)>\s*(?:<[^>]+>\s*)*Komune,\s*c[\u2019']est\s+quoi\s*\?", re.I)


def coupe_presentation(corps):
    m = PRESENTATION.search(corps)
    return corps[:m.start()].rstrip() if m else corps


def nettoie(html_page):
    """Rend le corps de l'article, sans la ligne de signature ni les blocs vides."""
    p = Corps()
    p.feed(html_page)
    corps = p.resultat()
    # la signature est reprise par la page elle-meme : on l'enleve du texte
    corps = re.sub(r"<p[^>]*>\s*(?:<[^>]+>\s*)*✍️?[\s\S]{0,200}?</p>", "", corps, count=1)
    corps = re.sub(r"<(p|li|h2|h3|h4)>\s*</\1>", "", corps)
    corps = re.sub(r"(\s*<br>\s*){3,}", "<br><br>", corps)
    corps = coupe_presentation(corps)
    corps = re.sub(r"(?:\s*<hr>\s*)+$", "", corps)
    return corps.strip()
