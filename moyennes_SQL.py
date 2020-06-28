"""
Ce script génère, à partir de la BDD Sacoche, un fichier .JSON contenant
toutes les informations nécessaires pour éditer le bulletin des élèves
Tables utilisées: [A COMPLETER]
TODO: Gestion des coeffs, appréciations (manque "décision"), absences
      Gestion des périodes (trimestres)
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

def periode_note(classe, date):
    """
    On a besoin d'associer une période à chaque note. Pour une classe donnée,
    les dates de périodes sont définies dans jointure_groupe_periode, les noms
    de périodes dans periode et les liens id/nom groupe sont dans groupe
    """
    periode = False
    ## On récupère, pour la classe, les dates et ID des périodes
    query = ("SELECT p.periode_nom, jgp.jointure_date_debut, jgp.jointure_date_fin "
             "FROM sacoche_jointure_groupe_periode as jgp, "
             "sacoche_groupe as g, sacoche_periode as p "
             "WHERE p.periode_id = jgp.periode_id "
             "AND jgp.groupe_id = g.groupe_id AND g.groupe_nom = '%s'"%classe)
    cursor.execute(query)

    periodes = nested_dict()
    for p, debut, fin in cursor:
        print(p, debut, fin)
        # conversion des dates de str à datetime.date
        # periodes[periode]['debut'] = datetime.datetime.strptime(debut, '%Y-%m-%d')
        # periodes[periode]['fin'] = datetime.datetime.strptime(fin, '%Y-%m-%d')
        periodes[p]['debut'] = debut
        periodes[p]['fin'] = fin

    for p in periodes:
        if periodes[p]['debut'] <= date <= periodes[p]['fin']:
            periode = p
            break

    return periode # on renvoit le nom de la période, pas l'id !

w = periode_note('2GT 2', datetime.date(2020, 2, 1))
print(w)
exit()

### Fonction calc_moyenne
# on attend de recevoir le dictionnaire resultat_eleve[matière][theme]
# qui est complété dans la grande boucle qui parse toutes les notes saisies
def calc_moyenne(dico):
    # Les périodes sont définies, pour un groupe donné, dans jointure_groupe_periode
    # On va donc calculer la moyenne par période, par matière, par thème
    # On retourne un dico sans les notes car l'objet datetime.date ne passe
    # pas bien dans JSON visiblement.
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
        if isinstance(eleve_id, str): # dans resultats[classe], type(key) est int pour eleve_id,
                                      # et str pour tout le reste (prof, PP, appréciations, ...)
            continue
        query = ("SELECT rt.theme_nom, rd.domaine_nom, s.saisie_note, "
                "s.saisie_date " # on prend aussi la date pour les moyennes trimestrielles
                "FROM sacoche_saisie AS s, sacoche_referentiel_item AS ri, "
                "sacoche_referentiel_theme as rt, sacoche_referentiel_domaine as rd "
                "WHERE s.eleve_id=%d AND ri.item_id = s.item_id "
                "AND rt.theme_id = ri.theme_id AND rd.domaine_id = rt.domaine_id "%eleve_id)
                #"AND s.saisie_note REGEXP '^[0-9]+$' " # on enlève les AB, NE, NN, ...
                #"LIMIT 30"%eleve_id)

                # date: datetime.date(2020, 6, 27)

        # RQ: Avec tables s_ref_domaine et s_matiere, on peut avoir un accès propre
        #     au nom des matières
        cursor.execute(query)

        # On met les données de l'élève considéré dans resultat_eleve
        # dictionnaire temporaire
        resultat_eleve = nested_dict()
        ### resultat_eleve[nom_matiere][nom_thème] = [(note1, date1), (note2,date2), ...]
        for theme_nom, domaine_nom, note, date in cursor:
            try:
                resultat_eleve[domaine_nom][theme_nom]['notes'].append((note,date))
            except AttributeError as err:
                resultat_eleve[domaine_nom][theme_nom]['notes'] = []
                resultat_eleve[domaine_nom][theme_nom]['notes'].append((note,date))

        # On inclut les notes et la moyenne dans le dictionnaire global
        resultats[classe][eleve_id]['bulletin'] = calc_moyenne(resultat_eleve)


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
        print(periode, classe, appr, matiere, prof_id)
        print(resultats[classe]['profs'][prof_id]['nom'], matiere)
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
             "m.matiere_nom "
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
        print(periode, classe, eleve, appr, matiere)

        resultats[classe][eleve]['bulletin'][periode][matiere]['appreciation'] = appr


with open('temp.json', 'w') as json_file:
    json.dump(resultats, json_file)
