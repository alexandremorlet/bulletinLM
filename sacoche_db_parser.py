"""
Ce script génère, à partir de la BDD Sacoche, un fichier .JSON contenant
toutes les informations nécessaires pour éditer le bulletin des élèves
TODO: On peut supprimer la boucle sur la classe dans la plupart des cas ? (cf absences)
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
# WARNING: Si l'élève n'est pas associé à un parent, on aura une erreur au moment de générer le bulletin
resultats = nested_dict()

query = ("SELECT u.user_id, u.user_reference, u.user_nom, u.user_prenom, g.groupe_nom, u.user_naissance_date, u.user_genre, jpe.parent_id "
        "FROM sacoche_user AS u, sacoche_groupe AS g, sacoche_jointure_parent_eleve as jpe "
        "WHERE u.user_profil_sigle = 'ELV' AND g.groupe_id = u.eleve_classe_id "
        "AND u.user_sortie_date > NOW() "
        "AND jpe.eleve_id = u.user_id")
cursor.execute(query)
for id, INE, nom, prenom, classe, d_n, genre, id_parent in cursor:
    resultats[classe][id]['INE'] = INE
    resultats[classe][id]['nom'] = nom
    resultats[classe][id]['prenom'] = prenom
    resultats[classe][id]['genre'] = genre
    if d_n is not None:
        resultats[classe][id]['naissance'] = str(d_n.day)+'/'+str(d_n.month)+'/'+str(d_n.year)
    else:
        resultats[classe][id]['naissance'] = ''

    try:
        resultats[classe][id]['parents'].append(id_parent)
    except AttributeError as e:
        resultats[classe][id]['parents'] = [id_parent]

############################
#   Equipes pédagogiques   #
############################
# On crée un dictionnaire de correspondances id_prof <=> nom_prof
profs_matiere = {0: ''} # l'ID 0 sert de valeur par défaut

# On init la liste des PP pour chaque classe
for c in resultats:
    resultats[c]['PP']=[]

# La (ou les) matière enseignée à chaque classe est déterminée
# à partir des appréciations et stockée par élève (voir plus loin)

query = ("SELECT u.user_nom, u.user_genre, g.groupe_nom, jug.jointure_pp, u.user_id "
         "FROM sacoche_jointure_user_groupe as jug, sacoche_user as u, "
         "sacoche_groupe as g "
         "WHERE u.user_profil_sigle IN ('ENS','EDU')  AND jug.user_id = u.user_id "
         "AND g.groupe_id = jug.groupe_id AND g.groupe_type = 'classe' "
         "AND u.user_sortie_date > NOW()")
cursor.execute(query)
for nom, genre, classe, pp, id in cursor:
    # Gestion du genre de l'enseignant
    if genre == 'F':
        nom = 'Mme. '+nom
    elif genre == 'M':
        nom = 'M. '+nom
    else:
        pass # Non renseigné/inconnu

    # On ajoute l'enseignant à la "classe"
    profs_matiere[id] = nom

    # Si PP, on l'indique dans la classe correspondance
    if pp == 1:
        resultats[classe]['PP'].append(nom)



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

def switch_notes_text(note, notes):
    # Switch/case fonction pour comptabiliser les AB, NN, NE et DI (+ NF et NR)
    # notes = list d'entiers selon [AB,NN,NE,DI]

    d={'AB':0,'NN':1,'NE':2,'DI':3, 'NF':4, 'NR':5}

    notes[d[note]] += 1

    return notes

### Fonction calc_moyenne
# on attend de recevoir le dictionnaire resultat_eleve[matière][theme]
# qui est complété dans la grande boucle qui parse toutes les notes saisies
def calc_moyenne(notes, periode, matiere, theme):
    # A partir du dict notes[matiere][theme][periode] = (note1, note2, ...)
    # on renvoit la moyenne des notes

    somme = 0
    nb_notes = 0
    moyenne = None
    notes_text = [0,0,0,0,0,0] # Valeurs textuelles plutôt que notes (nb de AB, NN, NE, DI)
    for note, coef in notes[matiere][theme][periode]:
        if note.isdigit(): # Note = int entre 1 et 4
            somme += int(note)*int(coef)
            nb_notes += int(coef)
        else: # On peut avoir AB, NN, NE, DI
            notes_text = switch_notes_text(note, notes_text)

    # Une fois toutes les notes lues, on peut calculer la moyenne
    try:
        moyenne = somme/nb_notes
        return moyenne

    except ZeroDivisionError as err: # Pas de valeur numérique à calculer


        somme = sum(notes_text) # On somme le nombre de AB+NE+NN+DI

        # 1er cas: En fait il y a juste aucune note
        if somme == 0:
            return None

        # 2ème cas: que des AB/NE/NN/DI/NF/NR
        elif notes_text[0] == somme:
            return 'Abs.'
        elif notes_text[1] == somme:
            return 'NN'
        elif notes_text[2] == somme:
            return 'NE'
        elif notes_text[3] == somme:
            return 'Disp.'
        elif notes_text[4] == somme:
            return 'NF'
        elif notes_text[5] == somme:
            return 'NR'

        # 3ème cas: On a un mélange de différentes choses, on marque NN
        return 'NN'

    return

### Enregistrement des évaluations pour chaque élève
for classe in resultats:

    # On récupère les dates de périodes pour cette classe
    p_dict = periode_classe(classe)

    # On récupère les notes de chaque élève
    for eleve_id in resultats[classe]:
        # L'entrée du dico resultats[classe] concerne-t-elle un élève ?
        if isinstance(eleve_id, str): # dans resultats[classe], type(key) est int pour eleve_id,
                                      # et str pour tout le reste (appréciations, ...)
            continue

        query = ("SELECT rt.theme_nom, m.matiere_nom, s.saisie_note, "
                "s.saisie_date, ri.item_coef " # on prend aussi la date pour les moyennes trimestrielles
                "FROM sacoche_saisie AS s, sacoche_referentiel_item AS ri, "
                "sacoche_referentiel_theme as rt, sacoche_referentiel_domaine as rd, "
                "sacoche_matiere as m, sacoche_devoir as d "
                "WHERE s.eleve_id=%d " # filtre par élève
                "AND ri.item_id = s.item_id AND rt.theme_id = ri.theme_id " # filtre par thème (ts items d'un thème)
                "AND rd.domaine_id = rt.domaine_id AND m.matiere_id = rd.matiere_id " # nom matiere
                "AND d.devoir_id = s.devoir_id AND d.devoir_diagnostic = 0 "%eleve_id) # On exclut les évaluations diagnostiques

        cursor.execute(query)

        # resultat_eleve = temp nested dict car on peut pas calculer les moyennes à la volée
        # on doit d'abord les regrouper par période
        resultat_eleve = nested_dict()
        ### resultat_eleve[nom_matiere][nom_thème] = [(note1, période1), (note2,période2), ...]
        for theme_nom, domaine_nom, note, date , coef in cursor:
            # A quelle période appartient la date ?
            periode = periode_note(p_dict,date)

            # On ajoute l'entrée au dict
            try:
                resultat_eleve[domaine_nom][theme_nom][periode].append((note,coef))
            except AttributeError as err:
                resultat_eleve[domaine_nom][theme_nom][periode] = []
                resultat_eleve[domaine_nom][theme_nom][periode].append((note,coef))


        # A ce stade, resultat_eleve contient le détail des notes
        # On veut regrouper, selon periode/matiere/theme, les moyennes
        for periode in p_dict:
            for matiere in resultat_eleve:
                for theme in resultat_eleve[matiere]:
                    resultats[classe][eleve_id][periode]['moyennes'][matiere][theme] = calc_moyenne(resultat_eleve, periode, matiere, theme)



#############################
#  Appréciations (classes)  #
#############################
# On collecte toutes les appréciations générales des classes, triées par periode

# Attention: la table officiel_saisie contient des ID de groupe et de classe dans
# la même colonne, il faut être vigilant

# rubrique_id est associable à matiere_id
# Ignorer prof_id = 0 (lignes qui stockent la moyenne de la classe (telle que calc par Sacoche))

for classe in resultats:
    query = ("SELECT p.periode_nom, os.saisie_appreciation, "
             "m.matiere_nom "
             "FROM sacoche_officiel_saisie as os, sacoche_groupe as g, "
             "sacoche_matiere as m, sacoche_periode as p "
             "WHERE p.periode_id = os.periode_id AND os.saisie_type = 'classe' "
             "AND os.eleve_ou_classe_id = g.groupe_id "
             "AND g.groupe_nom = '%s' "
             "AND m.matiere_id = os.rubrique_id AND os.prof_id NOT LIKE 0"%classe)
    cursor.execute(query)
    for periode, appr, matiere in cursor:
        resultats[classe]['appreciations'][periode][matiere] = appr.replace(u"\2019","'")


##############################
#   Appréciations (élèves)   #
##############################
# On collecte toutes les appréciations, triées par periode
# Les appréciations servent également à associer un prof à chaque matière de l'élève

# Attention: la table officiel_saisie contient des ID de groupe et de classe dans
# la même colonne, il faut être vigilant

# rubrique_id est associable à matiere_id
# rubrique_id = 0 pour moyenne/appréciation générale
# Ignorer prof_id = 0 (lignes qui stockent la moyenne de la classe (telle que calc par Sacoche))

for classe in resultats:
    query = ("SELECT p.periode_nom, os.saisie_appreciation, os.eleve_ou_classe_id, "
             "m.matiere_nom, os.prof_id  "
             "FROM sacoche_officiel_saisie as os, sacoche_groupe as g, "
             "sacoche_matiere as m, sacoche_periode as p, sacoche_user as u "
             "WHERE p.periode_id = os.periode_id " # pour p.periode_nom
             "AND u.user_sortie_date > NOW() "
             "AND os.saisie_type = 'eleve' " # appréciations des élèves, pas des classes
             "AND os.rubrique_id NOT LIKE 0 " # pas les appréciations générales
             "AND u.user_id = os.eleve_ou_classe_id " # lignes suivantes: trouver la classe (groupe_nom)
             "AND g.groupe_id = u.eleve_classe_id "
             "AND g.groupe_nom = '%s' "
             "AND m.matiere_id = os.rubrique_id AND os.prof_id NOT LIKE 0"%classe) # nom matière
    cursor.execute(query)

    for periode, appr, eleve, matiere, prof in cursor:
        # WARNING: Unicode / UTF-8 / Erreurs d'encodage
        # Pour supporter les caractères unicode, il faudrait installer une autre police
        # Le choix a été fait de remplacer les caractères au cas par cas
        # Voir: https://pyfpdf.readthedocs.io/en/latest/Unicode/index.html
        resultats[classe][eleve][periode]['appreciations'][matiere] = appr.replace(u"\u2019","'").replace(u'\u2026',"...")
        resultats[classe][eleve]['profs'][matiere] = prof # HYP: 1 prof par matière !


    ### Appréciation globale de l'élève
    query = ("SELECT p.periode_nom, os.eleve_ou_classe_id, os.saisie_appreciation "
             "FROM sacoche_officiel_saisie as os, sacoche_periode as p "
             "WHERE rubrique_id = 0 AND saisie_type = 'eleve' AND prof_id NOT LIKE 0 "
             "AND p.periode_id = os.periode_id ")
    cursor.execute(query)
    for periode, eleve, appr in cursor:
        resultats[classe][eleve][periode]['bilan'] = appr.replace(u"\u2019","'")

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


################
#   Absences   #
################
# Dans sacoche_officiel_assiduite, on a le nb d'absences (1/2 journées ?)
# et le nb d'abs non-justifiées.
# RQ: Absences exportées de Pronote (cf. doc. SACoche)

query = ("SELECT g.groupe_nom, oa.user_id, p.periode_nom, oa.assiduite_absence, "
         "oa. assiduite_absence_nj "
         "FROM sacoche_officiel_assiduite as oa, sacoche_groupe as g, "
         "sacoche_periode as p, sacoche_user as u "
         "WHERE p.periode_id = oa.periode_id " # pour p.periode_nom
         "AND u.user_id = oa.user_id " # lignes suivantes: trouver la classe (groupe_nom)
         "AND g.groupe_id = u.eleve_classe_id "
         "AND u.user_sortie_date > NOW()")
cursor.execute(query)
for classe, eleve, periode, abs, abs_non_reglees in cursor:
    # Si on a des valeurs None (NULL), on passe
    if abs is None:
        continue
    # On peut avoir abs != None & abs_n_r = None (saisie manuelle)
    if abs_non_reglees is None:
        abs_non_reglees = 0
    resultats[classe][eleve][periode]['absences'] = (abs,abs_non_reglees)



#######################
#   Fichier parents   #
#######################
# On fait un fichier dans lequel on ira chercher les coordonnées des parents
# à faire apparaître sur le bulletin pour l'envoi aux familles
parents = nested_dict()

query = ("SELECT u.user_id, u.user_nom, u.user_prenom, pa.adresse_ligne1, pa.adresse_ligne2, "
        "pa.adresse_ligne3, pa.adresse_ligne4, pa.adresse_postal_code, pa.adresse_postal_libelle, "
        "pa.adresse_pays_nom, jpe.resp_legal_num "
        "FROM sacoche_user as u, sacoche_parent_adresse as pa, sacoche_jointure_parent_eleve as jpe "
        "WHERE pa.parent_id = u.user_id AND jpe.parent_id = u.user_id")
cursor.execute(query)

for id, nom, prenom, al1, al2, al3, al4, CP, ville, pays, num in cursor:
    parents[id]['nom'] = nom + ' ' + prenom
    parents[id]['num'] = num

    # Adresse multiligne dans 1 variable
    al = [al1, al2, al3, al4]
    adresse = ''
    for ligne in al:
        if ligne == '':
            pass
        else:
            adresse += ligne
            adresse += '\n'

    adresse = adresse + CP + ' ' + ville
    if pays != "FRANCE":
        adresse = adresse + '\n' + pays

    parents[id]['adresse'] = adresse

with open('classes.json', 'w') as json_file:
    json.dump(resultats, json_file, indent='\t')


with open('profs.json', 'w') as json_file:
    json.dump(profs_matiere, json_file, indent='\t')

with open('parents.json', 'w') as json_file:
    json.dump(parents, json_file, indent='\t')
