#!/usr/bin/env python3
"""Génère index.html à partir du gabarit et du contenu du sujet.

Le bloc <style>, le moteur Grading et le moteur applicatif sont repris tels
quels depuis outils/gabarit-exercice-interactif.html ; seuls changent les
points de configuration prévus par le gabarit (durée conseillée, DECOR,
DR_NAMES) et le contenu du sujet décrit ci-dessous.

Usage : python3 outils/generer.py
"""
import base64
import json
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
GABARIT = os.path.join(ICI, "gabarit-exercice-interactif.html")
SORTIE = os.path.join(RACINE, "index.html")


# ---------------------------------------------------------------- images
def img(nom):
    chemin = os.path.join(ICI, "images", nom)
    mime = "image/jpeg" if nom.endswith(".jpg") else "image/png"
    with open(chemin, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode("ascii"))


IMG = {k: img(f) for k, f in {
    "kart": "kart.jpg", "moteur": "moteur.jpg", "chaine": "chaine.png", "hacheur": "hacheur.png",
    "r1": "r1.png", "r2": "r2.png", "r3": "r3.png", "r4": "r4.png",
    "schema": "schema.png", "sinus": "sinus.png"}.items()}


# ---------------------------------------------------------------- unités
def unite(label, *accept):
    return {"label": label, "accept": list(accept)}


U_W = unite("W", "w", "watt", "watts")
U_KW = unite("kW", "kw", "kilowatt", "kilowatts")
U_A = unite("A", "a", "ampere", "amperes")
U_V = unite("V", "v", "volt", "volts")
U_TRMIN = unite("tr/min", "tr/min", "trmin", "trmin-1", "tr/mn", "trmn", "trmn-1", "tour/min", "tours/min",
                "tourmin", "toursmin", "tourmin-1", "toursmin-1", "tours/minute", "toursminute", "tr/minute",
                "trminute", "rpm")
U_MS = unite("ms", "ms", "milliseconde", "millisecondes")
U_S = unite("s", "s", "seconde", "secondes")
U_HZ = unite("Hz", "hz", "hertz")

H_UNITE = ("Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la moitié des points de la question.")
H_CENT = "Arrondir au centième. " + H_UNITE
H_ENTIER = "Arrondir à l'entier. " + H_UNITE
H_ALPHA = "Nombre sans unité, compris entre 0 et 1, arrondi au centième (exemple : 0,35)."

# ---------------------------------------------------------------- parties
PARTS = [
    {"num": "1", "title": "Le kart électrique : moteur à courant continu", "minutes": 20, "duration": "20 min"},
    {"num": "2", "title": "Faire varier la vitesse : le hacheur", "minutes": 25, "duration": "25 min"},
    {"num": "3", "title": "Courant alternatif : l'onduleur", "minutes": 15, "duration": "15 min"},
    {"num": "4", "title": "Analyse de la tension de sortie de l'onduleur", "minutes": 10, "duration": "10 min"},
]
TOTAL_MIN = sum(p["minutes"] for p in PARTS)

QCFG = {}


def fr(x, d=1):
    return ("%." + str(d) + "f") % x


def duree_longue(minutes):
    h, m = divmod(minutes, 60)
    return "%d h %02d" % (h, m) if h else "%d min" % m


# ---------------------------------------------------------------- briques HTML
def chip(doc):
    return '<button type="button" class="doc-chip" data-doc="%s" aria-pressed="false">%s</button>' % (doc, doc)


def qbar(label, docs):
    d = " ".join(chip(x) for x in docs) if docs else "aucun"
    return ('<div class="qbar" role="group" aria-label="%s"><div class="qb-num">%s</div>'
            '<div class="qb-docs">Documents à consulter : %s</div>'
            '<div class="qb-ans">Répondre : ci-dessous</div></div>' % (label, label, d))


def q(qid, label, part, stem, hint, grader, expected, why, pts=1):
    QCFG[qid] = {"label": label, "part": part, "pts": pts, "grader": grader}
    return """
        <div class="q" id="{id}" data-q="{id}">
          <p class="q-stem"><span class="q-num">{label}</span> <strong>{stem}</strong></p>
          <p class="q-hint" id="h-{id}">{hint}</p>
          <div class="q-row">
            <input type="text" class="q-input" id="in-{id}" aria-label="Réponse {label}" aria-describedby="h-{id}" autocomplete="off" autocapitalize="off" spellcheck="false">
            <button type="button" class="btn btn-validate">Valider</button>
            <span class="q-status" aria-live="polite"></span>
            <span class="print-only pstat">Non validée : comptée fausse</span>
          </div>
          <p class="q-msg" role="alert"></p>
          <div class="q-expl" hidden>
            <p class="q-unit-msg" hidden></p>
            <p class="q-expected"><span>Réponse attendue :</span> {expected}</p>
            <div class="q-why">{why}</div>
          </div>
        </div>""".format(id=qid, label=label, stem=stem, hint=hint, expected=expected, why=why)


SOL_STYLE = "width:100%;max-width:none;flex:none"


def sol(qid, label, part, aria, grader, pts=1):
    QCFG[qid] = {"label": label, "part": part, "pts": pts, "grader": grader}
    return ('<div class="sol"><input type="text" class="q-input" data-q="%s" aria-label="%s" autocomplete="off" '
            'autocapitalize="off" spellcheck="false" style="%s">'
            '<span class="mark" aria-live="polite" style="display:block;font-size:.8rem;font-weight:700;min-height:1.1em"></span></div>'
            % (qid, aria, SOL_STYLE))


