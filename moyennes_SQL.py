"""
Script qui récupère la moyenne, pour chaque élève, pour chaque matière (domaine),
pour chaque grande compétence (thème), à partir de la base SACoche.
Tables utilisées: [A COMPLETER]
"""
import json
###########################
#    Connexion à MySQL    #
###########################
import mysql.connector

cnx = mysql.connector.connect(user='root', password='admin',
                              host='localhost',
                              database='sacochedb')
cursor = cnx.cursor()

#################################
#  Définition des nested dicts  #
#################################
from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)
# dico = nested_dict()
# une entrée de dico peut être un autre dico, une liste ou une valeur.


### On essaye de récupérer, pour un élève (ex: id_eleve = 324), toutes ses notes regroupées par thème
query= ("SELECT s.item_id, ri.item_nom, s.saisie_note "
        "FROM sacoche_saisie AS s, sacoche_user AS u, sacoche_referentiel_item AS ri "
        "WHERE s.eleve_id=98 AND ri.item_id = s.item_id "
        "AND s.saisie_note REGEXP '^[0-9]+$' " # on enlève les AB, NE, NN, ...
        "LIMIT 30")
cursor.execute(query)
for tuple in cursor:
    print(tuple)

print("###########")
# Pareil, mais cette fois on voit si on arrive à afficher le theme_id et theme_nom qui va bien
query= ("SELECT rt.theme_id, rt.theme_nom, s.saisie_note "
        "FROM sacoche_saisie AS s, sacoche_user AS u, sacoche_referentiel_item AS ri, "
        "sacoche_referentiel_theme as rt "
        "WHERE s.eleve_id=98 AND ri.item_id = s.item_id "
        "AND rt.theme_id = ri.theme_id "
        "AND s.saisie_note REGEXP '^[0-9]+$' " # on enlève les AB, NE, NN, ...
        "LIMIT 30")
cursor.execute(query)
for tuple in cursor:
    print(tuple)


print("###########")
# Pareil, mais cette fois on voit si on arrive à afficher la matière en plus
# + variable pour choisir l'élève
eleve_id = 98
query= ("SELECT rt.theme_nom, rd.domaine_nom, s.saisie_note "
        "FROM sacoche_saisie AS s, sacoche_user AS u, sacoche_referentiel_item AS ri, "
        "sacoche_referentiel_theme as rt, sacoche_referentiel_domaine as rd "
        "WHERE s.eleve_id=%d AND ri.item_id = s.item_id "
        "AND rt.theme_id = ri.theme_id AND rd.domaine_id = rt.domaine_id "
        "AND s.saisie_note REGEXP '^[0-9]+$' " # on enlève les AB, NE, NN, ...
        "LIMIT 30"%eleve_id)
cursor.execute(query)
#for tuple in cursor:
#    print(tuple)$


## On met les données dans un dictionnaire pour pouvoir les traiter
resultat_eleve = nested_dict()
### resultat_eleve[nom_matiere][nom_thème] = [note1, note2, ...]
for theme_nom, domaine_nom, note in cursor:
    try:
        resultat_eleve[domaine_nom][theme_nom]['notes'].append(note)
    except AttributeError as err:
        resultat_eleve[domaine_nom][theme_nom]['notes'] = []
        resultat_eleve[domaine_nom][theme_nom]['notes'].append(note)

print(resultat_eleve)
with open('temp.json', 'w') as json_file:
    json.dump(resultat_eleve, json_file, sort_keys=True)
