Ce dépôt contient les scripts utilisés par la classe à compétences du lycée Louise Michel (94) pour générer les bulletins scolaires. Les notes sont extraites de la base de données de [SACoche](https://sacoche.sesamath.net/), utilisé pour rentrer les évaluations au fur et à mesure.
Le format du bulletin est très rigide, l'équipe pédagogique ayant choisi d'évaluer les six mêmes compétences ("thème" dans la BDD SACoche).

## Maquette du bulletin
![Maquette](https://github.com/alexandremorlet/bulletinLM/raw/master/maquette.jpg "Maquette du bulletin")

## Prérequis
- Dump de la BDD de SACoche (exportée par l'administrateur)
- Python 3 (+ FPDF2)
- MySQL 8

## Scripts
- sacoche_db_parser.py: génère deux fichiers JSON (profs.json et classes.json) contenant les informations utiles à la création des bulletins.
- generateur_bulletin.py: prend les fichiers JSON pour générer le bulletin, selon les critères décidés au sein de notre équipe.

## Générer les bulletins
- Importer le dump SACoche dans une base MySQL 'sacochedb'.
- Exécuter le script sacoche_db_parser.py (options de connexion MySQL en début de script).
- Exécuter le script generateur_bulletin.py.

## Notes d'utilisation
- SACoche ne stocke pas directement le lien entre professeurs, matières et classes. C'est les appréciations qui sont utilisées pour savoir quel nom d'enseignant.e doit apparaître sur le bulletin de chaque élève. On reprend ici ce fonctionnement: un.e enseignant.e qui ne remplit pas ses appréciations n'aura pas son nom sur le bulletin.
- TODO: Gestion des options, ajout de l'adresse des parents au dos (pour enveloppe à fenêtre).