def fast(qid, label, stem, hint, corps, expected, why):
    return """
        <div class="q fast-q" id="{id}">
          <p class="q-stem"><span class="q-num">{label}</span> <strong>{stem}</strong></p>
          <p class="q-hint">{hint}</p>
          {corps}
          <div class="fast-foot"><button type="button" class="btn btn-fast">Valider</button>
            <span class="q-status" aria-live="polite"></span></div>
          <p class="q-msg" role="alert"></p>
          <div class="q-expl" hidden>
            <p class="q-expected"><span>Réponses attendues :</span> {expected}</p>
            <div class="q-why">{why}</div>
          </div>
        </div>""".format(id=qid, label=label, stem=stem, hint=hint, corps=corps, expected=expected, why=why)


def kw(*groupes, forbid=None):
    g = {"type": "kw", "any": [list(groupes)]}
    if forbid:
        g["forbid"] = forbid
    return g


def num(value, tol, u=None, variants=None):
    g = {"type": "num", "value": value, "absTol": tol}
    if u:
        g["unit"] = u
    if variants:
        g["variants"] = variants
    return g


def part_head(p, pts):
    poids = p["minutes"] / TOTAL_MIN * 100
    return """
  <section class="part" id="partie-{n}" aria-labelledby="t-partie-{n}">
    <header class="part-head"><div class="part-num" aria-hidden="true">{n}</div>
      <div><h2 id="t-partie-{n}"><span class="sr-only">Partie {n} : </span>{t}</h2>
        <div class="duree">Durée conseillée : {d} · Barème : {pts} points, soit {w} % de la note</div></div></header>
    <div class="part-body">""".format(n=p["num"], t=p["title"], d=p["duration"], pts=pts,
                                      w=fr(poids).replace(".", ","))


def figure(src, alt, cap, style=""):
    st = ' style="%s"' % style if style else ""
    return ('<figure class="fig"%s><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>'
            % (st, src, alt, cap))


def calc(s):
    return '<strong style="display:block;margin:.35rem 0">%s</strong>' % s


# ================================================================ PARTIE 1
P1 = []
P1.append("""
      <p>On étudie un <strong>kart électrique</strong> propulsé par un moteur à courant continu alimenté par une batterie.
        Ses caractéristiques sont rassemblées dans le dossier de présentation <strong>DP1</strong>.</p>
      <div class="data"><p class="data-title">Données — moteur du kart</p><ul class="cols">
        <li>Type : moteur à courant continu</li><li>Puissance utile : P<sub>u</sub> = 3,8 kW</li>
        <li>Vitesse nominale : 2600 tr/min</li><li>Tension nominale : U = 48 V</li>
        <li>Rendement : η = 0,81</li></ul></div>""")

P1.append(qbar("Q1.1", ["DP1"]))
chaine_corps = (
    figure(IMG["chaine"], "Chaîne d'énergie du kart à compléter", "Chaîne d'énergie du kart électrique (document d'origine).")
    + '<div class="chain" role="group" aria-label="Chaîne d\'énergie à compléter">'
    + '<div class="chain-box" style="flex:1 1 0"><b>ALIMENTER</b>' + sol("q1_1a", "Q1.1 alimenter", "1", "Composant qui assure la fonction ALIMENTER",
          kw(["batterie", "batteries", "accumulateur", "accumulateurs", "accu", "accus"])) + "</div>"
    + '<div class="chain-arrow" aria-hidden="true"></div>'
    + '<div class="chain-box" style="flex:1 1 0"><b>DISTRIBUER</b>' + sol("q1_1b", "Q1.1 distribuer", "1", "Composant qui assure la fonction DISTRIBUER",
          {"type": "kw", "any": [[["hacheur", "hacheurs", "variateur", "variateurs"]],
                                 [["convertisseur"], ["continu", "continue", "dc"]]]}) + "</div>"
    + '<div class="chain-arrow" aria-hidden="true"></div>'
    + '<div class="chain-box" style="flex:1 1 0"><b>CONVERTIR</b>' + sol("q1_1c", "Q1.1 convertir", "1", "Composant qui assure la fonction CONVERTIR",
          kw(["moteur", "moteurs", "machine"])) + "</div>"
    + '<div class="chain-arrow" aria-hidden="true"></div>'
    + '<div class="chain-box" style="flex:1 1 0"><b>TRANSMETTRE</b><span>Pignon-chaîne</span></div>'
    + "</div>")
P1.append(fast("q1_1", "Q1.1",
    "À partir de tes connaissances, complète la chaîne d'énergie du kart électrique : nomme le composant qui assure chaque fonction.",
    "Un nom de composant par case. La fonction TRANSMETTRE est déjà renseignée (pignon-chaîne).",
    chaine_corps,
    "ALIMENTER : batterie · DISTRIBUER : hacheur (variateur) · CONVERTIR : moteur à courant continu",
    """<p>On suit le trajet de l'énergie, de la source jusqu'aux roues :</p><ul>
      <li><strong>ALIMENTER → la batterie</strong> : elle stocke l'énergie et fournit une tension continue de 48 V.</li>
      <li><strong>DISTRIBUER → le hacheur</strong> (variateur) : il dose l'énergie envoyée au moteur ; c'est lui qui règle la vitesse du kart.</li>
      <li><strong>CONVERTIR → le moteur à courant continu</strong> : il transforme l'énergie électrique en énergie mécanique de rotation.</li>
      <li><strong>TRANSMETTRE → le pignon-chaîne</strong> (donné) : il adapte le couple et la vitesse jusqu'aux roues.</li></ul>"""))

