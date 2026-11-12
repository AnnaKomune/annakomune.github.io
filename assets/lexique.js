/* Komune - le lexique dans le texte : les mots difficiles sont soulignés en pointillés, un clic ouvre la définition.
   K.lexique(zone) souligne, dans une zone, la première occurrence de chaque mot du lexique. */
(function(){
  'use strict';
  var K = window.K, G = window.K_LEXIQUE || [];
  if (!G.length){ K.lexique = function(){}; return; }
  var PAR_ID = {}; G.forEach(function(e){ PAR_ID[e.id] = e; });

  /* Un sigle ne se reconnaît qu'à la casse exacte (« PS » oui, « ps » non) ; un mot ordinaire quelle que soit la casse.
     Du plus long au plus court, pour que « TVA sociale » gagne contre « TVA ». */
  var CIBLES = [];
  G.forEach(function(e){ (e.a || []).forEach(function(mot){ CIBLES.push([mot, e.id, !/^[A-Z0-9][A-Z0-9 .É]*$/.test(mot)]); }); });
  CIBLES.sort(function(a, b){ return b[0].length - a[0].length; });
  var LETTRE = /[0-9A-Za-zÀ-ÖØ-öø-ÿ·]/;
  function borne(t, i, j){ return !(i > 0 && LETTRE.test(t.charAt(i - 1))) && !(j < t.length && LETTRE.test(t.charAt(j))); }
  function cherche(txt){
    var trouves = [], bas = txt.toLowerCase(), sur = bas.length === txt.length;
    CIBLES.forEach(function(c){
      if (c[2] && !sur) return;
      var cible = c[2] ? bas : txt, mot = c[2] ? c[0].toLowerCase() : c[0], de = 0, k;
      while ((k = cible.indexOf(mot, de)) >= 0){
        de = k + 1; var fin = k + mot.length; if (!borne(txt, k, fin)) continue;
        if (trouves.every(function(x){ return k >= x[1] || fin <= x[0]; })) trouves.push([k, fin, c[1]]);
      }
    });
    return trouves.sort(function(a, b){ return a[0] - b[0]; });
  }

  var EXCLUS = 'a,button,summary,label,select,option,textarea,input,h1,h2,h3,h4,.mot,.bulle,.puce,.vote,.al,.av,.fb-th,.fb-col,.fb-lib,.fb-qui,#lexique,[aria-hidden="true"]';
  K.lexique = function(zone){
    if (!zone) return;
    var vus = {}, noeuds = [], n;
    var w = document.createTreeWalker(zone, NodeFilter.SHOW_TEXT, {acceptNode: function(x){
      var v = x.nodeValue, p = x.parentElement;
      if (!v || v.length < 2 || !/\S/.test(v) || !p || p.closest(EXCLUS)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT; }});
    while ((n = w.nextNode())) noeuds.push(n);
    noeuds.forEach(function(nd){
      var txt = nd.nodeValue, occ = cherche(txt).filter(function(o){ if (vus[o[2]]) return false; vus[o[2]] = 1; return true; });
      if (!occ.length) return;
      var frag = document.createDocumentFragment(), pos = 0;
      occ.forEach(function(o){
        if (o[0] > pos) frag.appendChild(document.createTextNode(txt.slice(pos, o[0])));
        var e = PAR_ID[o[2]], bt = K.el('button', 'mot', txt.slice(o[0], o[1])); bt.type = 'button'; bt.setAttribute('data-lex', o[2]); bt.setAttribute('aria-expanded', 'false');
        bt.appendChild(K.el('span', 'lecteur', ' (' + (e.d ? e.d + ', ' : '') + 'voir la définition)'));
        frag.appendChild(bt); pos = o[1];
      });
      if (pos < txt.length) frag.appendChild(document.createTextNode(txt.slice(pos)));
      nd.parentNode.replaceChild(frag, nd);
    });
  };

  /* la bulle de définition */
  var bulle = null, decl = null;
  function ferme(focus){ if (!bulle || bulle.hidden) return; bulle.hidden = true; if (decl){ decl.setAttribute('aria-expanded', 'false'); if (focus) decl.focus(); } decl = null; }
  function place(){
    bulle.style.left = '0px'; bulle.style.top = '0px';
    var r = decl.getBoundingClientRect(), b = bulle.getBoundingClientRect(), m = 10;
    var x = Math.max(m, Math.min(r.left + r.width / 2 - b.width / 2, document.documentElement.clientWidth - b.width - m));
    var y = r.bottom + 8; if (y + b.height > window.innerHeight - m && r.top - b.height - 8 > m) y = r.top - b.height - 8;
    bulle.style.left = Math.round(x + window.scrollX) + 'px'; bulle.style.top = Math.round(y + window.scrollY) + 'px';
  }
  function ouvre(bt){
    var e = PAR_ID[bt.getAttribute('data-lex')]; if (!e) return;
    if (!bulle){ bulle = K.el('div', 'bulle'); bulle.setAttribute('role', 'dialog'); bulle.setAttribute('aria-label', 'Définition'); bulle.tabIndex = -1; document.body.appendChild(bulle); }
    if (decl) decl.setAttribute('aria-expanded', 'false');
    bulle.innerHTML = '';
    bulle.appendChild(K.el('b', null, e.t + (e.d ? ' : ' + e.d : '')));
    bulle.appendChild(K.el('span', null, e.x));
    var bas = K.el('span', 'bulle-bas');
    if (e.s){ var s = K.el('a', null, 'Source : ' + (e.sn || 'voir') + ' ↗'); s.href = e.s; s.target = '_blank'; s.rel = 'noopener'; bas.appendChild(s); }
    var l = K.el('a', null, 'Tout le lexique'); l.href = K.racine + 'comparateur/#lex-' + e.id; bas.appendChild(l);
    bulle.appendChild(bas);
    decl = bt; bt.setAttribute('aria-expanded', 'true'); bulle.hidden = false; place();
  }
  document.addEventListener('click', function(ev){
    var bt = ev.target.closest && ev.target.closest('.mot[data-lex]');
    if (bt){ ev.preventDefault(); if (decl === bt && bulle && !bulle.hidden) ferme(true); else ouvre(bt); return; }
    if (bulle && !bulle.hidden && !ev.target.closest('.bulle')) ferme(false);
  });
  document.addEventListener('keydown', function(ev){ if (ev.key === 'Escape') ferme(true); });
  window.addEventListener('resize', function(){ ferme(false); });
})();
