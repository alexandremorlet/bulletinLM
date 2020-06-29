"""
Ce script génère, à partir de la BDD Sacoche, un fichier .JSON contenant
toutes les informations nécessaires pour éditer le bulletin des élèves
Tables utilisées: [A COMPLETER]
TODO: Gestion des coeffs, appréciations (manque "décision"), absences
      Faire apparaître explicitement tous les thèmes, même en l'abs d'éval
        (géré dans la partie graphique selon le référentiel
        choisi par notre équipe ?)
      Gestion des cas particuliers (que des absences, que des NE, NN, ...)
        Faire apparaître ABS, NE, NN ou une croix si on a un mélange de cas
      (Done ?) Associer à chaque prof sa matière (sacoche_jointure_user_matiere)
"""
import json
import os
import datetime
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
query = ("SELECT u.user_nom, u.user_genre, g.groupe_nom, jug.jointure_pp, u.user_id "
         "FROM sacoche_jointure_user_groupe as jug, sacoche_user as u, "
         "sacoche_groupe as g "
         "WHERE u.user_profil_sigle = 'ENS' AND jug.user_id = u.user_id "
         "AND g.groupe_id = jug.groupe_id AND g.groupe_type = 'classe'")
cursor.execute(query)
for nom, genre, classe, pp, id in cursor:
    # Gestion du genre de l'enseignant
    if genre == 'F':
        nom = 'Mme. '+nom
    elif genre == 'M':
        nom = 'M. '+nom
    else:
        pass # Non renseigné/inconnu

    # On ajoute l'enseignant à la classe
    # Format: [M/Mme X, matière, PP (0/1)]
    # On garde un espace vide pour la matière (TODO)
    # Solution temp: matière remplie à partir des appréciations
    resultats[classe]['profs'][id]={'nom': nom, 'matiere': [], 'pp': bool(pp)}

# with open('temp.json', 'w') as json_file:
#     json.dump(resultats, json_file)
# exit()

###########################
#   Notes et  moyennes   #
###########################

def periode_classe(classe):
    ## On récupère, pour la classe, les dates et noms des périodes
    query = ("SELECT p.periode_nom, jgp.jointure_date_debut, jgp.jointure_date_fin "
             "FROM sacoche_jointure_groupe_periode as jgp, "
             "sacoche_groupe as g, sacoche_periode as p "
             "WHERE p.periode_id = jgp.periode_id "
             "AND jgp.groupe_id = g.groupe_id AND g.groupe_nom = '%s'"%classe)
    cursor.execute(query)

    periodes = nested_dict()
    for p, debut, fin in cursor:
        # conversion des dates de str à datetime.date
        # periodes[periode]['debut'] = datetime.datetime.strptime(debut, '%Y-%m-%d')
        # periodes[periode]['fin'] = datetime.datetime.strptime(fin, '%Y-%m-%d')
        periodes[p]['debut'] = debut
        periodes[p]['fin'] = fin

    return periodes

def periode_note(periodes, date):
    """
    On a besoin d'associer une période à chaque note.
    On reçoit de la boucle principale un dictionnaire (periodes) contenant les
    dates et noms des différentes périodes, qu'on utilise pour comparer à date.
    On renvoit la str periode qui contient le nom de la période.
    """

    periode = 0 # normalement jamais zéro !

    for p in periodes:
        if periodes[p]['debut'] <= date <= periodes[p]['fin']:
            periode = p
            break

    return periode


### Fonction calc_moyenne
# on attend de recevoir le dictionnaire resultat_eleve[matière][theme]
# qui est complété dans la grande boucle qui parse toutes les notes saisies
def calc_moyenne(notes, periode, matiere, theme):
    # A partir du dict notes[matiere][theme][periode] = (note1, note2, ...)
    # on renvoit la moyenne des notes

    moyenne = 0
    nb_notes = 0
    for note in notes[matiere][theme][periode]:
        if note.isdigit(): # Ne comptent dans la moyenne que les nombres 1-4
                           # et pas les AB, NE, NN, ...
            moyenne += int(note)
            nb_notes += 1

            # Une fois toutes les notes lues, on peut calculer la moyenne
            try:
                moyenne = moyenne/nb_notes
            except ZeroDivisionError as err:
                moyenne = False
    return moyenne

### Enregistrement des évaluations pour chaque élève
for classe in resultats:

    # On récupère les dates de périodes pour cette classe
    p_dict = periode_classe(classe)

    # On récupère les notes de chaque élève
    for eleve_id in resultats[classe]:
        # L'entrée du dico resultats[classe] concerne-t-elle un élève ?
        if isinstance(eleve_id, str): # dans resultats[classe], type(key) est int pour eleve_id,
                                      # et str pour tout le reste (prof, PP, appréciations, ...)
            continue

        query = ("SELECT rt.theme_nom, m.matiere_nom, s.saisie_note, "
                "s.saisie_date " # on prend aussi la date pour les moyennes trimestrielles
                "FROM sacoche_saisie AS s, sacoche_referentiel_item AS ri, "
                "sacoche_referentiel_theme as rt, sacoche_referentiel_domaine as rd, "
                "sacoche_matiere as m "
                "WHERE s.eleve_id=%d " # filtre par élève
                "AND ri.item_id = s.item_id AND rt.theme_id = ri.theme_id " # filtre par thème (ts items d'un thème)
                "AND rd.domaine_id = rt.domaine_id AND m.matiere_id = rd.matiere_id "%eleve_id) # nom matiere

        cursor.execute(query)

        # resultat_eleve = temp nested dict car on peut pas calculer les moyennes à la volée
        # on doit d'abord les regrouper par période
        resultat_eleve = nested_dict()
        ### resultat_eleve[nom_matiere][nom_thème] = [(note1, période1), (note2,période2), ...]
        for theme_nom, domaine_nom, note, date in cursor:
            # A quelle période appartient la date ?
            periode = periode_note(p_dict,date)

            # On ajoute l'entrée au dict
            try:
                resultat_eleve[domaine_nom][theme_nom][periode].append(note)
            except AttributeError as err:
                resultat_eleve[domaine_nom][theme_nom][periode] = []
                resultat_eleve[domaine_nom][theme_nom][periode].append(note)


        # A ce stade, resultat_eleve contient le détail des notes
        # On veut regrouper, selon periode/matiere/theme, les moyennes
        for periode in p_dict:
            for matiere in resultat_eleve:
                for theme in resultat_eleve[matiere]:
                    resultats[classe][eleve_id][periode]['moyennes'][matiere][theme] = calc_moyenne(resultat_eleve, periode, matiere, theme)



