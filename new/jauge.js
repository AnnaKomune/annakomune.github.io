/* Jauge des soutiens mensuels : lit une seule cellule d'une feuille Google publique (meme source que la page actuelle). */
(function(){
  var FEUILLE = "1jGIf48AVtuHa3wEphqPUhDNARQ7Cch2HlNccEJSeo_w", ONGLET = "donnée site", CELL = "A1", CAP = 800;
  function nombre(v){ if (v == null) return NaN; var s = String(v).replace(/[^\d,.-]/g, '').replace(',', '.'); return parseFloat(s); }
  function lit(rep){
    var t = rep && rep.table; if (!t) return NaN;
    var c = t.rows && t.rows[0] && t.rows[0].c && t.rows[0].c[0];
    var v = c ? (c.f != null ? c.f : c.v) : null;
    var n = nombre(v); if (isFinite(n)) return n;
    return nombre(t.cols && t.cols[0] && t.cols[0].label);
  }
  function affiche(n){
    var pct = n >= CAP ? 100 : Math.min(Math.floor(n / CAP * 100), 99);
    [].forEach.call(document.querySelectorAll('[data-jauge="n"]'), function(e){ e.textContent = n.toLocaleString('fr-FR'); });
    [].forEach.call(document.querySelectorAll('[data-jauge="pct"]'), function(e){ e.textContent = pct + ' %'; });
    [].forEach.call(document.querySelectorAll('[data-jauge="barre"]'), function(e){ e.style.width = pct + '%'; });
    [].forEach.call(document.querySelectorAll('[data-jauge="reste"]'), function(e){
      e.textContent = n >= CAP ? 'Cap tenu ce mois-ci' : (CAP - n) + ' soutiens pour revenir à 800'; });
    [].forEach.call(document.querySelectorAll('[data-jauge="etat"]'), function(e){ e.textContent = n >= CAP ? 'Cap des 800 tenu' : 'Sous le cap des 800'; });
  }
  window.komuneJauge = function(){
    var nom = 'komuneJauge_' + Date.now(), s = document.createElement('script');
    var fin = setTimeout(function(){ s.remove(); }, 9000);
    window[nom] = function(rep){ clearTimeout(fin); var n = Math.round(lit(rep)); if (isFinite(n) && n >= 0) affiche(n); delete window[nom]; s.remove(); };
    var p = new URLSearchParams({sheet: ONGLET, range: CELL, headers: '0', tqx: 'out:json;responseHandler:' + nom, cacheBust: String(Date.now())});
    s.src = 'https://docs.google.com/spreadsheets/d/' + FEUILLE + '/gviz/tq?' + p.toString();
    document.body.appendChild(s);
  };
  if (document.querySelector('[data-jauge]')) window.komuneJauge();
})();
