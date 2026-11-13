/* Komune - script commun : menu, vidéos au clic, jauge des soutiens, retours, et petits outils partagés. */
(function(){
  'use strict';
  var K = window.K = window.K || {};

  /* ---------- outils ---------- */
  K.esc = function(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };
  K.el = function(t, c, x){ var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  K.pli = function(s){ return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); };
  K.melange = function(a){ a = a.slice(); for (var i = a.length - 1; i > 0; i--){ var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; };
  K.famille = function(nom){ var p = String(nom).split(' '); return K.pli(p.slice(1).join(' ')) + ' ' + K.pli(p[0]); };
  K.racine = (document.documentElement.getAttribute('data-racine') || './');

  /* Un texte du tableur : paragraphes, retours à la ligne, liens cliquables. Rien n'est réécrit. */
  K.riche = function(texte){
    var t = String(texte || '').trim(); if (!t) return '';
    return t.split(/\n\s*\n/).map(function(par){
      var h = K.esc(par).replace(/\n/g, '<br>');
      h = h.replace(/(https?:\/\/[^\s<)]+[^\s<).,;])/g, function(u){ return '<a href="' + u + '" target="_blank" rel="noopener">' + u.replace(/^https?:\/\/(www\.)?/, '').split('/')[0] + ' ↗</a>'; });
      return '<p>' + h + '</p>';
    }).join('');
  };

  K.avatar = function(c, taille){
    var s = K.el('span', 'av' + (taille ? ' ' + taille : ''));
    if (c && c.photo){ var i = new Image(); i.alt = ''; i.loading = 'lazy'; i.decoding = 'async'; i.src = K.racine + 'candidats/img/' + c.photo + '.webp';
      i.onerror = function(){ s.textContent = c.ini || ''; }; s.appendChild(i); }
    else s.textContent = (c && c.ini) || '';
    return s;
  };

  K.LIB_VOTE = {pour: 'Pour', contre: 'Contre', abstention: 'Abstention', npppv: "N'a pas pris part au vote", na: 'Non concerné·e', divise: 'Divisé'};
  K.vote = function(v, court){
    var s = K.el('span', 'vote ' + v.c, v.c === 'na' ? (v.l === 'Non applicable' || v.l === 'Sans objet' ? v.l : 'Non concerné·e') : (v.c === 'npppv' && court ? "N'a pas pris part" : (K.LIB_VOTE[v.c] || v.l)));
    return s;
  };
  K.AL = {aligne: ['✅', 'Aligné'], partiel: ['⚠️', 'Partiellement aligné'], contraire: ['❌', 'Contradictoire'],
          heterogene: ['🔀', 'Position hétérogène'], 'non-testable': ['➖', 'Non testable']};
  K.alignement = function(code){ var a = K.AL[code] || K.AL['non-testable']; var s = K.el('span', 'al ' + code); s.appendChild(K.el('span', null, a[0])); s.appendChild(document.createTextNode(a[1])); return s; };

  /* ---------- menu ---------- */
  var b = document.querySelector('.burger'), n = document.getElementById('nav-site');
  if (b && n){
    b.addEventListener('click', function(e){ e.stopPropagation(); var o = n.classList.toggle('ouvert'); b.setAttribute('aria-expanded', o ? 'true' : 'false'); });
    document.addEventListener('click', function(e){ if (n.classList.contains('ouvert') && !n.contains(e.target)){ n.classList.remove('ouvert'); b.setAttribute('aria-expanded', 'false'); } });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && n.classList.contains('ouvert')){ n.classList.remove('ouvert'); b.setAttribute('aria-expanded', 'false'); b.focus(); } });
  }
  var ici = document.querySelector('.nav-outils a.ici'); if (ici && ici.scrollIntoView) { try { ici.scrollIntoView({block: 'nearest', inline: 'center'}); } catch (e) {} }

  /* ---------- vidéos : rien ne se charge avant le clic ---------- */
  document.addEventListener('click', function(e){
    var bt = e.target.closest && e.target.closest('.vid [data-yt], .vid [data-ig]'); if (!bt) return;
    var f = document.createElement('iframe'); f.title = bt.getAttribute('aria-label') || 'Vidéo'; f.allow = 'autoplay; encrypted-media; picture-in-picture'; f.setAttribute('allowfullscreen', '');
    f.src = bt.hasAttribute('data-yt') ? 'https://www.youtube-nocookie.com/embed/' + bt.getAttribute('data-yt') + '?autoplay=1&rel=0'
                                       : 'https://www.instagram.com/' + bt.getAttribute('data-ig') + '/embed/';
    bt.replaceWith(f);
  });

  /* ---------- jauge des soutiens mensuels : une seule cellule d'une feuille publique ---------- */
  K.jauge = function(retour){
    var FEUILLE = '1jGIf48AVtuHa3wEphqPUhDNARQ7Cch2HlNccEJSeo_w', ONGLET = 'donnée site', CELL = 'A1', CAP = 800;
    function nombre(v){ if (v == null) return NaN; return parseFloat(String(v).replace(/[^\d,.-]/g, '').replace(',', '.')); }
    function lit(rep){ var t = rep && rep.table; if (!t) return NaN; var c = t.rows && t.rows[0] && t.rows[0].c && t.rows[0].c[0];
      var x = nombre(c ? (c.f != null ? c.f : c.v) : null); return isFinite(x) ? x : nombre(t.cols && t.cols[0] && t.cols[0].label); }
    function affiche(x){
      var pct = x >= CAP ? 100 : Math.min(Math.floor(x / CAP * 100), 99);
      function tous(k, f){ [].forEach.call(document.querySelectorAll('[data-jauge="' + k + '"]'), f); }
      tous('n', function(e){ e.textContent = x.toLocaleString('fr-FR'); });
      tous('barre', function(e){ e.style.width = pct + '%'; });
      tous('etat', function(e){ e.textContent = x >= CAP ? 'Le seuil des 800 est tenu ce mois-ci.' : 'On est sous le seuil des 800.'; });
      tous('reste', function(e){ e.textContent = x >= CAP ? '' : 'Il manque ' + (CAP - x) + ' ' + (CAP - x > 1 ? 'soutiens' : 'soutien') + ' pour y revenir.'; });
      if (retour) retour(x, CAP);
    }
    var nom = 'komuneJauge_' + Date.now(), s = document.createElement('script');
    var fin = setTimeout(function(){ s.remove(); }, 9000);
    window[nom] = function(rep){ clearTimeout(fin); var x = Math.round(lit(rep)); if (isFinite(x) && x >= 0) affiche(x); delete window[nom]; s.remove(); };
    var p = new URLSearchParams({sheet: ONGLET, range: CELL, headers: '0', tqx: 'out:json;responseHandler:' + nom, cacheBust: String(Date.now())});
    s.src = 'https://docs.google.com/spreadsheets/d/' + FEUILLE + '/gviz/tq?' + p.toString();
    document.body.appendChild(s);
  };
  if (document.querySelector('[data-jauge]') && !document.querySelector('[data-jauge-au-clic]')) K.jauge();

  /* ---------- retours des lecteur·ices : le message part par leur logiciel de mail ---------- */
  var ADRESSE_RETOURS = ['jeannette', 'komunemedia.fr'].join('@');
  function ouvreRetours(){
    var w = K.el('div', 'fenetre'); w.setAttribute('role', 'dialog'); w.setAttribute('aria-modal', 'true'); w.setAttribute('aria-label', 'Vos retours');
    w.innerHTML = '<div class="boite"><button type="button" class="fermer" aria-label="Fermer">✕</button>' +
      '<h2 style="font-size:28px">Dites-nous où on se trompe.</h2>' +
      '<p style="margin-top:10px">Une erreur dans un vote, un contexte qui manque, un désaccord avec notre méthode, un passage illisible, un bug : tout nous intéresse. On lit tout, et les corrections passent avant les nouveautés.</p>' +
      '<form novalidate><label for="r-sujet">Sur quoi porte votre retour ?</label><select id="r-sujet">' +
      '<option>Il manque du contexte</option><option>Une erreur ou une source qui manque</option><option>Notre méthode ou notre périmètre</option>' +
      '<option>On s\'y perd dans la page</option><option>Un bug ou un problème d\'affichage</option><option>Un sujet qu\'on ne traite pas encore</option><option>Autre</option></select>' +
      '<label for="r-message">Votre retour</label><textarea id="r-message" maxlength="2500" placeholder="Le plus précis possible : quelle loi, quel·le candidat·e, quelle phrase."></textarea>' +
      '<p class="pet" id="r-etat" role="status" style="margin:8px 0 0"></p>' +
      '<div class="rang" style="margin-top:14px"><button type="submit" class="b rose">Envoyer mon retour</button><button type="button" class="b" data-fermer>Annuler</button></div>' +
      '<p class="pet mut" style="margin:14px 0 0">Votre message s\'ouvre dans votre logiciel de mail : vous gardez la main. Pas de cookie, pas de traceur.</p></form></div>';
    document.body.appendChild(w); document.body.style.overflow = 'hidden';
    var avant = document.activeElement;
    function ferme(){ w.remove(); document.body.style.overflow = ''; if (avant && avant.focus) avant.focus(); }
    w.addEventListener('click', function(e){ if (e.target === w || e.target.closest('.fermer') || e.target.closest('[data-fermer]')) ferme(); });
    w.addEventListener('keydown', function(e){ if (e.key === 'Escape') ferme(); });
    w.querySelector('#r-sujet').focus();
    w.querySelector('form').addEventListener('submit', function(e){
      e.preventDefault();
      var m = w.querySelector('#r-message').value.trim(), s = w.querySelector('#r-sujet').value;
      if (m.length < 10){ w.querySelector('#r-etat').textContent = 'Il nous faut un peu plus que ça pour agir : décrivez le problème en quelques mots.'; return; }
      var corps = 'Sujet : ' + s + '\nPage : ' + location.pathname + location.hash + '\n\n' + m + '\n';
      location.href = 'mailto:' + ADRESSE_RETOURS + '?subject=' + encodeURIComponent('Retour comparateur - ' + s) + '&body=' + encodeURIComponent(corps);
      w.querySelector('form').innerHTML = '<p style="margin-top:14px"><b>Votre message est prêt.</b> Il vient de s\'ouvrir dans votre logiciel de mail : il ne reste qu\'à l\'envoyer. Si rien ne s\'est ouvert, copiez votre retour.</p>' +
        '<div class="rang"><button type="button" class="b rose" id="r-copier">Copier mon retour</button><button type="button" class="b" data-fermer>Fermer</button></div>';
      w.querySelector('#r-copier').addEventListener('click', function(){ var t = ADRESSE_RETOURS + '\n\nRetour comparateur - ' + s + '\n\n' + corps; var bt = this;
        if (navigator.clipboard) navigator.clipboard.writeText(t).then(function(){ bt.textContent = 'Copié'; }); });
    });
  }
  document.addEventListener('click', function(e){ if (e.target.closest && e.target.closest('[data-retours]')){ e.preventDefault(); ouvreRetours(); } });

  /* ---------- copier un lien ---------- */
  K.copie = function(texte, bouton){
    var avant = bouton.textContent; function dit(t){ bouton.textContent = t; setTimeout(function(){ bouton.textContent = avant; }, 1800); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(texte).then(function(){ dit('Lien copié'); }, function(){ dit('Copie impossible'); });
    else dit('Copie impossible');
  };

  /* ---------- typographie : jamais de ponctuation, de guillemet ou de symbole seul en début ou en fin de ligne ---------- */
  /* On remplace l'espace ordinaire par une espace insécable de même largeur : devant ? ! : ; » % €, après «,
     entre les milliers d'un nombre et après « n° ». Le texte ne change pas, seulement l'endroit où il peut passer à la ligne. */
  K.typo = function(t){
    return t.replace(/ ([?!:;\u00bb%\u20ac])/g, '\u00a0$1').replace(/\u00ab /g, '\u00ab\u00a0')
            .replace(/(\d) (?=\d{3}(?!\d))/g, '$1\u00a0').replace(/([nN]\u00b0) (?=\d)/g, '$1\u00a0');
  };
  (function(){
    var HORS = /^(SCRIPT|STYLE|TEXTAREA|INPUT|CODE|PRE|NOSCRIPT)$/, UTILE = /[?!:;\u00bb%\u20ac\u00ab\d]/;
    function traite(n){
      var p = n.parentNode; if (!p || HORS.test(p.nodeName)) return;
      var v = n.nodeValue; if (v.length < 2 || !UTILE.test(v)) return;
      var r = K.typo(v); if (r !== v) n.nodeValue = r;
    }
    function passe(racine){
      if (racine.nodeType === 3){ traite(racine); return; }
      if (racine.nodeType !== 1 || HORS.test(racine.nodeName)) return;
      var w = document.createTreeWalker(racine, NodeFilter.SHOW_TEXT, null), n, lot = [];
      while ((n = w.nextNode())) lot.push(n);
      for (var i = 0; i < lot.length; i++) traite(lot[i]);
    }
    if (!document.body) return;
    passe(document.body);
    if (window.MutationObserver) new MutationObserver(function(ms){
      for (var a = 0; a < ms.length; a++) for (var i = 0; i < ms[a].addedNodes.length; i++) passe(ms[a].addedNodes[i]);
    }).observe(document.body, {childList: true, subtree: true});
  })();
})();