#############################
#  Appréciations (classes)  #
#############################
# On collecte toutes les appréciations, triées par periode
# On associe également chaque prof à sa matière (ou ses matières)

# Attention: la table officiel_saisie contient des ID de groupe et de classe dans
# la même colonne, il faut être vigilant

# rubrique_id est associable à matiere_id
# prof_id = 0 dans les row qui stockent la moyenne de la classe (telle que calc par Sacoche)
for classe in resultats:
    query = ("SELECT p.periode_nom, os.saisie_appreciation, "
             "m.matiere_nom, os.prof_id "
             "FROM sacoche_officiel_saisie as os, sacoche_groupe as g, "
             "sacoche_matiere as m, sacoche_periode as p "
             "WHERE p.periode_id = os.periode_id AND os.saisie_type = 'classe' AND os.eleve_ou_classe_id = g.groupe_id "
             "AND g.groupe_nom = '%s' "
             "AND m.matiere_id = os.rubrique_id AND os.prof_id NOT LIKE 0"%classe)
    cursor.execute(query)
    for periode, appr, matiere, prof_id in cursor:
        resultats[classe]['appreciations'][periode][matiere] = appr

        # On en profite pour remplir la matière de chaque prof sauf cas particuliers
        # d'abord c'est peut-être déjà écrit (très probable)
        if matiere in resultats[classe]['profs'][prof_id]['matiere']:
            continue
        # ensuite deux cas: soit ce prof n'a qu'1 matière (cas simple)
        # soit il en a plusieurs (PC+SL, HG+EMC), donc il faut initier une liste
        else:
            resultats[classe]['profs'][prof_id]['matiere'].append(matiere)


##############################
#   Appréciations (élèves)   #
##############################
# On collecte toutes les appréciations, triées par periode
# Attention: la table officiel_saisie contient des ID de groupe et de classe dans
# la même colonne, il faut être vigilant

# rubrique_id est associable à matiere_id
# prof_id = 0 dans les row qui stockent la moyenne de la classe (telle que calc par Sacoche)
for classe in resultats:
    query = ("SELECT p.periode_nom, os.saisie_appreciation, os.eleve_ou_classe_id, "
             "m.matiere_nom  "
             "FROM sacoche_officiel_saisie as os, sacoche_groupe as g, "
             "sacoche_matiere as m, sacoche_periode as p, sacoche_user as u "
             "WHERE p.periode_id = os.periode_id " # pour p.periode_nom
             "AND os.saisie_type = 'eleve' " # appréciations des élèves, pas des classes
             "AND u.user_id = os.eleve_ou_classe_id " # lignes suivantes: trouver la classe (groupe_nom)
             "AND g.groupe_id = u.eleve_classe_id "
             "AND g.groupe_nom = '%s' "
             "AND m.matiere_id = os.rubrique_id AND os.prof_id NOT LIKE 0"%classe) # nom matière
    cursor.execute(query)

    for periode, appr, eleve, matiere in cursor:
        resultats[classe][eleve][periode]['appreciations'][matiere] = appr

    ### Mentions du conseil de classe (encouragements, félicitations, avertissement ...)
    # Une seule mention peut être rentrée dans l'interface (donc AT+AC = un élément).
    query = ("SELECT p.periode_nom, od.decision_contenu, ojd.user_id "
             "FROM sacoche_periode as p, sacoche_officiel_decision as od, "
             "sacoche_officiel_jointure_decision as ojd "
             "WHERE p.periode_id = ojd.periode_id " # Filtre période
             "AND od.decision_id = ojd.decision_mention") # Filtre décision contenu
    cursor.execute(query)

    for periode, mention, eleve in cursor:
        resultats[classe][eleve][periode]['mention'] = mention


    ### Décisions du conseil de classe (passage, redoublement, ...)
    query = ("SELECT p.periode_nom, od.decision_contenu, ojd.user_id "
             "FROM sacoche_periode as p, sacoche_officiel_decision as od, "
             "sacoche_officiel_jointure_decision as ojd "
             "WHERE p.periode_id = ojd.periode_id " # Filtre période
             "AND od.decision_id = ojd.decision_orientation") # Filtre décision contenu
    cursor.execute(query)

    for periode, orientation, eleve in cursor:
        resultats[classe][eleve][periode]['orientation'] = orientation

with open('temp.json', 'w') as json_file:
    json.dump(resultats['Classe test'], json_file)
