// Tests unitaires du moteur de correction sur chaque question du sujet : node outils/tests/grading.test.js
const fs = require("fs"), path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "..", "index.html"), "utf8");
const G = new Function(html.match(/\/\*GRADING-START\*\/([\s\S]*?)\/\*GRADING-END\*\//)[1] + "; return Grading;")();
const QCFG = JSON.parse(html.match(/window\.__QCFG__ = (\{.*?\});\n/)[1]);

// [réponse saisie, score attendu]
const CAS = {
  q1_1a: [["batterie", 1], ["Batteries", 1], ["la batterie d'accumulateurs", 1], ["accus", 1], ["baterie", 1], ["hacheur", 0], ["moteur", 0]],
  q1_1b: [["hacheur", 1], ["Hâcheur", 1], ["le variateur", 1], ["convertisseur continu-continu", 1], ["hacheru", 1], ["onduleur", 0], ["batterie", 0], ["convertisseur", 0]],
  q1_1c: [["moteur", 1], ["Moteur à courant continu", 1], ["machine électrique", 1], ["roue", 0], ["hacheur", 0]],
  q1_2: [["4691,36 W", 1], ["Pa = 4691.36 W", 1], ["4 691,36 watts", 1], ["4691,358 W", 1], ["4,69 kW", 1], ["4691,36", 0.5], ["4691,36 V", 0.5], ["4,69", 0], ["3800 W", 0], ["4691 W", 0]],
  q1_3: [["97,74 A", 1], ["I = 97.74 ampères", 1], ["97,73 A", 1], ["97,74", 0.5], ["97,74 W", 0.5], ["79,17 A", 0]],
  q1_4: [["de la tension", 1], ["La Tension d'alimentation", 1], ["tention", 1], ["U", 1], ["du courant", 0], ["de la fréquence", 0]],
  q1_5a: [["650", 1], ["650 tr/min", 1], ["650,04", 1], ["600", 0]],
  q1_5b: [["1300", 1], ["1 300", 1], ["1200", 0]],
  q1_5c: [["1950", 1], ["1950,0", 1], ["1900", 0]],
  q3_1: [["convertir du continu en alternatif", 1], ["transforme une tension continue en tension alternative", 1], ["DC -> AC", 1], ["il convertit le continu", 0], ["redresser", 0]],
  q3_2a: [["continue", 1], ["Continu", 1], ["DC", 1], ["alternative", 0], ["continue et alternative", 0]],
  q3_2b: [["alternative", 1], ["alternatif", 1], ["AC", 1], ["sinusoïdale", 1], ["continue", 0]],
  q3_3: [["112,75 W", 1], ["112.75 watts", 1], ["112,75", 0.5], ["112,75 VA", 0.5], ["11,25 W", 0]],
  q3_4: [["100,32 W", 1], ["100,32", 0.5], ["132 W", 0], ["100,32 VA", 0.5]],
  q3_5: [["0,89", 1], ["0.89", 1], ["0,8898", 1], ["η = 0,89", 1], ["1,12", 0], ["0,9", 0], ["0,88", 0]],
  q4_1: [["310 V", 1], ["300 V", 1], ["311 volts", 1], ["310", 0.5], ["310 Hz", 0.5], ["600 V", 0], ["3 V", 0]],
  q4_2: [["219,20 V", 1], ["212,13 V", 1], ["220 V", 1], ["212,13", 0.5], ["300 V", 0], ["155 V", 0]],
  q4_3: [["20 ms", 1], ["T = 20 ms", 1], ["0,02 s", 1], ["20 millisecondes", 1], ["20", 0.5], ["0,02", 0], ["20 s", 0.5], ["10 ms", 0]],
  q4_4: [["50 Hz", 1], ["50 hertz", 1], ["50", 0.5], ["50 ms", 0.5], ["0,05 Hz", 0], ["25 Hz", 0]],
};
const ALPHA = { q2_1: 0.2, q2_4: 0.4, q2_7: 0.5, q2_10: 0.8 };
const UMOY = { q2_2: 9.6, q2_5: 19.2, q2_8: 24, q2_11: 38.4 };
const VIT = { q2_3: 520, q2_6: 1040, q2_9: 1300, q2_12: 2080 };
const fr = x => String(x).replace(".", ",");
for (const [id, a] of Object.entries(ALPHA)) CAS[id] = [[fr(a), 1], [String(a), 1], ["α = " + fr(a), 1], [String(a * 100), 0], [fr(a + 0.1), 0]];
for (const [id, u] of Object.entries(UMOY)) CAS[id] = [[fr(u) + " V", 1], ["Umoy = " + u + " volts", 1], [fr(u), 0.5], [fr(u) + " A", 0.5], [fr(u + 1) + " V", 0]];
for (const [id, n] of Object.entries(VIT)) CAS[id] = [[n + " tr/min", 1], [n + " tr.min-1", 1], [n + " tr·min⁻¹", 1], [n + " tours par minute", 1], [n + " rpm", 1], [n, 0.5], [n + " Hz", 0.5], [(n + 50) + " tr/min", 0]];

let ok = 0, ko = 0;
const manquants = Object.keys(QCFG).filter(id => !CAS[id]);
if (manquants.length) { console.log("Questions sans test :", manquants); ko++; }
for (const [id, cas] of Object.entries(CAS)) {
  if (!QCFG[id]) { console.log("Question inconnue :", id); ko++; continue; }
  for (const [rep, att] of cas) {
    const r = G.grade(String(rep), QCFG[id].grader);
    const s = r.score || 0;
    if (s === att) ok++; else { ko++; console.log(`ÉCHEC ${id} « ${rep} » : obtenu ${s}, attendu ${att}`, r); }
  }
}
console.log(`${ok} cas justes, ${ko} échec(s)`);
process.exit(ko ? 1 : 0);