P1.append(qbar("Q1.2 et Q1.3", ["DP1"]))
P1.append(q("q1_2", "Q1.2", "1", "Calcule la puissance électrique absorbée par le moteur à pleine charge.", H_CENT,
    num(4691.36, 0.006, U_W, [{"value": 4.69, "absTol": 0.006, "unit": U_KW, "strictUnit": True}]),
    "P<sub>a</sub> = 4691,36 W (soit 4,69 kW)",
    """<p>Le rendement est le rapport de la puissance utile sur la puissance absorbée :
      η = P<sub>u</sub> / P<sub>a</sub>, donc P<sub>a</sub> = P<sub>u</sub> / η.</p>
    <p>Avec P<sub>u</sub> = 3,8 kW = 3800 W et η = 0,81 :""" + calc("P<sub>a</sub> = 3800 ÷ 0,81 = 4691,36 W") + """
    La puissance absorbée est supérieure à la puissance utile : la différence (≈ 891 W) correspond aux pertes du moteur
    (effet Joule, pertes fer, frottements).</p>"""))

P1.append(q("q1_3", "Q1.3", "1", "Calcule l'intensité du courant consommé par le moteur à pleine charge.", H_CENT,
    num(97.74, 0.016, U_A), "I = 97,74 A",
    """<p>En courant continu, la puissance s'écrit P = U × I, donc I = P<sub>a</sub> ÷ U.</p>
    <p>C'est bien la puissance <em>absorbée</em> qu'il faut utiliser, car c'est elle qui est prélevée sur la batterie, sous 48 V :"""
    + calc("I = 4691,36 ÷ 48 = 97,74 A") + """Ce courant très élevé justifie les câbles de forte section et le fusible de
    forte valeur montés sur le kart.</p><p class="small">Une valeur intermédiaire arrondie (4691 W → 97,73 A) est acceptée.</p>"""))

P1.append(qbar("Q1.4 et Q1.5", ["DP1"]))
P1.append(q("q1_4", "Q1.4", "1", "De quelle grandeur électrique dépend la vitesse de rotation d'un moteur à courant continu ?",
    "Réponse courte en toutes lettres.",
    kw(["tension", "tensions", "u", "voltage"]),
    "de la tension d'alimentation (sa valeur moyenne), à laquelle elle est proportionnelle",
    """<p>Pour un moteur à courant continu à excitation constante, la force électromotrice est proportionnelle à la
    vitesse : E = k × n ; en négligeant la chute de tension dans l'induit, U ≈ E.</p>
    <p>La vitesse de rotation est donc <strong>proportionnelle à la tension d'alimentation</strong> (plus précisément à la
    valeur moyenne de la tension appliquée à l'induit). Pour faire varier la vitesse du kart, il suffit de faire varier
    cette tension.</p>"""))

tab = ('<div style="overflow-x:auto"><table class="t" style="min-width:520px;table-layout:fixed">'
       '<tr><th scope="row">Tension (V)</th><td>0</td><td>12</td><td>24</td><td>36</td><td>48</td></tr>'
       '<tr><th scope="row">Vitesse (tr/min)</th><td>0</td>'
       '<td>' + sol("q1_5a", "Q1.5 (12 V)", "1", "Vitesse pour 12 V, en tr/min", num(650, 0.5)) + '</td>'
       '<td>' + sol("q1_5b", "Q1.5 (24 V)", "1", "Vitesse pour 24 V, en tr/min", num(1300, 0.5)) + '</td>'
       '<td>' + sol("q1_5c", "Q1.5 (36 V)", "1", "Vitesse pour 36 V, en tr/min", num(1950, 0.5)) + '</td>'
       '<td>2600</td></tr></table></div>')
P1.append(fast("q1_5", "Q1.5",
    "Complète le tableau : pour chaque tension d'alimentation, donne la vitesse de rotation du moteur.",
    "Valeurs entières, exprimées en tr/min comme l'indique le tableau. Les points 0 V et 48 V (point nominal) sont donnés.",
    tab, "12 V → 650 tr/min · 24 V → 1300 tr/min · 36 V → 1950 tr/min",
    """<p>On utilise la proportionnalité vitesse ↔ tension établie en Q1.4. Le point de référence est le point nominal :
    <strong>48 V → 2600 tr/min</strong>, soit 2600 ÷ 48 ≈ 54,17 tr/min par volt.</p><ul>
      <li>12 V → 2600 × 12 / 48 = <strong>650 tr/min</strong> (le quart de 48 V)</li>
      <li>24 V → 2600 × 24 / 48 = <strong>1300 tr/min</strong> (la moitié)</li>
      <li>36 V → 2600 × 36 / 48 = <strong>1950 tr/min</strong> (les trois quarts)</li></ul>"""))

# ================================================================ PARTIE 2
P2 = []
P2.append("""
      <p>Pour faire varier la tension appliquée au moteur, on utilise un convertisseur qui modifie la
        <strong>valeur moyenne</strong> d'une tension continue : le <strong>hacheur</strong> (document <strong>DT1</strong>).
        Alimenté sous 48 V par la batterie, il délivre une tension découpée, visualisée à l'oscilloscope pour quatre réglages.</p>
      <div class="data"><p class="data-title">Données</p><ul>
        <li>Réglages de l'oscilloscope : 1 carreau = 8 V verticalement ; 1 carreau = 0,01 s horizontalement.</li>
        <li>Rapport cyclique : α = durée à l'état haut ÷ période.</li>
        <li>Tension moyenne en sortie du hacheur : U<sub>moy</sub> = α × 48.</li>
        <li>Vitesse du moteur : proportionnelle à U<sub>moy</sub> (2600 tr/min sous 48 V).</li></ul></div>""")

