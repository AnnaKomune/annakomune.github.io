/* Komune - page « Débats et meetings » : les prises de parole, rangées par thème, avec l'horodatage de la vidéo. */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, D = window.K_DEBATS;
  var CAND = {}; B.cands.forEach(function(c){ CAND[c.id] = c; });
  var zone = document.getElementById('d-liste'), q = document.getElementById('d-q'), res = document.getElementById('d-res');
  function lienTs(deb, cit){ var a = K.el('a', 'ts', cit.ts); a.href = deb.video + (deb.video.indexOf('?') >= 0 ? '&' : '?') + 't=' + cit.sec + 's'; a.target = '_blank'; a.rel = 'noopener'; a.setAttribute('aria-label', 'Ouvrir la vidéo à ' + cit.ts); return a; }
  function citation(deb, cit){
    var bq = K.el('blockquote', 'cit'); bq.appendChild(document.createTextNode('« ' + cit.texte + ' » ')); bq.appendChild(lienTs(deb, cit));
    if (cit.corr) bq.appendChild(K.el('small', null, 'Correction : ' + cit.corr));
    if (!cit.ctx) return bq;
    /* une phrase de contexte : ce qui est dit juste avant, à quoi la citation répond */
    var w = K.el('div', 'cit-bloc'); w.appendChild(K.el('p', 'cit-ctx', cit.ctx)); w.appendChild(bq); return w;
  }
  function carte(deb){
    var d = K.el('details', 'pli debat'); d.id = deb.id;
    var s = K.el('summary'), t = K.el('div', 'pli-titre'); t.appendChild(K.el('h3', null, deb.titre)); t.appendChild(K.el('p', null, deb.type + ' · ' + deb.date)); s.appendChild(t);
    var tetes = K.el('div', 'tetes'); deb.participants.forEach(function(id){ var a = K.avatar(CAND[id]); a.title = CAND[id].nom; tetes.appendChild(a); }); s.appendChild(tetes);
    s.appendChild(K.el('span', 'chev')); d.appendChild(s);
    var corps = K.el('div', 'pli-corps'); d.appendChild(corps);
    var fait = false;
    d.addEventListener('toggle', function(){ if (!d.open || fait) return; fait = true;
      var meta = K.el('p', 'pet'); meta.appendChild(document.createTextNode(deb.lieu + ' · ' + deb.duree + '. ' + deb.animation + ' '));
      var v = K.el('a', null, 'Voir la vidéo intégrale ↗'); v.href = deb.video; v.target = '_blank'; v.rel = 'noopener'; meta.appendChild(v); corps.appendChild(meta);
      var ch = K.el('input', 'champ'); ch.type = 'search'; var quoi = deb.type === 'Meeting' ? 'le meeting' : 'le débat'; ch.placeholder = 'Chercher dans ' + quoi + ' : retraites, salaires, dette, un nom…'; ch.setAttribute('aria-label', 'Chercher dans ' + quoi); corps.appendChild(ch);
      var onglets = K.el('div', 'puces onglets'); onglets.setAttribute('role', 'group'); onglets.setAttribute('aria-label', 'Thèmes du débat'); corps.appendChild(onglets);
      var z = K.el('div', 'debat-corps'); corps.appendChild(z);
      var actif = deb.themes[0].id;
      function theme(th){
        z.innerHTML = '';
        if (th.question){ var qq = K.el('div', 'debat-question'); qq.textContent = th.question; z.appendChild(qq); }
        if (th.contexte){ var cx = K.el('div', 'debat-question'); cx.appendChild(K.el('b', null, 'Le contexte. ')); cx.appendChild(document.createTextNode(th.contexte)); z.appendChild(cx); }
        var g = K.el('div', 'debat-prises' + (th.prises.length === 1 ? ' seul' : ''));
        th.prises.forEach(function(pr){ var c = CAND[pr.cand], b = K.el('article', 'prise'); var h = K.el('div', 'prise-tete'); h.appendChild(K.avatar(c)); h.appendChild(K.el('b', null, c.nom)); b.appendChild(h);
          pr.citations.forEach(function(ci){ b.appendChild(citation(deb, ci)); }); g.appendChild(b); });
        z.appendChild(g);
        if (th.defs && th.defs.length){ var dl = K.el('dl', 'debat-defs'); th.defs.forEach(function(x){ dl.appendChild(K.el('dt', null, x[0])); dl.appendChild(K.el('dd', null, x[1])); }); var dd = K.el('details', 'fb-sources'); dd.appendChild(K.el('summary', null, 'Les mots de ce thème')); dd.appendChild(dl); z.appendChild(dd); }
      }
      function cherche(){
        var f = K.pli(ch.value).trim(); if (f.length < 2){ onglets.hidden = false; theme(deb.themes.filter(function(t){ return t.id === actif; })[0]); return; }
        onglets.hidden = true; z.innerHTML = ''; var n = 0, g = K.el('div', 'debat-prises');
        deb.themes.forEach(function(th){ th.prises.forEach(function(pr){ var c = CAND[pr.cand]; var bons = pr.citations.filter(function(ci){ return K.pli(ci.texte + ' ' + (ci.ctx || '') + ' ' + c.nom + ' ' + th.titre).indexOf(f) >= 0; }); if (!bons.length) return;
          var b = K.el('article', 'prise'); var h = K.el('div', 'prise-tete'); h.appendChild(K.avatar(c)); var hh = K.el('div'); hh.appendChild(K.el('b', null, c.nom)); hh.appendChild(K.el('span', null, th.titre)); h.appendChild(hh); b.appendChild(h);
          bons.forEach(function(ci){ b.appendChild(citation(deb, ci)); n++; }); g.appendChild(b); }); });
        if (!n) z.appendChild(K.el('p', null, 'Rien ne correspond ici.')); else z.appendChild(g);
      }
      deb.themes.forEach(function(th){ var b = K.el('button', 'puce', th.titre); b.type = 'button'; b.setAttribute('aria-pressed', String(th.id === actif));
        b.onclick = function(){ actif = th.id; [].forEach.call(onglets.children, function(x){ x.setAttribute('aria-pressed', String(x === b)); }); theme(th); }; onglets.appendChild(b); });
      ch.addEventListener('input', cherche); theme(deb.themes[0]);
      if (d.getAttribute('data-q')){ ch.value = d.getAttribute('data-q'); cherche(); }
    });
    return d;
  }
  /* deux rubriques : les débats d'un côté, les meetings de l'autre, du plus récent au plus ancien */
  [['debats', 'Débat', 'Les débats', 'De nouveaux débats arrivent très vite.'], ['meetings', 'Meeting', 'Les meetings', 'De nouveaux meetings arrivent très vite.']].forEach(function(g){
    var sec = K.el('section', 'debat-groupe'); sec.id = g[0]; sec.appendChild(K.el('h2', null, g[2]));
    D.filter(function(deb){ return deb.type === g[1]; }).forEach(function(deb){ sec.appendChild(carte(deb)); });
    sec.appendChild(K.el('p', 'arrive', g[3])); zone.appendChild(sec);
  });

  /* recherche générale : dans tous les débats */
  q.addEventListener('input', function(){
    var f = K.pli(q.value).trim(); res.innerHTML = ''; if (f.length < 2){ res.hidden = true; return; } res.hidden = false;
    var n = 0;
    D.forEach(function(deb){ var k = 0; deb.themes.forEach(function(th){ th.prises.forEach(function(pr){ pr.citations.forEach(function(ci){ if (K.pli(ci.texte + ' ' + CAND[pr.cand].nom + ' ' + th.titre).indexOf(f) >= 0) k++; }); }); });
      if (!k) return; n += k;
      var b = K.el('button', 'puce', deb.titre + ' : ' + k + (k > 1 ? ' citations' : ' citation')); b.type = 'button';
      b.onclick = function(){ var d = document.getElementById(deb.id); d.setAttribute('data-q', q.value); if (d.open){ var ch = d.querySelector('input'); ch.value = q.value; ch.dispatchEvent(new Event('input')); } else d.open = true; d.scrollIntoView({block: 'start'}); };
      res.appendChild(b); });
    if (!n) res.appendChild(K.el('p', null, 'Rien ne correspond pour l\'instant.'));
  });
  if (location.hash && document.getElementById(location.hash.slice(1)) && document.getElementById(location.hash.slice(1)).tagName === 'DETAILS') document.getElementById(location.hash.slice(1)).open = true;
})();
