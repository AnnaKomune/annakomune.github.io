// Releve des scrutins de l'Assemblee nationale.
//
// Les serveurs de l'Assemblee ne sont pas joignables depuis l'atelier : ce
// releve se fait depuis le navigateur de la redaction. Mode d'emploi :
//
//  1. ouvrir n'importe quelle page de www.assemblee-nationale.fr ;
//  2. coller ce fichier entier dans la console ;
//  3. appeler KOMUNE.releve([["ECO-01","15","3738"], ["SAN-02","17","8280"]]) ;
//  4. appeler KOMUNE.telecharge() : le fichier scrutins-an.json part dans les
//     telechargements, il alimente scripts/scrutins.py.
//
// Le script lit la page publique, rien d'autre. Il ne modifie rien.

window.KOMUNE = (function () {
  var NOMS = [];           // rempli par KOMUNE.candidats([...])
  var RESULTATS = [];

  function sansAccent(s) {
    return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^a-zA-Z ]/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
  }

  function texte(e) {
    return e ? (e.textContent || "").replace(/\s+/g, " ").trim() : "";
  }

  function lit(html, noms) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    var corps = texte(doc.body);
    var res = { meta: {}, synthese: {}, groupes: {}, trouves: [], absents: [] };

    res.meta.numero = (texte(doc.querySelector("h1")).match(/n[°o]\s*(\d+)/) || [])[1] || "";
    res.meta.legislature = (corps.match(/Analyse du scrutin[^]{0,160}?(\d+)e l[ée]gislature/) || [])[1] || "";
    res.meta.seance = (html.match(/(?:Premi[èe]re|Deuxi[èe]me|Troisi[èe]me|Unique|Seconde)\s+s[ée]ance du [^<]{5,40}/i) || [])[0]
      || (html.match(/s[ée]ance du [^<]{5,40}/i) || [])[0] || "";
    res.meta.objet = (corps.match(/(Scrutin public n[°o]\s*\d+ sur [^]*?\.)\s/) || [])[1] || "";

    var i0 = corps.indexOf("Synthèse du vote");
    var sy = i0 < 0 ? "" : corps.slice(i0, i0 + 340);
    [["votants", /Nombre de votants\s*:\s*(\d+)/],
     ["exprimes", /suffrages exprim[ée]s\s*:\s*(\d+)/],
     ["majorite", /Majorit[ée] absolue[^:]*:\s*(\d+)/],
     ["pour", /Pour l['’]adoption\s*:\s*(\d+)/],
     ["contre", /Contre\s*:\s*(\d+)/],
     ["abstention", /Abstention\s*:\s*(\d+)/]].forEach(function (p) {
      var m = sy.match(p[1]); if (m) res.synthese[p[0]] = +m[1];
    });
    res.meta.issue = (sy.match(/L['’]Assembl[ée]e nationale (?:a|n['’]a) [a-z'’ ]{2,40}/) || [])[0] || "";

    var cherches = (noms || []).map(function (n) { return { brut: n, cle: sansAccent(n) }; });
    var vus = {};
    doc.querySelectorAll('ul.simple-tree-list[id^="groupe"]').forEach(function (g) {
      var sigle = g.id.replace(/^groupe/, ""), pos = {};
      g.querySelectorAll("li.relative-flex").forEach(function (s) {
        var m = texte(s.firstElementChild).match(/^(.+?)\s*:\s*(\d+)$/);
        if (!m) return;
        var p = m[1].trim();
        var gens = [].slice.call(s.querySelectorAll("ul ._small"));
        // [annonce par la page, nombre de noms listes] : un ecart se signale.
        pos[p] = [+m[2], gens.length];
        gens.forEach(function (a) {
          var k = sansAccent(texte(a));
          cherches.forEach(function (c) {
            if (k === c.cle || k.endsWith(" " + c.cle)) {
              vus[c.brut] = 1;
              res.trouves.push([c.brut, p, sigle, a.getAttribute ? (a.getAttribute("href") || "") : ""]);
            }
          });
        });
      });
      res.groupes[sigle] = pos;
    });
    // Un nom absent de la page n'est pas « non concerne » : s'il siegeait, il
    // n'a pas pris part au vote. C'est scripts/controle.py qui tranche, avec
    // les fenetres de mandat.
    res.absents = cherches.map(function (c) { return c.brut; })
      .filter(function (n) { return !vus[n]; });
    return res;
  }

  return {
    candidats: function (liste) { NOMS = liste; return NOMS.length; },
    resultats: function () { return RESULTATS; },
    releve: async function (liste) {
      for (var i = 0; i < liste.length; i++) {
        var id = liste[i][0], leg = liste[i][1], num = liste[i][2];
        var url = "/dyn/" + leg + "/scrutins/" + num;
        try {
          var r = await fetch(url);
          if (!r.ok) { RESULTATS.push({ id: id, leg: leg, num: num, erreur: r.status }); continue; }
          var o = lit(await r.text(), NOMS);
          o.id = id; o.leg = leg; o.num = num;
          o.source = "https://www.assemblee-nationale.fr" + url;
          RESULTATS.push(o);
        } catch (e) {
          RESULTATS.push({ id: id, leg: leg, num: num, erreur: "exception" });
        }
        await new Promise(function (f) { setTimeout(f, 200); });
      }
      return RESULTATS.length;
    },
    telecharge: function (nom) {
      var b = new Blob([JSON.stringify(RESULTATS)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(b);
      a.download = nom || "scrutins-an.json";
      document.body.appendChild(a); a.click(); a.remove();
      return RESULTATS.length;
    }
  };
})();