REGLAGES = [
    # (n°, image, carreaux haut, alpha, Umoy, vitesse, commentaire)
    (1, "r1", "1", 0.2, 9.6, 520, ""),
    (2, "r2", "2", 0.4, 19.2, 1040, "<p>La période (5 carreaux) est inchangée : le hacheur garde la même fréquence, seule la largeur de l'impulsion change.</p>"),
    (3, "r3", "2,5", 0.5, 24, 1300, "<p>L'état haut et l'état bas durent autant : le signal est symétrique. On retrouve la valeur du tableau Q1.5 pour 24 V : le moteur tourne à la moitié de sa vitesse nominale.</p>"),
    (4, "r4", "4", 0.8, 38.4, 2080, "<p>Bilan des quatre réglages : plus l'impulsion est large, plus la tension moyenne est grande et plus le kart va vite. Le hacheur ne « perd » quasiment pas d'énergie : il découpe la tension au lieu de la freiner dans une résistance.</p>"),
]


def frn(x):
    s = ("%g" % x).replace(".", ",")
    return s


for k, (n, im, haut, a, um, vit, com) in enumerate(REGLAGES):
    i0 = 3 * k + 1
    la, lu, lv = "Q2.%d" % i0, "Q2.%d" % (i0 + 1), "Q2.%d" % (i0 + 2)
    P2.append('<h4 class="sub">Réglage n°%d</h4>' % n)
    P2.append(figure(IMG[im], "Oscillogramme du réglage n°%d" % n,
                     "Réglage n°%d — 1 carreau = 8 V verticalement et 0,01 s horizontalement." % n,
                     "max-width:420px"))
    P2.append(qbar("%s à %s" % (la, lv), ["DT1"]))
    P2.append(q("q2_%d" % i0, la, "2", "Réglage n°%d : détermine le rapport cyclique α." % n, H_ALPHA,
        num(a, 0.006), "α = %s (soit %d %%)" % (frn(a), round(a * 100)),
        "<p>La tension vaut 48 V (6 carreaux × 8 V) pendant <strong>%s carreau%s</strong> sur une période de "
        "<strong>5 carreaux</strong> (T = 5 × 0,01 = 0,05 s).</p>" % (haut, "x" if haut not in ("1",) else "")
        + calc("α = %s ÷ 5 = %s → %d %%" % (haut, frn(a), round(a * 100)))))
    P2.append(q("q2_%d" % (i0 + 1), lu, "2", "Réglage n°%d : calcule la tension moyenne U<sub>moy</sub> en sortie du hacheur." % n,
        H_CENT, num(um, 0.006, U_V), "U<sub>moy</sub> = %s V" % frn(um),
        "<p>Un signal qui vaut 48 V pendant une fraction α de la période et 0 V le reste a pour valeur moyenne :</p>"
        + calc("U<sub>moy</sub> = α × 48 = %s × 48 = %s V" % (frn(a), frn(um)))))
    P2.append(q("q2_%d" % (i0 + 2), lv, "2", "Réglage n°%d : calcule la vitesse de rotation du moteur." % n,
        H_ENTIER, num(vit, 0.5, U_TRMIN), "n = %d tr/min" % vit,
        "<p>La vitesse est proportionnelle à la tension moyenne (2600 tr/min sous 48 V) :</p>"
        + calc("n = 2600 × %s / 48 = %d tr/min" % (frn(um), vit)) + com))

# ================================================================ PARTIE 3
P3 = []
P3.append("""
      <p>On réalise maintenant une alimentation autonome en courant alternatif à partir d'une <strong>batterie</strong> et
        d'un <strong>onduleur</strong>. Les mesures relevées sur l'installation sont données dans le document <strong>DT2</strong>.</p>
      <div class="data"><p class="data-title">Mesures sur l'installation</p><ul>
        <li>Tension d'entrée de l'onduleur (sortie batterie) : U<sub>B</sub> = 11 V</li>
        <li>Courant en entrée de l'onduleur : I<sub>B</sub> = 10,25 A</li>
        <li>Tension en sortie de l'onduleur : U<sub>U</sub> = 220 V (valeur efficace)</li>
        <li>Courant en sortie de l'onduleur : I<sub>U</sub> = 0,6 A</li>
        <li>Facteur de puissance en sortie : cos φ = 0,76</li></ul></div>""")

P3.append(qbar("Q3.1 et Q3.2", []))
P3.append(q("q3_1", "Q3.1", "3", "Quel est le rôle du convertisseur appelé « onduleur » ?",
    "Réponse courte : précise la nature de la tension en entrée et en sortie.",
    kw(["continu", "continue", "continus", "continues", "dc"], ["alternatif", "alternative", "alternatifs", "alternatives", "ac"]),
    "convertir une tension continue en tension alternative",
    """<p>Une batterie ne fournit que du <strong>continu</strong>, alors que la plupart des appareils du commerce
    fonctionnent en <strong>alternatif</strong> (230 V / 50 Hz). Il faut un convertisseur entre les deux.</p>
    <p>L'onduleur <strong>convertit une tension continue en tension alternative</strong>, en général sinusoïdale, de
    fréquence et d'amplitude définies. C'est le convertisseur inverse du redresseur.</p>
    <p class="small">La réponse est acceptée si elle contient les deux idées : « continu » et « alternatif ».</p>"""))

