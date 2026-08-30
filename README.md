# Site Komune - komunemedia.fr

Site 100 % statique (HTML/CSS/JS, sans framework) du média **Komune**, hébergé gratuitement sur **GitHub Pages**.

## Structure

```
index.html                  → Accueil            (/)
articles/index.html         → Nos articles       (/articles/)
comparateur-2027/index.html → Comparateur 2027, retours citoyens (/comparateur-2027/)
comparateur/index.html      → Comparateur BÊTA (outil, version de travail) (/comparateur/)
equipe/index.html           → L'équipe           (/equipe/)
soutenir/index.html         → Nous soutenir      (/soutenir/)
.nojekyll                   → dit à GitHub Pages de servir les fichiers tels quels
```

Chaque page est autonome : son CSS et son JS sont dans le fichier lui-même.
Une **navigation commune** (bloc `<nav class="site-nav">` + un petit `<style>` juste
avant `</head>`) a été ajoutée en haut de chaque page - elle est clairement
commentée `Navigation commune du site` et peut être modifiée ou retirée librement.

Les liens internes sont **relatifs** (`../soutenir/` etc.) : le site fonctionne
aussi bien sur `xxx.github.io` que sur le domaine final.

## Modifier le site

1. Sur GitHub, ouvre le fichier de la page (ex. `soutenir/index.html`).
2. Clique sur le crayon ✏️ (« Edit this file »).
3. Fais ta modification, puis « Commit changes » avec un petit message
   (ex. « maj jauge soutiens »). C'est l'équivalent d'une sauvegarde horodatée.
4. Le site se met à jour tout seul en 1 à 2 minutes.

Pour travailler plus confortablement depuis le Mac : installe **GitHub Desktop**
(gratuit) - il télécharge le dépôt sur l'ordinateur, tu édites les fichiers dans
n'importe quel éditeur (VS Code conseillé), et tu publies en deux clics
(« Commit » puis « Push »).

## Ajouter une page

1. Crée un dossier au nom de la page (ex. `methodologie/`) contenant un `index.html`.
2. L'URL sera automatiquement `/methodologie/`.
3. Ajoute le lien dans le bloc `site-nav` des autres pages si besoin.

## À savoir

- Les images sont servies depuis Google Drive (`drive.google.com/thumbnail?...`) :
  ça fonctionne, mais à terme il vaut mieux les copier dans un dossier `assets/`
  du dépôt pour ne plus dépendre de Drive.
- La jauge de soutiens (page Nous soutenir) lit un Google Sheet public - rien à changer.
- Le comparateur bêta (`/comparateur/`) n'est volontairement pas mis en avant
  dans le menu tant qu'il est en version de travail ; son URL directe reste accessible.
