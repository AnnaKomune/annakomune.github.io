/* Komune - page « Les bases de l'élection » : quinze cartes à faire défiler, toutes sourcées. */
(function(){
  'use strict';
  var K = window.K;
var CC = 'https://www.conseil-constitutionnel.fr/le-bloc-de-constitutionnalite/texte-integral-de-la-constitution-du-4-octobre-1958-en-vigueur';
var CC22 = 'https://presidentielle2022.conseil-constitutionnel.fr/les-candidats/etre-candidat/etre-candidat-e-a-lelection-presidentielle.html';
var CC17 = 'https://www.conseil-constitutionnel.fr/actualites/communique/deroulement-de-l-election-presidentielle';
var CAL = 'https://www.touteleurope.eu/vie-politique-des-etats-membres/presidentielle-2027-calendrier-dates-inscription-candidats-vote/';
var CARTES = [
  {t: 'Qui peut se présenter ?', c: ['<p>Toute personne qui a la qualité d\'électeur français et qui n\'est frappée d\'aucune inéligibilité. La loi renvoie au code électoral pour l\'âge et les droits civiques.</p><p>Il n\'y a ni diplôme, ni expérience, ni parti exigés. Ce qui filtre, ce sont les parrainages.</p>'],
   s: 'Loi n° 62-1292 du 6 novembre 1962, et code électoral, art. L. 2 et L.O. 127, cités par le Conseil constitutionnel', u: CC22},
  {t: 'Les 500 parrainages', c: ['<p>Pour être candidat·e, il faut être présenté·e par au moins 500 élu·es habilité·es : parlementaires, député·es européen·nes élu·es en France, maires, conseiller·es départementaux et régionaux, entre autres.</p>'],
   s: 'Conseil constitutionnel, « Qui peut être candidat ? », élection de 2022', u: CC22},
  {t: '30 départements, et pas plus de 10 % d\'un seul', c: ['<p>Les 500 signatures doivent venir d\'au moins 30 départements ou collectivités d\'outre-mer différents. Et un même département ne peut pas fournir plus d\'un dixième des parrainages, soit 50.</p><p>Objectif : empêcher une candidature purement locale.</p>'],
   s: 'Conseil constitutionnel, « Qui peut être candidat ? », élection de 2022', u: CC22},
  {t: 'Un·e élu·e, un seul parrainage', c: ['<p>Chaque élu·e ne peut parrainer qu\'une seule personne, et une présentation envoyée ne peut plus être retirée.</p><p>Environ 42 000 élu·es sont habilité·es à parrainer. Les parrainages sont envoyés directement au Conseil constitutionnel.</p>'],
   s: 'Conseil constitutionnel, communiqué du 10 janvier 2017', u: CC17},
  {t: 'Les parrainages sont publics', c: ['<p>Depuis 2017, le Conseil constitutionnel publie l\'intégralité des parrainages validés, au fil de leur arrivée, deux fois par semaine. Avant, seuls 500 noms tirés au sort étaient publiés.</p><p>On sait donc qui a parrainé qui.</p>'],
   s: 'Conseil constitutionnel, communiqué du 10 janvier 2017', u: CC17},
  {t: 'Nul ne peut être candidat·e contre son gré', c: ['<p>Même avec 500 parrainages, le Conseil constitutionnel vérifie que la personne veut bien se présenter. Elle doit aussi déposer une déclaration de patrimoine et une déclaration d\'intérêts.</p><p>Aucun dossier à déposer en préfecture : c\'est le Conseil constitutionnel qui établit la liste.</p>'],
   s: 'Conseil constitutionnel, « Qui peut être candidat ? », élection de 2022 ; code électoral, art. L.O. 135-1', u: CC22},
  {t: 'Le calendrier de 2027', c: ['<p><b>Au plus tard le 7 février 2027</b> : décret de convocation des électeurs, dix semaines avant le vote.</p><p><b>12 mars 2027, 18 h</b> : fin de réception des parrainages au Conseil constitutionnel. Même jour : date limite d\'inscription sur les listes électorales.</p><p><b>5 avril</b> : ouverture de la campagne officielle. <b>18 avril</b> : premier tour. <b>2 mai</b> : second tour.</p>'],
   s: 'Dates arrêtées en Conseil des ministres le 1er juillet 2026, d\'après Touteleurope.eu, 7 octobre 2026. Le décret de convocation reste à paraître', u: CAL},
  {t: 'Deux tours, majorité absolue', c: ['<p>« Le Président de la République est élu à la majorité absolue des suffrages exprimés. » Si personne ne l\'obtient au premier tour, un second tour oppose les deux candidat·es arrivé·es en tête.</p>'],
   s: 'Constitution, art. 7', u: CC},
  {t: 'Cinq ans, deux mandats consécutifs au plus', c: ['<p>« Le Président de la République est élu pour cinq ans au suffrage universel direct. » Et nul ne peut exercer plus de deux mandats consécutifs.</p><p>Le suffrage universel direct date du référendum de 1962. Le quinquennat, de 2000. La limite de deux mandats, de 2008.</p>'],
   s: 'Constitution, art. 6 ; Nouveaux Cahiers du Conseil constitutionnel n° 34, 2012', u: CC},
  {t: 'Ce qu\'un président fait', c: ['<p>Il « veille au respect de la Constitution » (art. 5). Il « nomme le Premier ministre » (art. 8) et « préside le conseil des ministres » (art. 9). Il « promulgue les lois dans les quinze jours » (art. 10) et « signe les ordonnances et les décrets délibérés en conseil des ministres » (art. 13).</p>'],
   s: 'Constitution, art. 5, 8, 9, 10 et 13', u: CC},
  {t: 'Ce qu\'un président peut faire', c: ['<p>Soumettre certains projets de loi au référendum (art. 11). Dissoudre l\'Assemblée nationale, après consultation du Premier ministre et des présidents des assemblées (art. 12). Prendre des pouvoirs exceptionnels quand les institutions sont gravement menacées (art. 16).</p><p>Il est « le chef des armées » (art. 15) et « garant de l\'indépendance de l\'autorité judiciaire » (art. 64).</p>'],
   s: 'Constitution, art. 11, 12, 15, 16 et 64', u: CC},
  {t: 'Ce qu\'un président ne fait pas seul', c: ['<p>« Le Gouvernement détermine et conduit la politique de la nation » (art. 20). « Le Premier ministre dirige l\'action du Gouvernement » (art. 21). Et la plupart des actes du président sont contresignés par le Premier ministre et les ministres responsables (art. 19).</p><p>C\'est pour ça que les promesses d\'un·e candidat·e passent ensuite par un gouvernement et par le Parlement.</p>'],
   s: 'Constitution, art. 19, 20 et 21', u: CC},
  {t: 'Le 49.3, ce n\'est pas le président', c: ['<p>« Le Premier ministre peut, après délibération du conseil des ministres, engager la responsabilité du Gouvernement » sur un texte : il est adopté sans vote, sauf si une motion de censure est votée.</p><p>C\'est ce qui s\'est passé pour la réforme des retraites de 2023 : le scrutin de référence est alors la motion de censure, et voter pour la motion, c\'est voter contre le texte.</p>'],
   s: 'Constitution, art. 49, alinéa 3', u: CC},
  {t: 'Un président peut-il être jugé ?', c: ['<p>Pendant son mandat, il « n\'est pas responsable des actes accomplis en cette qualité », sauf exceptions prévues par la Constitution (art. 67). Il « ne peut être destitué qu\'en cas de manquement à ses devoirs » manifestement incompatible avec son mandat (art. 68).</p>'],
   s: 'Constitution, art. 67 et 68', u: CC},
  {t: 'Qui surveille l\'élection ?', c: ['<p>« Le Conseil constitutionnel veille à la régularité de l\'élection du Président de la République. » Il reçoit les parrainages, établit la liste des candidat·es, examine les réclamations et proclame les résultats.</p><p>Il envoie aussi des délégués dans les bureaux de vote.</p>'],
   s: 'Constitution, art. 58 ; Conseil constitutionnel, communiqué du 10 janvier 2017', u: CC}
];

  var n = 0, z = document.getElementById('diapo'), segs = document.getElementById('k-segs'), prec = document.getElementById('k-prec'), suiv = document.getElementById('k-suiv');
  function dessine(pousse){
    var c = CARTES[n]; z.innerHTML = '';
    z.appendChild(K.el('p', 'num', 'Carte ' + (n + 1) + ' sur ' + CARTES.length));
    z.appendChild(K.el('h3', null, c.t));
    var corps = K.el('div', 'corps'); corps.innerHTML = c.c.join(''); z.appendChild(corps);
    var s = K.el('p', 'source'); s.appendChild(document.createTextNode('Source : ' + c.s + '. '));
    var a = K.el('a', null, 'Ouvrir la source ↗'); a.href = c.u; a.target = '_blank'; a.rel = 'noopener'; s.appendChild(a); z.appendChild(s);
    segs.innerHTML = ''; CARTES.forEach(function(_, i){ segs.appendChild(K.el('i', i < n ? 'ok' : i === n ? 'now' : '')); });
    prec.disabled = n === 0; suiv.textContent = n === CARTES.length - 1 ? 'Recommencer' : 'Suivante';
    if (pousse && history.replaceState) history.replaceState(null, '', '#carte=' + (n + 1));
  }
  prec.onclick = function(){ if (n > 0){ n--; dessine(true); } };
  suiv.onclick = function(){ n = (n + 1) % CARTES.length; dessine(true); };
  document.addEventListener('keydown', function(e){ if (e.target && /input|textarea|select/i.test(e.target.tagName)) return;
    if (e.key === 'ArrowRight'){ n = (n + 1) % CARTES.length; dessine(true); } else if (e.key === 'ArrowLeft' && n > 0){ n--; dessine(true); } });
  /* recherche dans les cartes */
  var q = document.getElementById('b-q'), res = document.getElementById('b-res');
  var idx = CARTES.map(function(c){ var d = document.createElement('div'); d.innerHTML = c.c.join(' '); return K.pli(c.t + ' ' + d.textContent + ' ' + c.s); });
  q.addEventListener('input', function(){
    var f = K.pli(q.value).trim(); res.innerHTML = ''; if (f.length < 2){ res.hidden = true; return; } res.hidden = false;
    var vus = CARTES.map(function(c, i){ return i; }).filter(function(i){ return idx[i].indexOf(f) >= 0; });
    if (!vus.length){ res.appendChild(K.el('p', null, 'Rien ne correspond dans les cartes pour l\'instant.')); return; }
    var w = K.el('div', 'puces'); vus.forEach(function(i){ var b = K.el('button', 'puce', (i + 1) + '. ' + CARTES[i].t); b.type = 'button';
      b.onclick = function(){ n = i; dessine(true); document.getElementById('cartes').scrollIntoView({block: 'start'}); }; w.appendChild(b); }); res.appendChild(w);
  });
  var m = /carte=(\d+)/.exec(location.hash); if (m && +m[1] >= 1 && +m[1] <= CARTES.length) n = +m[1] - 1;
  document.getElementById('titre-cartes').textContent = 'Les bases, en ' + CARTES.length + ' cartes';
  dessine(false);
})();