schema_corps = (
    figure(IMG["schema"], "Schéma : batterie, onduleur, utilisation", "Schéma de principe de l'alimentation.")
    + '<div style="display:flex;gap:18px;flex-wrap:wrap">'
    + '<div style="flex:1 1 240px"><p style="margin:0 0 4px"><b>Batterie → onduleur</b> : tension…</p>'
    + sol("q3_2a", "Q3.2 (entrée)", "3", "Type de tension entre la batterie et l'onduleur",
          kw(["continu", "continue", "dc"], forbid=["alternatif", "alternative", "ac"])) + "</div>"
    + '<div style="flex:1 1 240px"><p style="margin:0 0 4px"><b>Onduleur → utilisation</b> : tension…</p>'
    + sol("q3_2b", "Q3.2 (sortie)", "3", "Type de tension entre l'onduleur et l'utilisation",
          kw(["alternatif", "alternative", "ac", "sinusoidale", "sinusoidal"], forbid=["continu", "continue", "dc"])) + "</div>"
    + "</div>")
P3.append(fast("q3_2", "Q3.2",
    "Complète le schéma de principe : indique le type de tension présent avant et après l'onduleur.",
    "Un mot par case.", schema_corps,
    "batterie → onduleur : continue · onduleur → utilisation : alternative",
    """<p>On lit le schéma de gauche à droite en se demandant, à chaque flèche, quelle tension circule :</p><ul>
      <li><strong>Batterie → onduleur : tension continue</strong> (DC) ; c'est la nature même d'une batterie, ici 11 V.</li>
      <li><strong>Onduleur → utilisation : tension alternative</strong> (AC) ; c'est le résultat de la conversion, ici 220 V, 50 Hz.</li></ul>"""))

P3.append(qbar("Q3.3 à Q3.5", ["DT2"]))
P3.append(q("q3_3", "Q3.3", "3", "Calcule la puissance électrique fournie par la batterie (puissance absorbée par l'onduleur).",
    H_CENT, num(112.75, 0.006, U_W), "P<sub>B</sub> = 112,75 W",
    "<p>Côté batterie, on est en <strong>courant continu</strong> : la puissance est le produit de la tension par "
    "l'intensité, sans facteur de puissance.</p>" + calc("P<sub>B</sub> = U<sub>B</sub> × I<sub>B</sub> = 11 × 10,25 = 112,75 W")))
P3.append(q("q3_4", "Q3.4", "3", "Calcule la puissance active fournie par l'onduleur à l'utilisation.",
    H_CENT, num(100.32, 0.006, U_W), "P<sub>U</sub> = 100,32 W",
    "<p>Côté sortie, on est en <strong>alternatif monophasé</strong> : le produit U × I donne la puissance "
    "<em>apparente</em> (en VA). Pour obtenir la puissance <em>active</em> (en W), on multiplie par le facteur de puissance :</p>"
    + calc("P<sub>U</sub> = U<sub>U</sub> × I<sub>U</sub> × cos φ = 220 × 0,6 × 0,76 = 100,32 W")
    + "<p class=\"small\">Sans le cos φ, on trouverait 132 VA : c'est la puissance apparente, pas la puissance active.</p>"))
P3.append(q("q3_5", "Q3.5", "3", "Calcule le rendement de l'onduleur.",
    "Nombre sans unité, arrondi au centième (exemple : 0,75).", num(0.89, 0.006), "η = 0,89 (soit 89 %)",
    "<p>Le rendement d'un convertisseur est le rapport de ce qu'il restitue sur ce qu'il absorbe :</p>"
    + calc("η = P<sub>U</sub> / P<sub>B</sub> = 100,32 ÷ 112,75 = 0,89")
    + "<p>Les 11 % restants (≈ 12,4 W) sont dissipés en chaleur dans l'électronique de l'onduleur. Un rendement est "
      "toujours inférieur à 1 : c'est un bon moyen de vérifier qu'on n'a pas inversé numérateur et dénominateur.</p>"))

# ================================================================ PARTIE 4
P4 = []
P4.append("""
      <p>On place un oscilloscope en sortie de l'onduleur, du côté utilisation, et on relève la tension u(t)
        (document <strong>DT3</strong>).</p>
      <div class="data"><p class="data-title">Réglages de l'oscilloscope</p><ul>
        <li>Sensibilité verticale : 1 carreau = 100 V</li><li>Base de temps : 1 carreau = 5 ms</li></ul></div>""")
P4.append(figure(IMG["sinus"], "Tension sinusoïdale relevée en sortie d'onduleur",
                 "Tension u(t) en sortie de l'onduleur — 1 carreau = 100 V et 5 ms.", "max-width:560px"))
P4.append(qbar("Q4.1 et Q4.2", ["DT3"]))
P4.append(q("q4_1", "Q4.1", "4", "Mesure la valeur maximale U<sub>max</sub> de la tension.",
    "Lecture graphique : précision attendue ± 10 V. " + H_UNITE,
    num(305, 10.5, U_V), "U<sub>max</sub> ≈ 310 V (un peu plus de 3 carreaux) ; toute lecture entre 295 V et 315 V est acceptée",
    """<p>On mesure l'écart entre l'axe horizontal (0 V) et le sommet de la sinusoïde : <strong>un peu plus de 3 carreaux</strong>
    (environ 3,1). On multiplie par la sensibilité verticale :</p>""" + calc("U<sub>max</sub> ≈ 3,1 × 100 ≈ 310 V") + """
    <p>Ce résultat est cohérent avec les 220 V efficaces annoncés : 220 × √2 ≈ 311 V. Une lecture arrondie à 3 carreaux
    (300 V) est également acceptée.</p>
    <p class="small">Attention à ne pas lire l'amplitude crête à crête (≈ 6,2 carreaux, soit 620 V) : la valeur maximale se
    compte à partir de l'axe des temps.</p>"""))
