Ce dépôt contient les scripts utilisés par la classe à compétences du lycée Louise Michel (94) pour générer les bulletins scolaires. Les notes sont extraites de la base de données de [SACoche](https://sacoche.sesamath.net/), utilisé pour rentrer les évaluations au fur et à mesure.
Le format du bulletin est très rigide, l'équipe pédagogique ayant choisi d'évaluer les six mêmes compétences ("thème" dans la BDD SACoche).

## Maquette du bulletin
![Maquette](https://github.com/alexandremorlet/bulletinLM/raw/master/maquette.jpg "Maquette du bulletin")

## Prérequis
- Dump de la BDD de SACoche (exportée par l'administrateur)
- Python 3
- MySQL 8

## Scripts
- sacoche_db_parser.py: génère un fichier .json contenant toutes les informations nécessaires pour générer le bulletin.
- generateur_bulletin.py: prend le fichier .json sorti par sacoche_db_parser.py pour générer le bulletin, selon les critères décidés au sein de notre équipe.

## Générer les bulletins
- Importer le dump SACoche dans une base MySQL 'sacochedb'.
- Exécuter le script sacoche_db_parser.py (options de connexion MySQL en début de script).
- Exécuter le script generateur_bulletin.py.
