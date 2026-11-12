/* Komune - page « Les candidat·es à la présidentielle 2027 » : une grille, et une fiche dépliée par personne. */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, F = window.K_FICHES;
  var CAND = {}, FICHE = {}, PAR_SLUG = {}; B.cands.forEach(function(c){ CAND[c.id] = c; PAR_SLUG[c.slug] = c; }); F.forEach(function(f){ FICHE[f.id] = f; });
  var grille = document.getElementById('c-grille'), zone = document.getElementById('c-fiche'), q = document.getElementById('c-q'), compte = document.getElementById('c-compte');
  /* ordre alphabétique des noms de famille : pas de classement */
  var ORDRE = B.cands.map(function(c){ return c.id; }).sort(function(a, b){ return K.famille(CAND[a].nom).localeCompare(K.famille(CAND[b].nom), 'fr'); });

  function dessine(){
    var f = K.pli(q.value).trim(), n = 0; grille.innerHTML = '';
    ORDRE.forEach(function(id){
      var c = CAND[id]; if (f && K.pli(c.nom + ' ' + c.parti).indexOf(f) < 0) return; n++;
      var a = K.el('a', 'cand-carte'); a.href = '#' + c.slug;
      a.appendChild(K.avatar(c, 'tg')); a.appendChild(K.el('b', null, c.nom)); a.appendChild(K.el('span', null, c.parti)); grille.appendChild(a);
    });
    compte.innerHTML = ''; compte.appendChild(K.el('b', null, String(n))); compte.appendChild(document.createTextNode(' candidat·e' + (n > 1 ? 's' : '') + (f ? ' pour cette recherche.' : '.')));
  }
  q.addEventListener('input', dessine);

  var PAST = ['Au Parlement aujourd\'hui', 'A siégé au Parlement', 'A été au gouvernement', 'Mandat local en cours', 'Mandat local passé'];
  function tableau(lignes){
    var t = K.el('table', 'reperes'), dates = lignes.some(function(l){ return l[0]; });
    lignes.forEach(function(l){
      var tr = K.el('tr');
      var maj = !l[0] && l[1].length < 90 && l[1] === l[1].toUpperCase() && /[A-ZÀ-Ý]{4}/.test(l[1]);
      if (dates && !maj) tr.appendChild(K.el('td', 'q', l[0]));
      var td = K.el('td', maj ? 'titre' : null); if (maj && dates) td.colSpan = 2; td.innerHTML = K.riche(l[1]).replace(/^<p>|<\/p>$/g, '');
      if (l[2]){ td.appendChild(document.createTextNode(' ')); var a = K.el('a', 'pet', 'Source ↗'); a.href = l[2]; a.target = '_blank'; a.rel = 'noopener'; td.appendChild(a); }
      tr.appendChild(td); t.appendChild(tr);
    });
    return t;
  }
  function pli(titre, sous, contenu, ouvert){
    var d = K.el('details', 'pli'); if (ouvert) d.open = true; var s = K.el('summary'), t = K.el('div', 'pli-titre'); t.appendChild(K.el('h3', null, titre)); if (sous) t.appendChild(K.el('p', null, sous));
    s.appendChild(t); s.appendChild(K.el('span', 'chev')); d.appendChild(s); var c = K.el('div', 'pli-corps'); c.appendChild(contenu); d.appendChild(c); return d;
  }
  function groupes(blocs){
    var w = K.el('div');
    blocs.forEach(function(b){ if (!b[1].length) return; w.appendChild(K.el('h4', 'sous-bloc', b[0])); w.appendChild(tableau(b[1])); });
    if (!w.children.length) w.appendChild(K.el('p', null, 'Rien à signaler.'));
    return w;
  }
  function ouvre(slug, defile){
    var c = PAR_SLUG[slug]; if (!c){ zone.hidden = true; zone.innerHTML = ''; return; }
    var f = FICHE[c.id]; zone.hidden = false; zone.innerHTML = '';
    var fer = K.el('a', 'b fin sans-impression', '← Tous et toutes les candidat·es'); fer.href = '#'; fer.onclick = function(e){ e.preventDefault(); history.pushState(null, '', location.pathname); ouvre(null); document.getElementById('c-grille').scrollIntoView({block: 'start'}); };
    zone.appendChild(fer);
    var tete = K.el('div', 'fiche-tete'); tete.appendChild(K.avatar(c, 'tg'));
    var d = K.el('div'); d.appendChild(K.el('h2', null, c.nom));
    var l1 = K.el('p', 'fiche-ligne'); l1.appendChild(K.el('span', 'puce parti', c.parti)); if (f.date) l1.appendChild(K.el('span', 'fiche-date', 'Déclaré·e : ' + f.date)); d.appendChild(l1);
    tete.appendChild(d); zone.appendChild(tete);

    var liens = K.el('div', 'rang fiche-liens');
    function lien(texte, href, cls, ext){ var a = K.el('a', 'b ' + (cls || ''), texte + (ext ? ' ↗' : '')); a.href = href; if (ext){ a.target = '_blank'; a.rel = 'noopener'; } liens.appendChild(a); }
    if (f.site) lien('Site de campagne', f.site, '', true);
    if (f.prog_url && f.prog) lien('Le programme, ' + f.prog, f.prog_url, '', true);
    else liens.appendChild(K.el('span', 'puce', 'Programme : pas encore publié'));
    /* ces deux accès n'apparaissent que si quelque chose est relevé pour cette personne */
    if (f.mes) lien('Ses mesures dans les programmes', K.racine + 'comparateur/programmes/#c=' + c.slug, 'vert');
    if (f.rel) lien('Promesses VS Actes', K.racine + 'comparateur/promesses-vs-actes/#c=' + c.id, 'rose');
    zone.appendChild(liens);

    var past = K.el('div', 'puces fiche-past');
    f.past.forEach(function(v, i){ var oui = v === '✅', non = v === '➖'; past.appendChild(K.el('span', 'puce mini ' + (oui ? 'oui' : non ? 'non' : 'doute'), PAST[i] + ' : ' + (oui ? 'oui' : non ? 'non' : 'pas encore vérifié'))); });
    zone.appendChild(past);

    zone.appendChild(pli('Mandats', 'Actuels d\'abord, puis passés', groupes(f.mandats), true));
    zone.appendChild(pli('Parcours et fonctions', 'Profession, parti, responsabilités non électives', groupes(f.parcours)));
    zone.appendChild(pli('Situation judiciaire', 'Formulée avec les qualifications exactes', f.judiciaire.length ? tableau(f.judiciaire) : K.el('p', null, 'Rien à signaler.')));
    var src = K.el('ul', 'fiche-src'); String(f.sources || '').split(/\s*[•\n]\s*/).forEach(function(x){ x = x.trim(); if (!x) return; var li = K.el('li'); li.innerHTML = K.riche(x).replace(/^<p>|<\/p>$/g, ''); src.appendChild(li); });
    zone.appendChild(pli('Sources', '', src));
    var enc = K.el('div', 'encart sans-impression'); enc.appendChild(K.el('p', null, 'Une erreur, une date, un mandat qui manque ? On corrige et on le dit.')); var br = K.el('button', 'b rose', 'J\'ai des retours'); br.type = 'button'; br.setAttribute('data-retours', ''); enc.appendChild(br); zone.appendChild(enc);
    document.title = c.nom + ' - Les candidat·es à la présidentielle 2027 - Komune';
    if (defile !== false) setTimeout(function(){ window.scrollTo({top: zone.getBoundingClientRect().top + window.scrollY - 120}); }, 30);
  }
  function route(){ var s = decodeURIComponent(location.hash.replace(/^#/, '')); if (s && PAR_SLUG[s]) ouvre(s); else { ouvre(null); document.title = 'Les candidat·es à la présidentielle 2027 - Komune'; } }
  dessine(); route(); window.addEventListener('hashchange', route); window.addEventListener('popstate', route);
})();