P4.append(q("q4_2", "Q4.2", "4", "Calcule la valeur efficace U<sub>eff</sub> de la tension.",
    "Calcule à partir de ta lecture de Q4.1, arrondi au centième : la tolérance suit celle de la lecture (± 7 V). " + H_UNITE,
    num(215.67, 7.5, U_V), "U<sub>eff</sub> = U<sub>max</sub> / √2 ≈ 219,20 V pour 310 V (212,13 V pour 300 V)",
    "<p>Pour une tension <strong>sinusoïdale</strong>, la valeur efficace se déduit de la valeur maximale :</p>"
    + calc("U<sub>eff</sub> = U<sub>max</sub> / √2 = 310 ÷ 1,414 ≈ 219,20 V")
    + "<p>On retrouve les 220 V mesurés au voltmètre en sortie d'onduleur (DT2). Avec une lecture de 300 V, on obtient "
      "212,13 V : l'écart vient de la précision de lecture sur l'écran.</p>"))
P4.append(qbar("Q4.3 et Q4.4", ["DT3"]))
P4.append(q("q4_3", "Q4.3", "4", "Mesure la période T de la tension.",
    "Lecture graphique : précision attendue ± 0,5 ms. " + H_UNITE,
    num(20, 0.6, U_MS, [{"value": 0.02, "absTol": 0.0006, "unit": U_S, "strictUnit": True}]),
    "T = 20 ms (0,02 s)",
    "<p>La période est la durée d'un motif complet, par exemple d'un sommet au sommet suivant : <strong>4 carreaux</strong>. "
    "On multiplie par la base de temps :</p>" + calc("T = 4 × 5 = 20 ms = 0,02 s")))
P4.append(q("q4_4", "Q4.4", "4", "Calcule la fréquence f de la tension.",
    "Calcule à partir de ta lecture de Q4.3, arrondi au centième. " + H_UNITE,
    num(50, 1.3, U_HZ), "f = 50 Hz",
    "<p>La fréquence est l'inverse de la période, la période étant exprimée <strong>en secondes</strong> :</p>"
    + calc("f = 1 / T = 1 ÷ 0,02 = 50 Hz")
    + "<p>On retrouve la fréquence du réseau électrique : l'onduleur peut alimenter des appareils domestiques classiques.</p>"))


# ================================================================ ASSEMBLAGE
def pts_part(n):
    return sum(c["pts"] for c in QCFG.values() if c["part"] == n)


PARTS_JS = [dict(p, points=pts_part(p["num"])) for p in PARTS]
CORPS = [P1, P2, P3, P4]

parties_html = ""
for p, corps in zip(PARTS_JS, CORPS):
    parties_html += part_head(p, p["points"]) + "\n" + "\n".join(corps) + "\n    </div>\n  </section>\n"

NB_ITEMS = len(QCFG)
TITRE = "Chaîne d'énergie électrique : du kart à l'onduleur"

DOCS = [
    ("DP1", "Le kart électrique", "Dossier présentation", False,
     '<img class="doc-img" src="%s" alt="Kart électrique">'
     '<img class="doc-img" src="%s" alt="Moteur à courant continu du kart" style="width:calc(var(--z) * 45%%)">'
     '<div class="doc-text"><h3>Caractéristiques du moteur</h3><ul>'
     '<li>Type : moteur à courant continu (DC)</li><li>Puissance utile : 3,8 kW</li>'
     '<li>Vitesse nominale : 2600 tr/min</li><li>Tension nominale : 48 V</li><li>Rendement : 0,81</li></ul>'
     '<p>Le moteur est alimenté par une batterie de 48 V à travers un hacheur ; il entraîne l\'essieu arrière par un pignon et une chaîne.</p></div>'
     % (IMG["kart"], IMG["moteur"])),
    ("DT1", "Le hacheur", "Dossier technique", True,
     '<img class="doc-img" src="%s" alt="Hacheur : entrée 48 V, sortie U réglable" style="width:calc(var(--z) * 60%%)">'
     '<div class="doc-text"><h3>Principe</h3><p>Le hacheur, alimenté sous 48 V par la batterie, découpe cette tension : '
     'sa sortie vaut 48 V pendant une durée réglable, puis 0 V jusqu\'à la fin de la période.</p>'
     '<ul><li>Rapport cyclique : α = durée à l\'état haut ÷ période</li><li>Tension moyenne : U<sub>moy</sub> = α × 48</li></ul>'
     '<h3>Réglages de l\'oscilloscope</h3><ul><li>1 carreau = 8 V verticalement</li><li>1 carreau = 0,01 s horizontalement</li></ul></div>'
     % IMG["hacheur"]),
    ("DT2", "Mesures sur l'onduleur", "Dossier technique", True,
     '<div class="doc-text"><h3>Mesures relevées sur l\'installation</h3><table class="t">'
     '<tr><th>Grandeur</th><th>Symbole</th><th>Valeur</th></tr>'
     '<tr><td>Tension d\'entrée de l\'onduleur (sortie batterie)</td><td>U<sub>B</sub></td><td>11 V</td></tr>'
     '<tr><td>Courant en entrée de l\'onduleur</td><td>I<sub>B</sub></td><td>10,25 A</td></tr>'
     '<tr><td>Tension en sortie de l\'onduleur (efficace)</td><td>U<sub>U</sub></td><td>220 V</td></tr>'
     '<tr><td>Courant en sortie de l\'onduleur</td><td>I<sub>U</sub></td><td>0,6 A</td></tr>'
     '<tr><td>Facteur de puissance en sortie</td><td>cos φ</td><td>0,76</td></tr></table></div>'),
    ("DT3", "Tension en sortie de l'onduleur", "Dossier technique", True,
     '<img class="doc-img" src="%s" alt="Tension sinusoïdale en sortie d\'onduleur">'
     '<p class="doc-cap">Réglages : 1 carreau = 100 V verticalement ; 1 carreau = 5 ms horizontalement.</p>' % IMG["sinus"]),
]

