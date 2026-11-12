/* Komune - page « Promesses VS Actes » : recherche, par sujet, par candidat·e, deux candidat·es côte à côte. */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, P = window.K_PVA, CAND = K.CAND;
  var zRes = document.getElementById('resultats'), zSuj = document.getElementById('z-sujet'), zCand = document.getElementById('z-cand');
  /* on ne garde que les candidat·es dont les positions sont relevées sur au moins un texte */
  var RELEVE = {}; P.lois.forEach(function(l){ Object.keys(l.pos).forEach(function(id){ RELEVE[id] = 1; }); });
  var ORDRE = B.sept.concat(B.cands.map(function(c){ return c.id; }).filter(function(id){ return B.sept.indexOf(id) < 0 && RELEVE[id]; })
    .sort(function(a, b){ return K.famille(CAND[a].nom).localeCompare(K.famille(CAND[b].nom), 'fr'); }));

  function comptes(cid){
    var k = {aligne: 0, partiel: 0, contraire: 0, heterogene: 0, 'non-testable': 0};
    P.lois.forEach(function(l){ k[l.pos[cid].alp]++; }); return k;
  }
  function selecteur(etiquette, exclus, sur){
    var s = K.el('select', 'champ'); s.setAttribute('aria-label', etiquette);
    var o0 = K.el('option', null, etiquette); o0.value = ''; s.appendChild(o0);
    ORDRE.forEach(function(id){ if (exclus && exclus.indexOf(id) >= 0) return; var o = K.el('option', null, CAND[id].nom + ' · ' + CAND[id].sigle); o.value = id; s.appendChild(o); });
    s.addEventListener('change', function(){ if (s.value) sur(s.value); });
    return s;
  }

  /* Une loi : carte dépliable. cids = 0, 1 ou 2 candidat·es affiché·es dans le format de base. */
  function carteLoi(l, cids, ouvert){
    cids = (cids || []).slice();
    var d = K.el('details', 'pli loi'); d.id = 'loi-' + l.id; if (ouvert) d.open = true;
    var s = K.el('summary'), t = K.el('div', 'pli-titre');
    t.appendChild(K.el('p', 'sur', K.surtitreLoi(l))); t.appendChild(K.el('h3', null, l.nom)); if (l.court) t.appendChild(K.el('p', null, l.court));
    s.appendChild(t);
    var droite = K.el('div', 'loi-droite');
    if (cids.length === 1){
      droite.appendChild(K.avatar(CAND[cids[0]]));
      var e = K.el('span', 'loi-egal'); e.appendChild(document.createTextNode('Promesses VS votes = ')); e.appendChild(K.alignement(l.pos[cids[0]].alp)); droite.appendChild(e);
    } else if (cids.length === 2){
      cids.forEach(function(id){ var x = K.el('span', 'loi-egal'); x.appendChild(K.avatar(CAND[id], 'p')); x.appendChild(K.alignement(l.pos[id].alp)); droite.appendChild(x); });
    } else droite.appendChild(K.el('span', 'puce mini', 'Comparer les candidat·es sur cette loi'));
    s.appendChild(droite); s.appendChild(K.el('span', 'chev')); d.appendChild(s);
    var corps = K.el('div', 'pli-corps'); d.appendChild(corps);
    var fait = false;
    function remplir(){
      corps.innerHTML = '';
      corps.appendChild(K.parcoursLoi(l));
      if (!cids.length){
        corps.appendChild(K.el('p', 'loi-invite', 'Choisis un·e candidat·e pour voir ses promesses, ses actes et son alignement sur ce texte.'));
        corps.appendChild(selecteur('Choisir un·e candidat·e', [], function(id){ cids = [id]; remplir(); }));
        return;
      }
      var z = K.el('div', 'fb-cote' + (cids.length > 1 ? ' deux' : ''));
      cids.forEach(function(id){ z.appendChild(K.formatPVA(l, id)); });
      corps.appendChild(z);
      var bas = K.el('div', 'loi-bas sans-impression');
      bas.appendChild(K.el('span', 'fb-lib', cids.length > 1 ? 'Changer le ou la deuxième candidat·e' : 'Chercher pour un·e autre candidat·e'));
      bas.appendChild(selecteur('Choisir un·e candidat·e', [cids[0]], function(id){ cids = [cids[0], id]; remplir(); }));
      if (cids.length > 1){ var un = K.el('button', 'b fin', 'Revenir à ' + CAND[cids[0]].court + ' seul·e'); un.type = 'button'; un.onclick = function(){ cids = [cids[0]]; remplir(); }; bas.appendChild(un); }
      var lien = K.el('button', 'b fin', 'Copier le lien'); lien.type = 'button';
      lien.onclick = function(){ K.copie(location.origin + location.pathname + '#loi=' + l.id + '&c=' + cids.join(','), lien); }; bas.appendChild(lien);
      corps.appendChild(bas);
      if (K.lexique) K.lexique(corps);
    }
    d.addEventListener('toggle', function(){ if (d.open && !fait){ fait = true; remplir(); } });
    if (ouvert){ fait = true; remplir(); }
    return d;
  }

  /* ---------- par sujet ---------- */
  var zThemes = document.getElementById('themes');
  B.themes.forEach(function(t){
    var b = K.el('button', 'puce', t.nom); b.type = 'button'; b.setAttribute('data-theme', t.n); b.setAttribute('aria-pressed', 'false');
    b.onclick = function(){ ouvreSujet(t.n, true); }; zThemes.appendChild(b);
  });
  function ouvreSujet(n, pousse){
    [].forEach.call(zThemes.children, function(b){ b.setAttribute('aria-pressed', String(+b.getAttribute('data-theme') === n)); });
    zSuj.innerHTML = '';
    var lois = P.lois.filter(function(l){ return l.theme === n; }), att = P.attente.filter(function(a){ return a.theme === n; });
    zSuj.appendChild(K.el('h3', 'z-titre', K.THEME[n]));
    if (!lois.length) zSuj.appendChild(K.el('p', null, 'Aucune comparaison publiée sur ce sujet pour l\'instant. On en ajoute chaque semaine.'));
    lois.forEach(function(l){ zSuj.appendChild(carteLoi(l, [])); });
    if (att.length){ var p = K.el('p', 'pet mut', lois.length ? 'D\'autres comparaisons sont en préparation sur ce sujet.' : 'Des comparaisons sont en préparation sur ce sujet.'); p.style.marginTop = '14px'; zSuj.appendChild(p); }
    if (pousse){ history.replaceState(null, '', '#sujet=' + n); zSuj.scrollIntoView({block: 'nearest'}); }
  }

  /* ---------- par candidat·e ---------- */
  var zTetes = document.getElementById('tetes'), tout = false, paire = null;
  function dessineTetes(){
    zTetes.innerHTML = '';
    var avec = ORDRE.filter(function(id){ var k = comptes(id); return k.aligne + k.partiel + k.contraire > 0; });
    var liste = tout ? ORDRE : B.sept.concat(avec.filter(function(id){ return B.sept.indexOf(id) < 0; })).slice(0, 11);
    liste.forEach(function(id){
      var c = CAND[id], b = K.el('button', 'tete-c'); b.type = 'button'; b.setAttribute('data-c', id);
      b.appendChild(K.avatar(c, 'g')); b.appendChild(K.el('b', null, c.court)); b.appendChild(K.el('span', null, c.sigle));
      b.onclick = function(){ if (paire){ choisirPaire(id); } else ouvreCand([id], true); };
      zTetes.appendChild(b);
    });
    if (!tout){ var v = K.el('button', 'tete-c plus'); v.type = 'button'; v.appendChild(K.el('b', null, 'Voir tout')); v.appendChild(K.el('span', null, 'tous et toutes les candidat·es')); v.onclick = function(){ tout = true; dessineTetes(); }; zTetes.appendChild(v); }
    marque();
  }
  var actifs = [];
  function marque(){ [].forEach.call(zTetes.querySelectorAll('[data-c]'), function(b){ var on = actifs.indexOf(b.getAttribute('data-c')) >= 0 || (paire && paire.indexOf(b.getAttribute('data-c')) >= 0); b.classList.toggle('on', !!on); }); }
  var bPaire = document.getElementById('b-paire'), aide = document.getElementById('aide-paire');
  bPaire.onclick = function(){
    if (paire){ paire = null; bPaire.setAttribute('aria-pressed', 'false'); aide.textContent = ''; marque(); return; }
    paire = []; bPaire.setAttribute('aria-pressed', 'true'); tout = true; dessineTetes(); aide.textContent = 'Touche deux candidat·es, l\'un·e après l\'autre.';
  };
  function choisirPaire(id){
    if (paire.indexOf(id) >= 0) paire.splice(paire.indexOf(id), 1); else paire.push(id);
    marque();
    if (paire.length === 2){ var p = paire.slice(); paire = null; bPaire.setAttribute('aria-pressed', 'false'); aide.textContent = ''; ouvreCand(p, true); }
    else aide.textContent = paire.length ? 'Encore un·e candidat·e.' : 'Touche deux candidat·es, l\'un·e après l\'autre.';
  }
  function titreCand(id){
    var c = CAND[id], k = comptes(id), w = K.el('div', 'c-titre');
    w.appendChild(K.avatar(c)); w.appendChild(K.el('h3', null, c.court + ' sur ' + P.lois.length + ' textes'));
    [['aligne', 'aligné', 'alignés'], ['partiel', 'partiellement aligné', 'partiellement alignés'], ['contraire', 'contradictoire', 'contradictoires'], ['non-testable', 'non testable', 'non testables']].forEach(function(x){
      if (!k[x[0]]) return; var s = K.el('span', 'c-compte'); s.appendChild(K.el('b', null, String(k[x[0]]))); s.appendChild(document.createTextNode(' ' + K.AL[x[0]][0] + ' ' + (k[x[0]] > 1 ? x[2] : x[1]))); w.appendChild(s); });
    return w;
  }
  function ouvreCand(ids, pousse, loiOuverte){
    actifs = ids.slice(); if (ids.some(function(id){ return !zTetes.querySelector('[data-c="' + id + '"]'); })){ tout = true; dessineTetes(); } else marque();
    zCand.innerHTML = '';
    ids.forEach(function(id){ zCand.appendChild(titreCand(id)); });
    if (ids.length === 2) zCand.appendChild(K.el('p', 'pet', 'Choisis une loi : les deux comparaisons s\'affichent côte à côte.'));
    P.lois.forEach(function(l){ zCand.appendChild(carteLoi(l, ids, loiOuverte === l.id)); });
    var f = K.el('p', 'pet'); f.style.marginTop = '14px';
    ids.forEach(function(id){ var a = K.el('a', 'puce mini', 'La fiche de ' + CAND[id].nom); a.href = K.racine + 'comparateur/candidats/#' + CAND[id].slug; a.style.marginRight = '8px'; f.appendChild(a); });
    zCand.appendChild(f);
    if (pousse){ history.replaceState(null, '', '#c=' + ids.join(',')); zCand.scrollIntoView({block: 'start'}); }
    if (loiOuverte){ var e = document.getElementById('loi-' + loiOuverte); if (e) setTimeout(function(){ e.scrollIntoView({block: 'start'}); }, 60); }
  }

  /* ---------- est-ce que les actes suivent la parole ? ---------- */
  (function(){
    var z = document.getElementById('barres'), n = P.lois.length;
    var lignes = ORDRE.map(function(id){ return {id: id, k: comptes(id)}; })
      .sort(function(a, b){ return (b.k.aligne + b.k.partiel + b.k.contraire) - (a.k.aligne + a.k.partiel + a.k.contraire) || b.k.aligne - a.k.aligne; });
    lignes.forEach(function(x){
      var c = CAND[x.id], r = K.el('button', 'barre-c'); r.type = 'button'; r.onclick = function(){ ouvreCand([x.id], true); };
      r.appendChild(K.avatar(c, 'p')); r.appendChild(K.el('b', null, c.court));
      var piste = K.el('span', 'barre-piste'), det = [];
      [['aligne', '✅'], ['partiel', '⚠️'], ['contraire', '❌'], ['non-testable', '➖']].forEach(function(s){
        var v = x.k[s[0]]; if (!v) return; var i = K.el('i', s[0]); i.style.width = (v / n * 100) + '%'; piste.appendChild(i); det.push(v + ' ' + s[1]); });
      r.appendChild(piste); r.appendChild(K.el('span', 'barre-det', det.join('  ')));
      r.setAttribute('aria-label', c.nom + ' : ' + x.k.aligne + ' alignés, ' + x.k.partiel + ' partiellement alignés, ' + x.k.contraire + ' contradictoires, ' + x.k['non-testable'] + ' non testables');
      z.appendChild(r);
    });
  })();

  /* ---------- recherche ---------- */
  var q = document.getElementById('q');
  function cherche(){
    var f = K.pli(q.value).trim(); zRes.innerHTML = ''; if (f.length < 2){ zRes.hidden = true; return; }
    zRes.hidden = false;
    var cs = ORDRE.filter(function(id){ return K.pli(CAND[id].nom + ' ' + CAND[id].parti).indexOf(f) >= 0; });
    var ls = P.lois.filter(function(l){ return K.pli([l.nom, l.court, l.sous, l.tags, K.THEME[l.theme]].join(' ')).indexOf(f) >= 0; });
    var ts = B.themes.filter(function(t){ return K.pli(t.nom).indexOf(f) >= 0; });
    function groupe(titre){ var g = K.el('div', 'res-groupe'); g.appendChild(K.el('h3', null, titre)); zRes.appendChild(g); return g; }
    if (cs.length){ var g1 = groupe('Candidat·es'), w = K.el('div', 'puces'); cs.forEach(function(id){ var b = K.el('button', 'puce'); b.type = 'button'; b.appendChild(K.avatar(CAND[id], 'p')); b.appendChild(document.createTextNode(CAND[id].nom)); b.onclick = function(){ ouvreCand([id], true); }; w.appendChild(b); }); g1.appendChild(w); }
    if (ts.length){ var g2 = groupe('Sujets'), w2 = K.el('div', 'puces'); ts.forEach(function(t){ var b = K.el('button', 'puce', t.nom); b.type = 'button'; b.onclick = function(){ ouvreSujet(t.n, true); }; w2.appendChild(b); }); g2.appendChild(w2); }
    if (ls.length){ var g3 = groupe('Lois'); ls.forEach(function(l){ g3.appendChild(carteLoi(l, [])); }); }
    if (!cs.length && !ls.length && !ts.length) zRes.appendChild(K.el('p', null, 'Rien ne correspond pour l\'instant. Les comparaisons sont ajoutées chaque semaine.'));
  }
  q.addEventListener('input', cherche);

  /* ---------- liens directs ---------- */
  function route(){
    var h = decodeURIComponent(location.hash.replace(/^#/, '')), o = {};
    h.split('&').forEach(function(x){ var i = x.indexOf('='); if (i > 0) o[x.slice(0, i)] = x.slice(i + 1); });
    if (o.c){ var ids = o.c.split(',').filter(function(id){ return CAND[id]; }).slice(0, 2); if (ids.length){ ouvreCand(ids, false, o.loi && K.LOI[o.loi] ? o.loi : null); setTimeout(function(){ (o.loi ? document.getElementById('loi-' + o.loi) || zCand : zCand).scrollIntoView({block: 'start'}); }, 80); return; } }
    if (o.loi && K.LOI[o.loi]){ ouvreSujet(K.LOI[o.loi].theme, false); var e = document.getElementById('loi-' + o.loi); if (e){ e.open = true; setTimeout(function(){ e.scrollIntoView({block: 'start'}); }, 80); } return; }
    if (o.sujet && K.THEME[+o.sujet]){ ouvreSujet(+o.sujet, false); setTimeout(function(){ document.getElementById('par-sujet').scrollIntoView({block: 'start'}); }, 80); }
  }
  dessineTetes();
  /* par défaut : le premier sujet qui a des comparaisons, pour arriver directement sur du contenu */
  var premier = B.themes.filter(function(t){ return P.lois.some(function(l){ return l.theme === t.n; }); }).sort(function(a, b){
    return P.lois.filter(function(l){ return l.theme === b.n; }).length - P.lois.filter(function(l){ return l.theme === a.n; }).length; })[0];
  if (premier) ouvreSujet(premier.n, false);
  route(); window.addEventListener('hashchange', route);
})();
