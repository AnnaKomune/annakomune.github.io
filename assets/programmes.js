/* Komune - page « Les programmes, par sujet » : un sujet, ce que chaque candidat·e propose, avec la source. */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, P = window.KOMUNE_PROGRAMMES;
  var CAND = {}, PAR_NOM = {}; B.cands.forEach(function(c){ CAND[c.id] = c; PAR_NOM[c.nom] = c; });
  var ETAT = {}; P.etat.forEach(function(e){ ETAT[e.cand] = e; });
  var NONC = {}; P.etat.forEach(function(e){ if (e.candidat2027 === 'Non') NONC[e.cand] = 1; });
  function slug(s){ return K.pli(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }

  var SOUS = P.sous.map(function(s, i){ return {i: i, th: s[0], nom: s[1], id: slug(s[1]), n: 0, cands: {}, tags: {}}; });
  (function(){ var vus = {}; SOUS.forEach(function(s){ if (vus[s.id]) s.id += '-' + slug(P.themes[s.th] || '').slice(0, 12); vus[s.id] = 1; }); })();
  var SOUS_ID = {}; SOUS.forEach(function(s){ SOUS_ID[s.id] = s; });

  /* un document de parti sans candidat·e se rattache au ou à la candidat·e de ce parti quand il n'y en a qu'un·e */
  var PARTI_CAND = {}; B.cands.forEach(function(c){ var p = K.pli(c.parti).replace(/\s*\(.*$/, ''); (PARTI_CAND[p] = PARTI_CAND[p] || []).push(c); });
  function candDuDoc(d){
    if (d.cand) return NONC[d.cand] ? null : (PAR_NOM[d.cand] || null);
    var p = K.pli(d.parti || '').replace(/^parti /, ''), trouve = null;
    Object.keys(PARTI_CAND).forEach(function(k){ if (k.indexOf(p) >= 0 || p.indexOf(k.replace(/^parti /, '')) >= 0) if (PARTI_CAND[k].length === 1) trouve = PARTI_CAND[k][0]; });
    return trouve;
  }
  var MES = {};
  P.mesures.forEach(function(m){
    var d = P.docs[m[8]]; if (!d) return; var c = candDuDoc(d); if (!c) return; var s = SOUS[m[5]]; if (!s) return;
    (MES[s.i] = MES[s.i] || []).push({m: m, d: d, c: c}); s.n++; s.cands[c.id] = 1;
    (m[7] || []).forEach(function(t){ s.tags[t] = 1; });
  });
  SOUS.forEach(function(s){ s.cherche = K.pli(s.nom + ' ' + (P.themes[s.th] || '') + ' ' + Object.keys(s.tags).map(function(t){ return P.tags[t]; }).join(' ')); });

  var PAR_SLUG = {}; B.cands.forEach(function(c){ PAR_SLUG[c.slug] = c; });
  var zListe = document.getElementById('p-liste'), zChoix = document.getElementById('p-choix'), zFiche = document.getElementById('p-fiche');
  var seul = null;   /* arrivée depuis une fiche candidat·e : on ne garde que les sujets où ses documents ont des mesures */
  function garde(s){ return !seul || s.cands[seul.id]; }
  /* un émoji et une couleur de la charte par grand sujet, toujours les mêmes d'une visite à l'autre */
  var EMOJI = {1: '🛒', 2: '💼', 3: '☂️', 4: '🩺', 5: '🌍', 6: '🎓', 7: '🏠', 8: '🏤', 9: '🛂', 10: '⚖️', 11: '✊', 12: '🗳️', 13: '💶', 14: '🌾', 15: '🎭', 16: '💻', 17: '🌐', 18: '🚆'};
  var TEINTES = ['rose', 'bleu', 'vert', 'jaune'];
  var ouverts = {};   /* grands sujets dépliés par la personne : on les retrouve ouverts en revenant d'une fiche */
  function dessineSujets(filtre){
    zListe.innerHTML = ''; var f = K.pli(filtre).trim(), total = 0;
    document.getElementById('p-exemples').hidden = !!seul;
    if (seul){
      var b = K.el('div', 'prog-seul'); b.appendChild(K.avatar(seul));
      var t = K.el('p'); t.appendChild(K.el('b', null, seul.nom)); t.appendChild(document.createTextNode(' : les sujets sur lesquels ses documents contiennent des mesures. Ouvre un sujet pour les lire, à côté de celles des autres candidat·es.')); b.appendChild(t);
      var tous = K.el('a', 'b fin', 'Voir tous les sujets'); tous.href = '#'; tous.onclick = function(e){ e.preventDefault(); history.pushState(null, '', location.pathname); route(); }; b.appendChild(tous);
      zListe.appendChild(b);
    }
    Object.keys(P.themes).map(Number).sort(function(a, b){ return a - b; }).forEach(function(ti){
      var th = P.themes[ti];
      var ss = SOUS.filter(function(s){ return s.th === ti && s.n > 0 && garde(s) && s.nom !== 'Autre' && (!f || s.cherche.indexOf(f) >= 0); }).sort(function(a, b){ return a.nom.localeCompare(b.nom, 'fr'); });
      var autre = SOUS.filter(function(s){ return s.th === ti && s.n > 0 && garde(s) && s.nom === 'Autre' && (!f || s.cherche.indexOf(f) >= 0); });
      ss = ss.concat(autre); if (!ss.length) return;
      /* un grand sujet = une carte repliée : son nom, le nombre de sujets, et les sujets une fois dépliée.
         Pendant une recherche, les cartes qui contiennent un résultat sont ouvertes d'office. */
      var g = K.el('details', 'pli groupe-suj t-' + TEINTES[(ti - 1) % TEINTES.length]); if (f || ouverts[ti]) g.open = true;
      var sm = K.el('summary'), tt = K.el('div', 'pli-titre'); tt.appendChild(K.el('h3', null, th));
      if (EMOJI[ti]){ var em = K.el('span', 'suj-emo', EMOJI[ti]); em.setAttribute('aria-hidden', 'true'); sm.appendChild(em); }
      sm.appendChild(tt);
      var nb = K.el('span', 'suj-nb', String(ss.length)); nb.appendChild(K.el('span', 'suj-mot', ss.length > 1 ? ' sujets' : ' sujet')); nb.setAttribute('aria-label', ss.length + (ss.length > 1 ? ' sujets' : ' sujet')); sm.appendChild(nb); sm.appendChild(K.el('span', 'chev')); g.appendChild(sm);
      var corps = K.el('div', 'pli-corps'), w = K.el('div', 'puces');
      ss.forEach(function(s){ var a = K.el('a', 'puce', s.nom === 'Autre' ? 'Autres mesures' : s.nom); a.href = '#sujet=' + s.id + (seul ? '&c=' + seul.slug : ''); w.appendChild(a); total++; });
      corps.appendChild(w); g.appendChild(corps);
      g.addEventListener('toggle', function(){ if (!f) ouverts[ti] = g.open; });
      zListe.appendChild(g);
    });
    if (!total) zListe.appendChild(K.el('p', null, seul && !f ? 'Aucune mesure relevée dans ses documents pour l\'instant.' : 'Aucun sujet ne correspond. Essaie un autre mot.'));
  }
  document.getElementById('p-q').addEventListener('input', function(e){ if (zFiche.hidden === false) fermeSujet(); dessineSujets(e.target.value); });
  [].forEach.call(document.querySelectorAll('#p-exemples [data-s]'), function(b){ var s = SOUS.filter(function(x){ return x.nom === b.getAttribute('data-s'); })[0]; if (s) b.href = '#sujet=' + s.id; else b.remove(); });

  var charge = null;
  function textes(){
    if (!charge) charge = new Promise(function(ok){ if (window.KOMUNE_TEXTES) return ok();
      var s = document.createElement('script'); s.src = K.racine + 'programmes/textes.js?v=' + (P.maj || '') + '-b'; s.onload = ok; s.onerror = function(){ window.KOMUNE_TEXTES = {}; ok(); }; document.head.appendChild(s); });
    return charge;
  }
  function partage(texte, bouton){
    if (navigator.share){ navigator.share({text: texte}).catch(function(){}); return; }
    K.copie(texte, bouton);
  }
  function ouvreSujet(id, cslug){
    var s = SOUS_ID[id]; if (!s){ fermeSujet(); return; }
    zChoix.hidden = true; zFiche.hidden = false; zFiche.innerHTML = '<p>Chargement des mesures…</p>';
    textes().then(function(){
      var T = window.KOMUNE_TEXTES || {}, nomSujet = s.nom === 'Autre' ? 'Autres mesures' : s.nom;
      document.title = nomSujet + ' : les programmes, par sujet - Komune';
      zFiche.innerHTML = '';
      var haut = K.el('div', 'rang sans-impression'); haut.style.marginBottom = '18px';
      var r = K.el('a', 'b fin', '← Tous les sujets'); r.href = '#'; r.onclick = function(e){ e.preventDefault(); history.pushState(null, '', location.pathname + (seul ? '#c=' + seul.slug : '')); fermeSujet(); }; haut.appendChild(r);
      var cp = K.el('button', 'b fin', 'Copier le lien'); cp.type = 'button'; cp.onclick = function(){ K.copie(location.origin + location.pathname + '#sujet=' + id, cp); }; haut.appendChild(cp);
      var im = K.el('button', 'b fin', 'Imprimer'); im.type = 'button'; im.onclick = function(){ window.print(); }; haut.appendChild(im);
      zFiche.appendChild(haut);
      zFiche.appendChild(K.el('p', 'fiche-theme', (EMOJI[s.th] ? EMOJI[s.th] + ' ' : '') + (P.themes[s.th] || ''))); zFiche.appendChild(K.el('h2', null, nomSujet));

      var parCand = {}; (MES[s.i] || []).forEach(function(x){ (parCand[x.c.id] = parCand[x.c.id] || []).push(x); });
      var avec = Object.keys(parCand).sort(function(a, b){ return K.famille(CAND[a].nom).localeCompare(K.famille(CAND[b].nom), 'fr'); });
      var sans = B.cands.filter(function(c){ return !parCand[c.id]; }).sort(function(a, b){ return K.famille(a.nom).localeCompare(K.famille(b.nom), 'fr'); });

      var som = K.el('div', 'puces sans-impression'); som.style.margin = '16px 0 6px';
      avec.forEach(function(cid){ var a = K.el('a', 'puce mini'); a.appendChild(K.avatar(CAND[cid], 'p')); a.appendChild(document.createTextNode(CAND[cid].court)); a.href = '#sujet=' + id + '&c=' + CAND[cid].slug; som.appendChild(a); });
      zFiche.appendChild(som);

      avec.forEach(function(cid){
        var c = CAND[cid], bloc = K.el('section', 'prog-cand'); bloc.id = 'c-' + c.slug;
        var t = K.el('div', 'prog-tete'); t.appendChild(K.avatar(c)); var n = K.el('div'); n.appendChild(K.el('h3', null, c.nom)); n.appendChild(K.el('span', null, c.parti)); t.appendChild(n); bloc.appendChild(t);
        parCand[cid].forEach(function(x){
          var m = x.m, court = m[2] || '', tx = (T[m[0]] && T[m[0]].t) || court;
          var d = K.el('article', 'mesure');
          var nu = K.pli(court).replace(/\*$/, '').replace(/\s*\([^)]*\)\s*$/, '').trim();
          if (court && K.pli(tx).replace(/\s+/g, ' ').indexOf(nu.slice(0, 60)) !== 0) d.appendChild(K.el('h4', null, court));
          var p = K.el('div', 'mesure-txt'); p.innerHTML = K.riche(tx); d.appendChild(p);
          var src = K.el('p', 'mesure-src'); src.appendChild(K.el('b', null, 'Source : '));
          src.appendChild(document.createTextNode(x.d.doc + (x.d.cand ? '' : ' · document du parti') + ' '));
          var u = x.d.url || P.urls[m[10]] || ''; if (u){ var a = K.el('a', null, 'Voir le document ↗'); a.href = u; a.target = '_blank'; a.rel = 'noopener'; src.appendChild(a); }
          var pa = K.el('button', 'mesure-part sans-impression', 'Partager'); pa.type = 'button';
          pa.onclick = function(){ partage('« ' + (court || tx.slice(0, 200)) + ' » ' + c.nom + ', ' + x.d.doc + '. ' + location.origin + location.pathname + '#sujet=' + id + '&c=' + c.slug, pa); };
          src.appendChild(document.createTextNode(' ')); src.appendChild(pa);
          d.appendChild(src); bloc.appendChild(d);
        });
        var e = ETAT[c.nom]; if (e && e.etat) bloc.appendChild(K.el('p', 'prog-etat', 'État du programme : ' + e.etat));
        zFiche.appendChild(bloc);
      });
      if (sans.length){
        var z = K.el('section', 'prog-sans'); z.appendChild(K.el('h3', null, 'Rien de relevé sur ce sujet'));
        z.appendChild(K.el('p', 'pet', 'Ce qui ne veut pas dire « pas de position » : aucune mesure de leurs documents n\'est classée dans ce sujet pour l\'instant.'));
        z.appendChild(K.el('p', null, sans.map(function(c){ return c.nom; }).join(', ') + '.')); zFiche.appendChild(z);
      }
      var cible = cslug && document.getElementById('c-' + cslug);
      window.scrollTo({top: (cible || zFiche).getBoundingClientRect().top + window.scrollY - 130});
    });
  }
  function fermeSujet(){ zChoix.hidden = false; zFiche.hidden = true; document.title = 'Les programmes, par sujet - Komune'; }
  function route(){
    var o = {}; decodeURIComponent(location.hash.replace(/^#/, '')).split('&').forEach(function(x){ var i = x.indexOf('='); if (i > 0) o[x.slice(0, i)] = x.slice(i + 1); });
    var avant = seul; seul = (!o.sujet && o.c && PAR_SLUG[o.c]) || (o.sujet ? seul : null);
    if (o.sujet) ouvreSujet(o.sujet, o.c);
    else { fermeSujet(); if (o.q) document.getElementById('p-q').value = o.q; if (o.q || seul !== avant) dessineSujets(o.q || document.getElementById('p-q').value); }
  }
  dessineSujets(''); route(); window.addEventListener('hashchange', route); window.addEventListener('popstate', route);
})();
