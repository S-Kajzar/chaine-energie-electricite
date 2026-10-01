# Note de livraison — Chaîne d'énergie électrique : du kart à l'onduleur

`index.html` est désormais construit sur le gabarit `outils/gabarit-exercice-interactif.html`. Le bloc `<style>` et le moteur de correction `Grading` sont repris à l'identique. Du moteur applicatif, seuls changent les points de configuration prévus par le gabarit (voir plus bas).

- **Régénérer :** `python3 outils/generer.py` (contenu dans le script, images dans `outils/images/`).
- **Tests du moteur de correction :** `node outils/tests/grading.test.js` (182 cas : juste, faux, accents, casse, virgule, unités absentes, unités voisines, formulations alternatives).
- **Tests navigateur :** `NODE_PATH=$(npm root -g) node outils/tests/navigateur.test.js`. Ils couvrent les parcours entraînement et examen, l'impression avant et après la remise, les documents, l'affichage mobile, un sujet parfait à 20/20 et l'absence d'erreur JavaScript.

## Structure retenue

| Partie | Contenu | Durée | Points | Poids |
|---|---|---|---|---|
| 1 | Kart électrique : moteur à courant continu (Q1.1 à Q1.5) | 20 min | 9 | 28,6 % |
| 2 | Faire varier la vitesse : le hacheur (Q2.1 à Q2.12) | 25 min | 12 | 35,7 % |
| 3 | Courant alternatif : l'onduleur (Q3.1 à Q3.5) | 15 min | 6 | 21,4 % |
| 4 | Analyse de la tension de sortie (Q4.1 à Q4.4) | 10 min | 4 | 14,3 % |

Le sujet compte 31 items notés, pour une durée conseillée totale de 1 h 10. Il y a quatre documents : DP1 (le kart), DT1 (le hacheur), DT2 (les mesures sur l'onduleur) et DT3 (le relevé de tension en sortie).

## Configuration du moteur applicatif (points prévus par le gabarit)

- `CONSEIL_MIN` passe de 300 à 70 : la durée conseillée de ce sujet, qui fait virer le chronomètre au jaune.
- `DECOR` et `DR_NAMES` sont vides, car le sujet ne comporte **aucun tracé**. Le bouton « Imprimer les DR » n'apparaît donc pas, et la page d'accueil annonce « 0 tracé ».

## Erreur relevée dans la version précédente et arbitrage

- **Q4.1 (valeur maximale de la tension) :** l'ancien corrigé donnait 300 V (3 carreaux). Mesuré au pixel, le sommet de la sinusoïde est à **≈ 3,1 carreaux, soit ≈ 310 V**, ce qui correspond bien aux 220 V efficaces du tableau de mesures (220 × √2 ≈ 311 V). Avec 300 V, on obtenait en Q4.2 212 V efficaces, en contradiction avec les 220 V mesurés.
  - **Arbitrage :** toute lecture entre 295 et 315 V est acceptée.
  - **Q4.2 :** toute valeur efficace entre 208 et 223 V est acceptée, la tolérance suivant celle de la lecture. Le corrigé présente 310 V / 219,20 V et cite 300 V / 212,13 V comme lecture acceptable.
- Les autres résultats ont été recalculés et sont justes : 4691,36 W ; 97,74 A ; 650 / 1300 / 1950 tr/min ; α = 0,2 / 0,4 / 0,5 / 0,8 (vérifiés au pixel sur les quatre oscillogrammes) ; 9,6 / 19,2 / 24 / 38,4 V ; 520 / 1040 / 1300 / 2080 tr/min ; 112,75 W ; 100,32 W ; η = 0,89 ; T = 20 ms ; f = 50 Hz.

## Questions renumérotées, reformulées ou découpées

- **Numérotation :** elle passe au format partie.question. L'ancienne numérotation Q1 à Q14 était irrégulière (Q4.1, Q4.2, Q5.1 à Q5.4 au milieu de numéros simples).
- **Questions groupées (une validation pour plusieurs cases) :** l'ancienne Q1 (chaîne d'énergie) devient Q1.1, l'ancienne Q4.2 (tableau des vitesses) Q1.5, l'ancienne Q7 (schéma de l'onduleur) Q3.2. Chaque case vaut 1 point.
- **Réglages du hacheur :** les quatre anciennes questions à quatre champs deviennent 12 questions Q2.1 à Q2.12, soit trois par réglage : α, U<sub>moy</sub>, n.
  - Le champ « rapport cyclique en % » est supprimé, car il fait doublon avec α. Le pourcentage reste donné dans la correction.
- **Tableau Q1.5 :** les points 0 V → 0 tr/min et 48 V → 2600 tr/min (point nominal donné par l'énoncé) sont affichés comme données. Seules les cases 12, 24 et 36 V sont à remplir.
- **Unités annoncées :** les consignes n'annoncent plus l'unité attendue (anciennes Q2 « en watts » et Q13 « en millisecondes »). Elles rappellent que l'unité vaut la moitié des points. L'unité reste indiquée dans le tableau Q1.5, où l'énoncé la donne lui-même.

## Décisions de tolérance

- **Calculs directs :** la consigne demande d'arrondir au centième, la tolérance est de ± 0,006.
- **Calculs enchaînés (Q1.3) :** la tolérance est de ± 0,016, pour accepter un arrondi intermédiaire (4691 W → 97,73 A).
- **Vitesses en tr/min :** la consigne demande d'arrondir à l'entier, la tolérance est de ± 0,5. Le calcul par le coefficient 54,17 tr/min/V donne par exemple 520,03, ce qui reste accepté.
- **Lectures graphiques :** la précision attendue est annoncée dans la consigne : ± 10 V pour Q4.1, ± 0,5 ms pour Q4.3. Pour Q4.4, la fréquence est acceptée entre 48,7 et 51,3 Hz, dans la continuité de la lecture de la période.
- **Unités alternatives acceptées :** 4,69 kW en Q1.2 et 0,02 s en Q4.3. Elles ne sont reconnues que si l'unité est écrite.
- **Rapport cyclique et rendement :** nombres sans unité, donc la valeur seule rapporte le point entier. « 20 % » n'est pas accepté pour α = 0,2, et la consigne l'annonce (« nombre compris entre 0 et 1 »).
- **Q3.1 (rôle de l'onduleur) :** la réponse doit contenir « continu » et « alternatif ».
  - Limite connue : le moteur `kw` ne contrôle pas l'ordre des mots, donc « convertit l'alternatif en continu » serait accepté à tort.
- **Q3.2 :** une case qui contient à la fois « continue » et « alternative » est refusée.

## Points signalés sans modification

- **DT2 :** la tension de sortie de l'onduleur y est notée 220 V. La valeur du réseau est aujourd'hui de 230 V ; la donnée d'origine est conservée.
- **Deux batteries différentes :** la batterie de l'onduleur (11 V) n'est pas celle du kart (48 V). Le sujet présente bien deux installations distinctes, mais l'enchaînement peut surprendre les élèves.
