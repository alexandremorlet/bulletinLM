"""
Ce script génère, à partir de la BDD Sacoche, un fichier .JSON contenant
toutes les informations nécessaires pour éditer le bulletin des élèves
Tables utilisées: [A COMPLETER]
TODO: Gestion des coeffs, appréciations, absences
      Gestion des périodes (trimestres)
      Faire apparaître explicitement tous les thèmes, même en l'abs d'éval
        (géré dans la partie graphique selon le référentiel
        choisi par notre équipe ?)
      Gestion des cas particuliers (que des absences, que des NE, NN, ...)
        Faire apparaître ABS, NE, NN ou une croix si on a un mélange de cas
"""
import json
import os
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


###########################
#  Infos. persos. élèves  #
###########################
# Le grand dictionnaire resultats contiendra le bilan de chaque élève
# Les élèves sont regroupés par classes
# On utilise l'ID des élèves mais pas des classes (homonymes possibles que dans un cas)
# On commence donc par remplir les infos personnelles des élèves, regroupés par classes
resultats = nested_dict()

query = ("SELECT u.user_id, u.user_reference, u.user_nom, u.user_prenom, g.groupe_nom "
        "FROM sacoche_user AS u, sacoche_groupe AS g "
        "WHERE u.user_profil_sigle = 'ELV' AND g.groupe_id = u.eleve_classe_id")
cursor.execute(query)
for id, INE, nom, prenom, classe in cursor:
    resultats[classe][id]['INE'] = INE
    resultats[classe][id]['nom'] = nom
    resultats[classe][id]['prenom'] = prenom

# with open('temp.json', 'w') as json_file:
#     json.dump(resultats, json_file, sort_keys=True)
# exit()

############################
#   Equipes pédagogiques   #
############################
# Il faut, pour chaque resultats[classe], indiquer le/la PP ainsi
# que l'enseignant.e de chaque matière
# TODO: On fait la liste des profs, mais il faudrait les associer automatiquement
# à leur matière
query = ("SELECT u.user_nom, u.user_genre, g.groupe_nom, jug.jointure_pp "
         "FROM sacoche_jointure_user_groupe as jug, sacoche_user as u, "
         "sacoche_groupe as g "
         "WHERE u.user_profil_sigle = 'ENS' AND jug.user_id = u.user_id "
         "AND g.groupe_id = jug.groupe_id AND g.groupe_type = 'classe'")
cursor.execute(query)
for nom, genre, classe, pp in cursor:
    # Gestion du genre de l'enseignant
    if genre == 'F':
        nom = 'Mme. '+nom
    elif genre == 'M':
        nom = 'M. '+nom
    else:
        pass # Non renseigné/inconnu

    # On ajoute l'enseignant à la classe
    try:
        resultats[classe]['profs'].append(nom)
    except AttributeError as err:
        resultats[classe]['profs'] = []
        resultats[classe]['profs'].append(nom)

    if pp == 1:
        resultats[classe]['PP'] = nom

# with open('temp.json', 'w') as json_file:
#     json.dump(resultats, json_file)
# exit()

###########################
#   Notes et  moyennes   #
###########################

### Fonction calc_moyenne
# on attend de recevoir le dictionnaire resultat_eleve[matière][theme]
# qui est complété dans la grande boucle qui parse toutes les notes saisies
def calc_moyenne(dico):
    for matiere in dico:
        for theme in dico[matiere]:
            moyenne = 0
            nb_notes = 0
            for note in dico[matiere][theme]['notes']:
                if note.isdigit(): # Ne comptent dans la moyenne que les nombres 1-4
                    moyenne += int(note)
                    nb_notes += 1

            # Une fois toutes les notes lues, on peut calculer la moyenne
            try:
                moyenne = moyenne/nb_notes
                dico[matiere][theme]['moyenne'] = moyenne
            except ZeroDivisionError as err:
                moyenne = False
    return dico

### Enregistrement des évaluations pour chaque élève
for classe in resultats:
    for eleve_id in resultats[classe]:
        if isinstance(eleve_id, str):
            continue
        query = ("SELECT rt.theme_nom, rd.domaine_nom, s.saisie_note "
                "FROM sacoche_saisie AS s, sacoche_referentiel_item AS ri, "
                "sacoche_referentiel_theme as rt, sacoche_referentiel_domaine as rd "
                "WHERE s.eleve_id=%d AND ri.item_id = s.item_id "
                "AND rt.theme_id = ri.theme_id AND rd.domaine_id = rt.domaine_id "%eleve_id)
                #"AND s.saisie_note REGEXP '^[0-9]+$' " # on enlève les AB, NE, NN, ...
                #"LIMIT 30"%eleve_id)

        # RQ: Avec tables s_ref_domaine et s_matiere, on peut avoir un accès propre
        #     au nom des matières
        cursor.execute(query)

        # On met les données de l'élève considéré dans resultat_eleve
        # dictionnaire temporaire
        resultat_eleve = nested_dict()
        ### resultat_eleve[nom_matiere][nom_thème] = [note1, note2, ...]
        for theme_nom, domaine_nom, note in cursor:
            try:
                resultat_eleve[domaine_nom][theme_nom]['notes'].append(note)
            except AttributeError as err:
                resultat_eleve[domaine_nom][theme_nom]['notes'] = []
                resultat_eleve[domaine_nom][theme_nom]['notes'].append(note)

        # On inclut les notes et la moyenne dans le dictionnaire global
        resultats[classe][eleve_id]['bulletin'] = calc_moyenne(resultat_eleve)



with open('temp.json', 'w') as json_file:
    json.dump(resultats, json_file)