rail = []
for i, (k, t, kind, dt, _) in enumerate(DOCS):
    if dt and i and not DOCS[i - 1][3]:
        rail.append('  <div class="grp" aria-hidden="true"></div>')
    rail.append('  <button type="button" class="tab%s" data-doc="%s" aria-selected="false" title="%s">%s</button>'
                % (" dt" if dt else "", k, t, k))
dp_tabs = "\n".join('    <button type="button" data-doc="%s" aria-selected="false">%s</button>' % (d[0], d[0]) for d in DOCS)
dp_secs = "\n".join('    <section class="doc" id="doc-%s" data-title="%s : %s" data-kind="%s">\n      %s\n    </section>'
                    % (k, k, t, kind, html) for k, t, kind, _, html in DOCS)

BODY = """<body class="no-mode">

<nav class="rail" aria-label="Dossier de présentation et dossier technique">
{rail}
</nav>

<aside id="docpanel" aria-label="Documents du sujet" aria-hidden="true">
  <div class="dp-head">
    <h3 id="dp-title">Documents</h3>
    <button type="button" id="dp-out" aria-label="Réduire">−</button><span id="dp-zoom" class="small">100 %</span>
    <button type="button" id="dp-in" aria-label="Agrandir">+</button>
    <button type="button" id="dp-fit">Ajuster</button>
    <button type="button" id="dp-close">Fermer</button>
  </div>
  <div class="dp-tabs" role="tablist" aria-label="Choisir un document">
{dp_tabs}
  </div>
  <div class="dp-body">
{dp_secs}
  </div>
</aside>

<section id="home" aria-labelledby="home-title">
  <div class="home-inner">
    <header class="home-head">
      <h1 id="home-title">{titre}</h1>
      <p class="home-sub">Un kart électrique à moteur à courant continu, piloté par un hacheur, puis une alimentation autonome
        batterie + onduleur : on suit l'énergie électrique de la source à l'utilisation, en continu puis en alternatif.
        {nb} réponses à saisir, réparties en {np} parties.</p>
    </header>
    <figure class="home-hero" style="max-width:520px;margin-left:auto;margin-right:auto">
      <img src="{hero}" alt="Kart électrique">
      <figcaption>Le kart électrique étudié : moteur à courant continu de 3,8 kW alimenté sous 48 V.</figcaption>
    </figure>
    <div class="home-facts">
      <div><b>{np} parties</b><span>du courant continu au courant alternatif</span></div>
      <div><b>{duree}</b><span>durée conseillée, qui fixe la pondération</span></div>
      <div><b>{nd} documents</b><span>DP1 et DT1 à DT3 consultables</span></div>
      <div><b>0 tracé</b><span>toutes les réponses se saisissent au clavier</span></div>
    </div>
    <h2 class="home-choose">Choisis ton mode de travail</h2>
    <div class="modes">
      <article class="mode-card">
        <div class="mc-head"><span class="mc-tag">Mode 1</span><h3>Mode entraînement</h3></div>
        <p class="mc-lead">Pour apprendre en avançant, question par question.</p>
        <ul><li>Chaque question se valide isolément ; la démarche corrigée s'affiche aussitôt.</li>
          <li>La note pondérée s'actualise en continu dans le bandeau.</li>
          <li>Les documents et le chronomètre restent disponibles, sans contrainte de temps.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="training">Commencer l'entraînement</button>
      </article>
      <article class="mode-card exam">
        <div class="mc-head"><span class="mc-tag">Mode 2</span><h3>Mode examen</h3></div>
        <p class="mc-lead">Pour se placer dans les conditions d'une évaluation.</p>
        <ul><li>Aucune correction et aucune note pendant la composition ; les réponses restent modifiables.</li>
          <li>Le chronomètre tourne, à comparer à la durée conseillée.</li>
          <li>En fin de sujet, le bouton « J'ai fini, je fais corriger ma copie » dévoile d'un coup les corrections, les notes par partie et la note globale.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="exam">Composer en mode examen</button>
      </article>
    </div>
    <p class="home-note small">Le mode se choisit une seule fois : pour en changer, recharge la page. Rien n'est enregistré sur l'ordinateur.</p>
  </div>
</section>

<main class="page">
  <section class="print-only print-summary">
    <p>Élève : <span class="print-nom"></span> | Copie imprimée le <span class="print-date"></span></p>
    <p>Mode : <span class="print-mode"></span> | Temps de rédaction : <strong class="print-time"></strong> (durée conseillée : {duree})</p>
    <p class="print-note-line">Note finale pondérée : <strong class="final-note"></strong></p>
    <p class="print-nograde">Copie non corrigée : les corrections et la note n'apparaissent qu'après la remise de la copie en mode examen.</p>
  </section>

  <header class="cartouche">
    <div class="title">
      <h1>{titre}</h1>
      <p>{nb} réponses notées (unités comprises), réparties en {np} parties pondérées par leur durée.</p></div>
    <div class="nom"><label for="nom-eleve">Nom et prénom</label><input id="nom-eleve" type="text" autocomplete="name"></div>
  </header>

  <div class="consignes">
    <p class="only-training"><strong>Mode entraînement.</strong> Réponds dans chaque champ puis clique sur « Valider » : une réponse validée est définitive et sa correction s'affiche aussitôt.</p>
    <p class="only-exam"><strong>Mode examen.</strong> Compose tout le sujet sans correction ni note : tes réponses restent modifiables jusqu'au bout. Le bouton « J'ai fini, je fais corriger ma copie », en fin de sujet, dévoile d'un coup les corrections, les notes par partie et la note globale.</p>
    <p><strong>Les unités sont notées.</strong> Pour toute question numérique, la valeur vaut la moitié des points et l'unité l'autre moitié : une valeur juste écrite sans unité, ou avec une unité fausse, ne rapporte qu'un demi-point.</p>
    <p>La virgule et le point sont acceptés indifféremment comme séparateur décimal.</p>
    <p>Le dossier de présentation (DP) et le dossier technique (DT) s'ouvrent avec les onglets sur le bord droit, ou avec les boutons des en-têtes de question.</p>
    <p><strong>Barème pondéré par la durée conseillée</strong> : chaque partie est notée sur 20, puis pèse au prorata de son temps. Le récapitulatif de fin de sujet donne le détail partie par partie.</p>
  </div>
{parties}
  <section class="recap" id="recap" aria-labelledby="t-recap">
    <header class="recap-head"><h2 id="t-recap">Récapitulatif et note finale</h2>
      <p class="small">Les questions non validées comptent comme fausses. Chaque partie est ramenée sur 20, puis pondérée par sa durée conseillée.</p></header>
    <div id="exam-submit-wrap">
      <p class="es-lead">Ta copie n'est pas encore corrigée : aucune réponse n'est verrouillée, tu peux encore revenir sur les questions.</p>
      <button type="button" class="btn btn-exam" id="exam-submit">J'ai fini, je fais corriger ma copie</button>
      <p class="es-warn" id="exam-warn" role="alert"></p>
    </div>
    <div id="recap-graded">
      <div class="recap-wrap">
        <table class="t recap-table">
          <thead><tr><th>Partie</th><th>Durée</th><th>Poids</th><th>Points</th><th>Note /20</th><th>Contribution</th></tr></thead>
          <tbody id="recap-body"></tbody>
          <tfoot><tr><th colspan="4">Note globale pondérée</th><th class="final-note"></th><th></th></tr></tfoot>
        </table>
      </div>
      <p class="final-detail small"></p>
    </div>
    <div class="recap-foot" id="recap-foot"><button type="button" class="btn btn-print">Imprimer ma copie</button>
      <span class="small no-print">L'impression reprend tes réponses, les corrections et ce récapitulatif.</span></div>
  </section>
</main>

<footer class="banner" aria-label="Suivi de la composition">
  <div class="score-block"><div class="lab">Note provisoire</div><div class="score" id="score-val">–<small>/20</small></div></div>
  <div class="exam-block"><div class="lab">Mode examen</div><div class="exam-state">Note masquée</div></div>
  <div class="timer-block"><div class="lab">Temps</div><div class="timer" id="timer-val">0:00:00</div></div>
  <div class="count" id="score-count" aria-live="polite"></div>
  <div class="spacer"></div>
  <button type="button" class="btn-docs" id="btn-docs">Documents</button>
</footer>
""".format(rail="\n".join(rail), dp_tabs=dp_tabs, dp_secs=dp_secs, titre=TITRE, nb=NB_ITEMS, np=len(PARTS),
           nd=len(DOCS), duree=duree_longue(TOTAL_MIN), hero=IMG["kart"], parties=parties_html)


