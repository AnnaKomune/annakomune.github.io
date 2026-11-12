/* Komune - le format de base « Promesse VS Acte » : une loi, un·e candidat·e.
   Deux lignes (la personne, son parti), deux colonnes (promesses, actes), puis l'alignement.
   Utilisé par la page Promesses VS Actes et par le quiz « Qui tient parole ? ». */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, P = window.K_PVA;
  var CAND = {}; B.cands.forEach(function(c){ CAND[c.id] = c; });
  K.CAND = CAND;
  K.LOI = {}; P.lois.forEach(function(l){ K.LOI[l.id] = l; });
  K.THEME = {}; B.themes.forEach(function(t){ K.THEME[t.n] = t.nom; });

  /* Sur une motion de censure, « pour » veut dire « a voté la censure » : on le dit en toutes lettres. */
  K.voteLoi = function(l, v, groupe){
    if (!l.censure || v.c === 'na') return K.vote(v);
    var lib = {pour: 'A voté la censure', contre: "N'a pas voté la censure", npppv: "N'a pas voté la censure", abstention: 'Abstention', divise: 'Divisé sur la censure'}[v.c] || v.l;
    return K.el('span', 'vote ' + (v.c === 'pour' ? 'divise' : v.c === 'divise' ? 'divise' : 'npppv'), lib);
  };

  function bloc(x, source){
    var d = K.el('div', 'fb-texte');
    if (!x){ d.appendChild(K.el('p', 'mut', 'Rien de relevé.')); return d; }
    var p = K.el('p', 'fb-tete'); p.appendChild(K.el('b', null, x.t));
    if (x.a) p.appendChild(K.el('span', 'fb-an', ' (' + x.a + ')'));
    d.appendChild(p);
    if (x.r){
      var det = K.el('details', 'fb-suite'); det.appendChild(K.el('summary', null, 'Lire le détail'));
      var c = K.el('div'); c.innerHTML = K.riche(x.r); det.appendChild(c); d.appendChild(det);
    }
    if (source) d.appendChild(K.el('p', 'fb-src', 'Source : ' + source));
    return d;
  }

  function decompte(g){
    var w = K.el('div', 'fb-auto');
    var tot = g.pour + g.contre + g.abst + g.nv || 1, barre = K.el('div', 'fb-barre');
    [['pour', g.pour], ['contre', g.contre], ['abstention', g.abst], ['npppv', g.nv]].forEach(function(x){
      if (!x[1]) return; var i = K.el('i', x[0]); i.style.width = (x[1] / tot * 100) + '%'; barre.appendChild(i); });
    var p = K.el('p', 'fb-src'); p.appendChild(document.createTextNode('Décompte relevé automatiquement sur le scrutin n° ' + g.num + ', groupe ' + g.nom + '. '));
    var a = K.el('a', null, 'Voir le scrutin'); a.href = g.url; a.target = '_blank'; a.rel = 'noopener'; p.appendChild(a);
    if (g.pour + g.contre + g.abst + g.nv > 0) w.appendChild(barre);
    w.appendChild(p); return w;
  }

  K.formatPVA = function(l, cid){
    var c = CAND[cid], p = l.pos[cid], f = K.el('div', 'fb');
    var tete = K.el('div', 'fb-qui'); tete.appendChild(K.avatar(c)); var n = K.el('div'); n.appendChild(K.el('b', null, c.nom)); n.appendChild(K.el('span', null, c.parti)); tete.appendChild(n); f.appendChild(tete);

    var g = K.el('div', 'fb-grille'); g.setAttribute('role', 'table');
    function ligne(titre, cls){ var r = K.el('div', 'fb-ligne' + (cls ? ' ' + cls : '')); r.setAttribute('role', 'row'); var th = K.el('div', 'fb-th', titre); th.setAttribute('role', 'rowheader'); r.appendChild(th); return r; }
    function cellule(etiquette){ var d = K.el('div', 'fb-td'); d.setAttribute('role', 'cell'); d.appendChild(K.el('span', 'fb-col', etiquette)); return d; }
    var ent = K.el('div', 'fb-ligne fb-entete'); ent.setAttribute('role', 'row');
    ['', 'Promesses', 'Actes'].forEach(function(t){ var h = K.el('div', 'fb-th', t); h.setAttribute('role', 'columnheader'); ent.appendChild(h); });
    g.appendChild(ent);

    /* ligne de la personne */
    var r1 = ligne(c.court), a1 = cellule('Promesses'), b1 = cellule('Actes');
    a1.appendChild(bloc(p.pp, p.sp));
    var v1 = K.el('p', 'fb-vote'); v1.appendChild(K.el('span', 'fb-lib', 'Son vote')); v1.appendChild(K.voteLoi(l, p.vp)); b1.appendChild(v1);
    if (p.vp.r) b1.appendChild(K.el('p', 'fb-src', p.vp.r));
    b1.appendChild(bloc(p.ap));
    r1.appendChild(a1); r1.appendChild(b1); g.appendChild(r1);

    /* ligne du parti */
    var r2 = ligne(c.sigle, 'parti'), a2 = cellule('Promesses'), b2 = cellule('Actes');
    a2.appendChild(bloc(p.pg, p.sg));
    var v2 = K.el('p', 'fb-vote'); v2.appendChild(K.el('span', 'fb-lib', 'Vote du groupe')); v2.appendChild(K.voteLoi(l, p.vg, true)); b2.appendChild(v2);
    if (p.dg) b2.appendChild(K.el('p', 'fb-src', p.dg));
    if (p.ga) b2.appendChild(decompte(p.ga));
    b2.appendChild(bloc(p.ag));
    r2.appendChild(a2); r2.appendChild(b2); g.appendChild(r2);

    /* ligne de l'alignement, sur une seule colonne */
    var r3 = ligne('Alignement', 'al-ligne'), c3 = K.el('div', 'fb-td large'); c3.setAttribute('role', 'cell');
    var pa = K.el('p', 'fb-als');
    var s1 = K.el('span'); s1.appendChild(document.createTextNode(c.court + ' : ')); s1.appendChild(K.alignement(p.alp)); pa.appendChild(s1);
    var s2 = K.el('span'); s2.appendChild(document.createTextNode(c.sigle + ' : ')); s2.appendChild(K.alignement(p.alg)); pa.appendChild(s2);
    c3.appendChild(pa);
    if (p.com){ var pc = K.el('div', 'fb-com'); pc.innerHTML = K.riche(p.com); c3.appendChild(pc); }
    var lj = K.el('a', 'fb-juge', 'Comment on juge ?'); lj.href = K.racine + 'comparateur/#coulisses-3'; c3.appendChild(lj);
    r3.appendChild(c3); g.appendChild(r3);
    f.appendChild(g);
    if (l.censure) f.appendChild(K.el('p', 'fb-src', 'Le scrutin de référence est une motion de censure : la voter, c\'est s\'opposer au texte. Seules les voix pour sont décomptées.'));

    /* les sources, pas les chiffres */
    var src = K.el('details', 'fb-sources'); src.appendChild(K.el('summary', null, 'Les sources'));
    var ul = K.el('ul');
    function li(texte, url){ var x = K.el('li'); if (url){ var a = K.el('a', null, texte + ' ↗'); a.href = url; a.target = '_blank'; a.rel = 'noopener'; x.appendChild(a); } else x.textContent = texte; ul.appendChild(x); }
    if (p.sp) li('Promesse de ' + c.court + ' : ' + p.sp);
    if (p.sg && p.sg !== p.sp) li('Promesse du parti : ' + p.sg);
    (p.liens || []).forEach(function(x){ li(x.label || x.url, x.url); });
    (l.liens || []).forEach(function(x){ li(x.label || 'Source officielle', x.url); });
    if (!ul.children.length) li('Aucune source propre à cette comparaison : voir le dossier du texte.');
    src.appendChild(ul); f.appendChild(src);
    return f;
  };

  /* Le texte et son parcours : présentation, avertissement, initiative, relevé du scrutin. */
  K.parcoursLoi = function(l){
    var d = K.el('details', 'fb-parcours'); d.appendChild(K.el('summary', null, 'En apprendre plus sur le texte et son parcours'));
    var c = K.el('div', 'fb-parcours-corps');
    c.innerHTML = K.riche(l.chapo) + (l.avert ? K.riche(l.avert) : '') +
      (l.initiative ? '<h4>À l\'initiative</h4>' + K.riche(l.initiative) : '') +
      (l.releve ? '<h4>Le scrutin de référence</h4>' + K.riche(l.releve) : '');
    d.appendChild(c); return d;
  };

  K.surtitreLoi = function(l){ return [K.THEME[l.theme], l.sous, l.statut].filter(Boolean).join(' · '); };
})();
