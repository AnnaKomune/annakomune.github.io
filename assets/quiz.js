/* Komune - page « Teste tes connaissances » : trois quiz tirés des données du comparateur, toujours sourcés. */
(function(){
  'use strict';
  var K = window.K, B = window.K_BASE, P = window.K_PVA, Q = window.K_QUIZ, CAND = K.CAND, LOI = K.LOI;
  var SERIE = 6;

  function jeu(zone, questions, dessineQuestion){
    var serie, i, score;
    function debut(){ serie = K.melange(questions).slice(0, SERIE); i = 0; score = 0; suivante(); }
    function suivante(){
      zone.innerHTML = '';
      if (i >= serie.length){ fin(); return; }
      var carte = K.el('div', 'quiz-carte');
      carte.appendChild(K.el('p', 'quiz-num', 'Question ' + (i + 1) + ' sur ' + serie.length));
      var rep = K.el('div', 'quiz-rep'); rep.setAttribute('aria-live', 'polite');
      dessineQuestion(carte, serie[i], function(juste, detail){
        if (juste) score++;
        [].forEach.call(carte.querySelectorAll('.quiz-opt'), function(b){ b.disabled = true; });
        rep.appendChild(K.el('p', 'quiz-verdict ' + (juste ? 'ok' : 'ko'), juste ? 'Bien vu.' : 'Raté.'));
        if (detail) rep.appendChild(detail);
        var s = K.el('button', 'b rose', i === serie.length - 1 ? 'Voir mon score' : 'Question suivante'); s.type = 'button'; s.onclick = function(){ i++; suivante(); };
        rep.appendChild(s); s.focus();
      });
      carte.appendChild(rep); zone.appendChild(carte);
    }
    function fin(){
      var c = K.el('div', 'quiz-carte fin');
      c.appendChild(K.el('p', 'quiz-score', score + ' / ' + serie.length));
      c.appendChild(K.el('p', null, score === serie.length ? 'Sans faute.' : score >= serie.length / 2 ? 'Pas mal. Les réponses sont toutes sourcées : tu peux les vérifier.' : 'Pas simple. C\'est justement pour ça qu\'on a fait le comparateur.'));
      var r = K.el('button', 'b rose', 'Rejouer'); r.type = 'button'; r.onclick = debut; c.appendChild(r); zone.appendChild(c);
    }
    debut();
  }
  function option(texte, cls){ var b = K.el('button', 'quiz-opt' + (cls ? ' ' + cls : '')); b.type = 'button'; if (typeof texte === 'string') b.textContent = texte; else b.appendChild(texte); return b; }
  function marque(boutons, bon, choisi){ boutons.forEach(function(b){ if (b.getAttribute('data-v') === bon) b.classList.add('bon'); else if (b.getAttribute('data-v') === choisi) b.classList.add('faux'); }); }
  function lienSource(texte, url){ var p = K.el('p', 'quiz-src'); var a = K.el('a', null, texte + ' ↗'); a.href = url; a.target = '_blank'; a.rel = 'noopener'; p.appendChild(a); return p; }

  /* 1. Qui a voté quoi ? */
  jeu(document.getElementById('quiz-votes'), Q.votes, function(carte, q, repondre){
    var l = LOI[q.loi], c = CAND[q.cand], p = l.pos[q.cand];
    var t = K.el('div', 'quiz-qui'); t.appendChild(K.avatar(c, 'g')); var d = K.el('div'); d.appendChild(K.el('b', null, c.nom)); d.appendChild(K.el('span', null, c.parti)); t.appendChild(d); carte.appendChild(t);
    carte.appendChild(K.el('p', 'quiz-sur', K.surtitreLoi(l)));
    carte.appendChild(K.el('h3', null, l.nom));
    carte.appendChild(K.el('p', 'quiz-q', l.censure ? 'Ce texte est passé sans vote. ' + c.court + ' a-t-il ou elle voté la motion de censure de référence ?' : 'Qu\'a voté ' + c.court + ' ?'));
    var opts = l.censure ? [['pour', 'A voté la censure'], ['non', 'N\'a pas voté la censure']]
                         : [['pour', 'Pour'], ['contre', 'Contre'], ['abstention', 'Abstention'], ['npppv', 'N\'a pas pris part au vote']];
    var bon = l.censure ? (q.rep === 'pour' ? 'pour' : 'non') : q.rep;
    var w = K.el('div', 'quiz-opts'), bs = [];
    opts.forEach(function(o){ var b = option(o[1]); b.setAttribute('data-v', o[0]); bs.push(b);
      b.onclick = function(){
        marque(bs, bon, o[0]);
        var det = K.el('div'); if (p.ap && p.ap.t) det.appendChild(K.el('p', null, p.ap.t));
        var sc = (l.liens || []).filter(function(x){ return /scrutin/i.test(x.label); })[0] || (l.liens || [])[0];
        if (sc) det.appendChild(lienSource(sc.label || 'Source officielle', sc.url));
        var a = K.el('a', 'puce mini', 'Voir ses promesses et ses actes sur ce texte'); a.href = K.racine + 'comparateur/promesses-vs-actes/#c=' + c.id + '&loi=' + l.id; det.appendChild(a);
        repondre(o[0] === bon, det);
      }; w.appendChild(b); });
    carte.appendChild(w);
  });

  /* 2. Qui a promis quoi ? */
  jeu(document.getElementById('quiz-promesses'), Q.promesses, function(carte, q, repondre){
    carte.appendChild(K.el('p', 'quiz-sur', q.type === 'mesure' ? 'Mesure de programme' + (q.theme ? ' · ' + q.theme : '') : 'Déclaration publique'));
    carte.appendChild(K.el('blockquote', 'quiz-cit', q.type === 'mesure' ? q.texte : '« ' + q.texte + ' »'));
    carte.appendChild(K.el('p', 'quiz-q', q.type === 'mesure' ? 'Dans le programme de qui lit-on cette mesure ?' : 'Qui a dit ça ?'));
    var w = K.el('div', 'quiz-opts deux'), bs = [];
    K.melange([q.rep].concat(q.faux)).forEach(function(id){
      var c = CAND[id], x = K.el('span', 'quiz-cand'); x.appendChild(K.avatar(c, 'p')); x.appendChild(document.createTextNode(c.nom));
      var b = option(x); b.setAttribute('data-v', id); bs.push(b);
      b.onclick = function(){
        marque(bs, q.rep, id);
        var det = K.el('div'); det.appendChild(K.el('p', null, CAND[q.rep].nom + ', ' + CAND[q.rep].parti + '.'));
        if (q.detail && K.pli(q.detail).indexOf(K.pli(q.texte).slice(0, 50)) !== 0){ var dd = K.el('details', 'fb-suite'); dd.appendChild(K.el('summary', null, 'Lire le texte du programme')); var z = K.el('div'); z.innerHTML = K.riche(q.detail + (q.detail.length >= 700 ? '…' : '')); dd.appendChild(z); det.appendChild(dd); }
        if (q.url) det.appendChild(lienSource('Source : ' + q.src, q.url)); else det.appendChild(K.el('p', 'quiz-src', 'Source : ' + q.src));
        repondre(id === q.rep, det);
      }; w.appendChild(b); });
    carte.appendChild(w);
  });

  /* 3. Qui tient parole ? */
  jeu(document.getElementById('quiz-parole'), Q.parole, function(carte, q, repondre){
    var l = LOI[q.loi], c = CAND[q.cand];
    var t = K.el('div', 'quiz-qui'); t.appendChild(K.avatar(c, 'g')); var d = K.el('div'); d.appendChild(K.el('b', null, c.nom)); d.appendChild(K.el('span', null, c.parti)); t.appendChild(d); carte.appendChild(t);
    carte.appendChild(K.el('p', 'quiz-sur', K.surtitreLoi(l)));
    carte.appendChild(K.el('h3', null, l.nom));
    if (l.court) carte.appendChild(K.el('p', null, l.court));
    carte.appendChild(K.el('p', 'quiz-q', 'Sur ce texte, ses promesses et ses actes sont-ils alignés ?'));
    var w = K.el('div', 'quiz-opts'), bs = [];
    ['aligne', 'partiel', 'contraire'].forEach(function(code){
      var b = option(K.AL[code][0] + ' ' + K.AL[code][1]); b.setAttribute('data-v', code); bs.push(b);
      b.onclick = function(){ marque(bs, q.rep, code); var det = K.el('div', 'quiz-format'); det.appendChild(K.formatPVA(l, q.cand)); if (K.lexique) K.lexique(det); repondre(code === q.rep, det); };
      w.appendChild(b); });
    carte.appendChild(w);
  });
})();
