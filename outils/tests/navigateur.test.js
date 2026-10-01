// Tests navigateur (Playwright) : NODE_PATH=$(npm root -g) node outils/tests/navigateur.test.js
const { chromium } = require("playwright");
const path = require("path");
const URL = "file://" + path.join(__dirname, "..", "..", "index.html");

const JUSTES = {
  q1_1a: "batterie", q1_1b: "hacheur", q1_1c: "moteur à courant continu",
  q1_2: "4691,36 W", q1_3: "97,74 A", q1_4: "de la tension d'alimentation",
  q1_5a: "650", q1_5b: "1300", q1_5c: "1950",
  q2_1: "0,2", q2_2: "9,6 V", q2_3: "520 tr/min", q2_4: "0,4", q2_5: "19,2 V", q2_6: "1040 tr/min",
  q2_7: "0,5", q2_8: "24 V", q2_9: "1300 tr/min", q2_10: "0,8", q2_11: "38,4 V", q2_12: "2080 tr/min",
  q3_1: "convertir une tension continue en tension alternative", q3_2a: "continue", q3_2b: "alternative",
  q3_3: "112,75 W", q3_4: "100,32 W", q3_5: "0,89",
  q4_1: "310 V", q4_2: "219,2 V", q4_3: "20 ms", q4_4: "50 Hz",
};
let echecs = 0;
function verif(cond, msg) { console.log((cond ? "  ok  " : "  ÉCHEC ") + msg); if (!cond) echecs++; }

async function remplir(page) {
  for (const [id, v] of Object.entries(JUSTES)) {
    const sel = (await page.$(`#in-${id}`)) ? `#in-${id}` : `input[data-q="${id}"]`;
    if (await page.isEnabled(sel)) await page.fill(sel, v);
  }
}
async function printVisible(page, sel) {
  await page.emulateMedia({ media: "print" });
  const n = await page.$$eval(sel, els => els.filter(e => getComputedStyle(e).display !== "none").length);
  await page.emulateMedia({ media: "screen" });
  return n;
}

(async () => {
  const browser = await chromium.launch();
  for (const mode of ["training", "exam"]) {
    console.log("Mode " + mode);
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const erreurs = [];
    page.on("pageerror", e => erreurs.push(e.message));
    page.on("console", m => { if (m.type() === "error") erreurs.push(m.text()); });
    await page.goto(URL);
    verif(await page.isVisible("#home") && !(await page.isVisible("main.page")), "accueil seul visible");
    verif(!/bac|session|épreuve|baccalaur|BTS|CAP\b/i.test(await page.title()), "titre neutre");
    await page.click(`.btn-mode[data-mode="${mode}"]`);
    verif(await page.isVisible("main.page"), "sujet affiché");
    await page.waitForTimeout(1100);
    verif((await page.textContent("#timer-val")) !== "0:00:00", "chronomètre lancé");

    // documents
    await page.click('.rail .tab[data-doc="DT2"]');
    verif(await page.isVisible("#doc-DT2"), "panneau DT2 ouvert depuis le rail");
    await page.click("#dp-close");
    await page.click('.doc-chip[data-doc="DT3"] >> nth=0');
    verif(await page.isVisible("#doc-DT3"), "panneau DT3 ouvert depuis un en-tête de question");
    await page.click("#dp-close");
    verif((await page.$$(".btn-print")).length === 1, "un seul bouton « Imprimer ma copie »");

    if (mode === "training") {
      // unités : demi-point
      await page.fill("#in-q1_2", "4691,36");
      await page.click("#q1_2 .btn-validate");
      verif(await page.$eval("#q1_2", e => e.classList.contains("is-half")), "valeur sans unité → ½ point (orange)");
      verif(await page.isDisabled("#in-q1_2"), "réponse validée verrouillée");
      verif(await page.isVisible("#q1_2 .q-expl"), "démarche affichée après validation");
      // impression avant de finir : explications visibles, y compris non validées
      verif(await printVisible(page, ".q-expl") > 20, "impression entraînement : corrections visibles");
      await remplir(page);
      for (const id of Object.keys(JUSTES)) {
        if (await page.$(`#in-${id}`)) { if (id !== "q1_2") await page.click(`#${id} .btn-validate`); }
      }
      for (const f of ["q1_1", "q1_5", "q3_2"]) await page.click(`#${f} .btn-fast`);
      const note = (await page.textContent("#score-val")).trim();
      const fin = (await page.textContent("tfoot .final-note")).trim();
      console.log("    bandeau :", note, "| récapitulatif :", fin);
      verif(fin.startsWith("19,"), "note pondérée < 20 à cause du demi-point de Q1.2");
    } else {
      verif(await page.isVisible(".exam-state"), "« Note masquée » dans le bandeau");
      await remplir(page);
      verif(!(await page.isVisible(".btn-validate >> nth=0")), "pas de bouton Valider en examen");
      verif(await printVisible(page, ".q-expl") === 0, "impression avant remise : aucune correction");
      verif(await printVisible(page, ".print-nograde") === 1, "impression avant remise : « Copie non corrigée »");
      verif(!(await page.isVisible("#recap-graded")), "récapitulatif masqué avant remise");
      await page.click("#exam-submit");
      verif((await page.textContent("#exam-warn")).length > 0, "confirmation en deux temps");
      await page.click("#exam-submit");
      const fin = (await page.textContent("tfoot .final-note")).trim();
      console.log("    note finale :", fin);
      verif(fin === "20,0/20", "sujet entièrement juste = 20/20");
      verif(await page.isDisabled("#in-q4_4"), "copie verrouillée après remise");
      const t1 = await page.textContent("#timer-val"); await page.waitForTimeout(1200);
      verif(t1 === (await page.textContent("#timer-val")), "chronomètre arrêté à la remise");
      verif(await printVisible(page, ".q-expl") > 20, "impression après remise : corrections visibles");
      const rows = await page.$$eval("#recap-body tr", r => r.length);
      verif(rows === 4, "récapitulatif : 4 parties");
    }
    // mobile
    await page.setViewportSize({ width: 390, height: 800 });
    verif(await page.isVisible("#btn-docs"), "bouton « Documents » sous 760 px");
    const debord = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    verif(debord <= 0, "pas de défilement horizontal en 390 px (" + debord + ")");
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: path.join(process.env.SHOTS || "/tmp", `capture-${mode}.png`), fullPage: false });
    verif(erreurs.length === 0, "aucune erreur JavaScript " + (erreurs.length ? JSON.stringify(erreurs) : ""));
    await page.close();
  }
  await browser.close();
  console.log(echecs ? echecs + " échec(s)" : "Tous les tests navigateur passent");
  process.exit(echecs ? 1 : 0);
})();