# ================================================================ GABARIT
def extraire(gab):
    style = re.search(r"^<style>.*?</style>", gab, re.S | re.M).group(0)
    grading = re.search(r"<script>/\*GRADING-START\*/.*?/\*GRADING-END\*/\n</script>", gab, re.S).group(0)
    app = re.search(r"<script>\(function \(\) \{.*?\}\)\(\);\n</script>", gab, re.S).group(0)
    return style, grading, app


def configurer_app(app):
    """Points de configuration prévus par le gabarit : durée conseillée, DECOR, DR_NAMES."""
    def remplace(motif, par):
        nonlocal app
        nouv, n = re.subn(motif, par, app, count=1, flags=re.S)
        assert n == 1, motif
        app = nouv
    remplace(r"var CONSEIL_MIN = \d+;", "var CONSEIL_MIN = %d;" % TOTAL_MIN)
    # Aucun tracé dans ce sujet : pas de fond de document réponse à décorer ni à imprimer.
    remplace(r"var DECOR = \{.*?\n  \};\n", "var DECOR = {};\n")
    remplace(r"var DR_NAMES = \{.*?\n  \};\n", "var DR_NAMES = {};\n")
    return app


def main():
    with open(GABARIT, encoding="utf-8") as f:
        gab = f.read()
    style, grading, app = extraire(gab)
    app = configurer_app(app)
    cfg = ("<script>window.__PARTS__ = %s;\nwindow.__QCFG__ = %s;\nwindow.__SKCFG__ = {};</script>"
           % (json.dumps(PARTS_JS, ensure_ascii=False), json.dumps(QCFG, ensure_ascii=False)))
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Fichier généré par outils/generer.py à partir de outils/gabarit-exercice-interactif.html : ne pas éditer à la main. -->
<title>{titre} — exercice interactif</title>
<meta name="description" content="Chaîne d'énergie, puissance et rendement, moteur à courant continu, hacheur et rapport cyclique, onduleur, valeurs maximale et efficace, période et fréquence.">
{style}
</head>
{body}
<!-- CONFIGURATION DU SUJET -->
{cfg}
{grading}
{app}
</body>
</html>
""".format(titre=TITRE, style=style, body=BODY, cfg=cfg, grading=grading, app=app)
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html : %d octets, %d items notés, %d min" % (len(html.encode("utf-8")), NB_ITEMS, TOTAL_MIN))
    for p in PARTS_JS:
        print("  partie %s : %s pts, %s" % (p["num"], p["points"], p["duration"]))


if __name__ == "__main__":
    main()
