from fpdf import FPDF
import json
import re
from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)

# Todo: Verso du bulletin = Adresse des parents pour glisser le bulletin dans une enveloppe à fenêtre.

###############
#  Fonctions  #
###############


def make_bulletin():
    global y_appr
    global p
    p = FPDF('L','cm','A4')
    p.set_margins(marge,marge,marge) # marges (pas de marge_bottom, mais ligne suivante aide)
    p.set_auto_page_break(False) # empêcher les page break automatiques (donc ~ pas de marge en bas)

    p.add_page()

    #################################
    #  Logo + coordonnées du lycée  #
    #################################

    # Logo
    p.image('logo_lycée.png',marge,marge, w=w_logo)

    # Adresse
    p.set_font('Arial','',7)
    p.set_xy(w_logo+marge,marge)
    adr_lycee = "Académie de Créteil\nLycée Polyvalent Louise Michel\n7 Rue Pierre Marie Derrien\n94500 Champigny-sur-Marne\nTél. : 01.48.82.07.35"
    p.multi_cell(w_adr_lycee,h_cell-0.1,adr_lycee,aff_bord,'C',False)

    ###############################
    #  En-tête période + vie sco  #
    ###############################

    # Titres en gras: bulletin de période, vie scolaire
    p.set_font('Arial','B',9)
    p.cell(w_periode,h_cell,"Bulletin du "+periode.lower(),aff_bord,0,'C')
    p.cell(0,h_cell,"Vie scolaire",aff_bord,0,'C')

    # ligne horizontale
    x0 = marge+w_logo+w_adr_lycee
    x1 = width-marge
    y0 = marge+h_cell
    y1 = marge+h_cell
    p.line(x0,y0,x1,y1)

    # Infos de la classe
    p.set_font('Arial','',9)
    p.set_xy(x0,y0) # on commence au début de la ligne
    # infos_classe = "Année scolaire 2020-2021\nClasse: Classe test\nPP: Mme Professeure"
    # p.multi_cell(w_infos_classe,h_cell,infos_classe,aff_bord,'L',False)
    p.cell(w_infos_classe,h_cell,'Année scolaire: %s'%annee_sco,aff_bord,2,'L')
    p.cell(w_infos_classe,h_cell,'Classe: %s'%classe,aff_bord,2,'L')
    p.cell(w_infos_classe,h_cell,'PP: %s'%prof_principal,aff_bord,2,'L')

    p.set_xy(x0+w_infos_classe,y0)

    # prénom élève
    p.set_font('Arial','B',9)
    p.cell(w_periode-w_infos_classe,h_cell,nom,aff_bord,2,'L')

    # Infos persos élève (TODO)
    p.set_font('Arial','',9)
    infos_perso = "Né le 01/01/2005\nINE : 0123456789A"
    p.multi_cell(w_periode-w_infos_classe,h_cell,infos_perso,aff_bord,'L')

    # Absences + appréciation vie sco (TODO)
    # TODO: Passer l'appréciation vie sco sur une plus petite police (8 comme appr dir)
    p.set_xy(p.get_x(),p.get_y()-h_cell)
    texte_viesco = "Absences : 3 demi-journées dont 1 non-réglée.\nAppréciation : Rien à signaler."
    p.multi_cell(0,h_cell,texte_viesco,aff_bord,'L')

    ########################
    #  Bloc appréciations  #
    ########################

    # NOTE: On veut faire apparaître les appréciations dans un ordre précis
    # hardcodé ici
    ordre_matieres = ['FRANCAIS', 'LVA ANGLAIS', 'LVB ESPAGNOL', 'HIST.-GEOGRAPHIE','ENS. MORAL & CIV.', 'SC. ECO. & SOCIALES', 'MATHEMATIQUES', 'PHYSIQUE-CHIMIE','SC. VIE & TERRE', 'ED. PHY. & SPORT.', 'SC. NUM. & TECHNO.', 'OPTION']

    i=0
    for matiere in ordre_matieres:
        if matiere in moyennes:
            ligne_appreciation(x_appr,y_appr+i*height_appr,(matiere,moyennes[matiere]['prof'],moyennes[matiere]['appreciation']))
            i+=1

    ###################
    #  Bloc moyennes  #
    ###################

    # Vu qu'on a un template fixe, on va se contenter d'appeler des fonctions bien définies
    temp_dict = {
        'FRANCAIS': moyenne_matiere,
        'LVA ANGLAIS': moyenne_matiere,
        'LVB ESPAGNOL': moyenne_matiere
    }
    ligne_eval(x_bloc,y_bloc,temp_dict)
    temp_dict = {
        'HIST.-GEOGRAPHIE': moyenne_matiere,
        'ENS. MORAL & CIV.': moyenne_matiere,
        'SC. ECO. & SOCIALES': moyenne_matiere
    }
    ligne_eval(x_bloc,y_bloc + 7*h_cell + h_offset_blocs, temp_dict)
    temp_dict = {
        'MATHEMATIQUES': moyenne_matiere,
        'PHYSIQUE-CHIMIE': moyenne_matiere,
        'SC. VIE & TERRE': moyenne_matiere
    }
    ligne_eval(x_bloc,y_bloc + 2*(7*h_cell + h_offset_blocs), temp_dict)
    temp_dict = {
        'ED. PHY. & SPORTIVE': moyenne_matiere,
        'SC. NUM. & TECHNO.': moyenne_matiere,
        'OPTION': moyenne_matiere
    }
    ligne_eval(x_bloc,y_bloc + 3*(7*h_cell + h_offset_blocs), temp_dict)

    legende(x_bloc,y_bloc + 4*(7*h_cell + h_offset_blocs))

    #############################
    #  Appr. générale/mentions  #
    #############################

    # Appréciation de la direction/PP
    p.set_font('Arial','B',8)
    p.set_xy(x_appr_dir,y_appr_dir)
    p.cell(w_prof,h_cell,'Appréciation globale :',aff_bord,0)
    p.set_font('Arial','',8)
    p.multi_cell(0,h_cell,lorem,aff_bord,'L')

    # Mention
    # TODO: Question à poser: "mention:" apparaît toujours même si pas de mention ?
    p.set_font('Arial','B',8)
    p.set_xy(x_appr_dir,y_appr_dir+4*h_cell)
    p.cell(w_prof/2,h_cell,'Mention :',aff_bord,0)
    p.set_font('Arial','',8)
    p.cell(0,h_cell,'Félicitations du conseil de classe',aff_bord,0) # TODO var

    ####################
    #  Signature chef  #
    ####################
    # Mention "le chef d'établissement" + signature
    p.set_xy(x_chef,y_chef)
    p.cell(w_prof,h_cell,"Le chef d'établissement",aff_bord,0)
    #p.image(signature,p.get_x(),p.get_y()-0.5*h_cell, h=h_signature)




    ### Création du fichier
    p.output('bulletin/%s.pdf'%nom, 'F')

## Bloc appréciation
def ligne_appreciation(x,y,appr):
    # appr: (matiere,prof,appr)
    # On rentre dans un rectangle de w_appreciation de largeur
    # 3 h_cell+2*offset_appr de haut
    # l'offset sert à aérer la présentation
    x0=x ; y0 = y

    # espace vide
    p.set_xy(x,y)
    p.cell(w_appreciation, offset_appr,'',ln=2)

    # Affichage matière
    p.set_font('Arial','B',8)
    p.cell(w_prof,h_cell,appr[0],ln=2)

    # Affichage enseignant
    p.set_font('Arial','I',8)
    p.cell(w_prof,h_cell,appr[1])

    # Affichage appréciation
    p.set_font('Arial','',7.5)
    p.set_xy(x0+w_prof,y0+offset_appr)
    p.multi_cell(w_appreciation-w_prof,h_cell,appr[2], align='L')

    # Bordure autour du bloc
    p.rect(x0,y0,w_appreciation,height_appr)


def bloc_eval(x,y,matiere,moyennes):
    # matiere: str qui apparaîtra en haut du bloc
    # moyennes: dict format {'Restituer': 2.1;'Utiliser': 3}
    # donc thème -> moyenne (entre 1 et 4)

    x0=x ; y0 = y
    p.set_xy(x,y)

    # Case avec le nom de la matière
    p.set_font('Arial','B',9)
    p.set_fill_color(192) # niveau de gris
    p.cell(w_bloc,h_cell,matiere,1,2,'C',fill=True)

    # Cases avec les noms des thèmes
    p.set_font('Arial','',8)
    p.cell(2*w_bloc/3,h_cell,'Restituer',aff_bord,2,'L')
    p.cell(2*w_bloc/3,h_cell,"S'informer",aff_bord,2,'L')
    p.cell(2*w_bloc/3,h_cell,'Communiquer',aff_bord,2,'L')
    p.cell(2*w_bloc/3,h_cell,'Raisonner',aff_bord,2,'L')
    p.cell(2*w_bloc/3,h_cell,"S'impliquer",aff_bord,2,'L')
    p.cell(2*w_bloc/3,h_cell,'Utiliser',aff_bord,2,'L')

    # Cases avec les couleurs
    p.set_xy(x0+2*w_bloc/3,y0+h_cell)
    aff_moyenne(moyennes['Restituer'])
    aff_moyenne(moyennes["S'informer"])
    aff_moyenne(moyennes['Communiquer'])
    aff_moyenne(moyennes['Raisonner'])
    aff_moyenne(moyennes["S'impliquer"])
    aff_moyenne(moyennes['Utiliser'])

    # Bordure autour du bloc
    p.rect(x0,y0,w_bloc,7*h_cell)

def ligne_eval(x,y,dict):
    # Construit une ligne avec 3 blocs éval
    # x,y: coordonnées du coin supérieur gauche du premier bloc
    # dict: dico format d[matiere]={'theme1'=moyenne, 'theme2'=moyenne, ...}
    # Hyp: les matieres sont dans l'ordre souhaitées par le template
    # RQ: Python 3.7+: ordre préservé dans les dictionnaires

    matieres = list(dict)
    bloc_eval(x,y,matieres[0],dict[matieres[0]])

    # Coordonnées pour le bloc 2
    x2 = x+w_bloc+w_offset_blocs
    bloc_eval(x2,y,matieres[1],dict[matieres[1]])

    # Coordonnées pour le bloc 3
    x3 = x2+w_bloc+w_offset_blocs
    bloc_eval(x3,y,matieres[2],dict[matieres[2]])

def aff_moyenne(moyenne):
    # Crée et remplit l'objet (cell ou rect+fill) pour afficher la moyenne d'un thème
    # Le curseur est placé à y=y+h_cell à la fin de la fonction
    # moyenne: float entre 1 et 4
    # hypothèses: le curseur est en haut à gauche de l'espace réservé à la moyenne
    #             la largeur prévue est w_bloc/3
    #             la hauteur est h_cell

    # D'abord: Est-ce que la moyenne est None ? (thème non évalué)
    # Dans ce cas, on n'affiche rien
    if moyenne is None:
        p.cell(w_bloc/3,h_cell,'',aff_bord,2) # moyen le plus simple de faire ce qu'on veut
        return

    # Ensuite: Est-ce que la moyenne est un nombre ? Si c'est un str, on l'affiche
    # (par ex Ab, NE, NN)
    if isinstance(moyenne,str):
        p.set_font('Arial','',8)
        p.cell(w_bloc/3,h_cell,moyenne,aff_bord,2,'C')
        return

    # Enfin: Si on a bien un nombre, prendre la couleur qui va bien
    # Todo: passer ces seuils en variables globales
    # Pour l'instant: on prend un seuil tous les 0.75 (largeur intervalle/nb couleurs)

    if moyenne < 1.75: # Mauvais = rouge
        r,g,b = rouge
    if moyenne >= 1.75 and moyenne < 2.5: # moyen: orange
        r,g,b = orange
    if moyenne >= 2.5 and moyenne < 3.25: # bien: vert
        r,g,b = vert_clair
    if moyenne >= 3.25: # très bien: vert foncé
        r,g,b = vert_fonce

    # Centre du rectangle: (w_bloc/6,h_cell/2)
    # Position du curseur: (x,y)
    x0,y0 = p.get_x(),p.get_y()
    # Taille du rectangle: (0.8,2*h_cell/3)
    # Position du coin supérieur gauche du rectangle: (x+w_bloc/6-0.8,y+h_cell/2-2*h_cell/3)
    x=p.get_x()+w_bloc/6-0.8/2 ; y=p.get_y()+h_cell/2-2*h_cell/3/2
    p.set_fill_color(r,g,b)
    p.rect(x,y,0.8,2*h_cell/3,'F')

    # On met le curseur où il faut
    p.set_xy(x0,y0+h_cell)

    return

def legende(x,y):
    # Ligne qui va sous la dernière ligne de bloc éval
    w = (3*w_bloc+2*w_offset_blocs-4*h_cell)/4 # var locale pour la largeur des cellules
    o = w+h_cell # pour décaler d'assez chaque bloc

    p.set_font('Arial','I',6)

    r,g,b = rouge
    p.set_fill_color(r,g,b)
    p.rect(x,y,h_cell,h_cell,'F')
    p.set_xy(x+h_cell,y)
    p.cell(w,h_cell,'Très insuffisant',aff_bord)

    r,g,b = orange
    p.set_fill_color(r,g,b)
    p.rect(x+o,y,h_cell,h_cell,'F')
    p.set_xy(x+w+2*h_cell,y)
    p.cell(w,h_cell,'Insuffisamment maîtrisé',aff_bord)

    r,g,b = vert_clair
    p.set_fill_color(r,g,b)
    p.rect(x+2*o,y,h_cell,h_cell,'F')
    p.set_xy(x+2*o+h_cell,y)
    p.cell(w,h_cell,'Satisfaisant',aff_bord)

    r,g,b = vert_fonce
    p.set_fill_color(r,g,b)
    p.rect(x+3*o,y,h_cell,h_cell,'F')
    p.set_xy(x+3*o+h_cell,y)
    p.cell(w,h_cell,'Très satisfaisant',aff_bord)

################################
#  Init et variables globales  #
################################
### variables globales
marge = 0.64
height, width = (21.0,29.7)
aff_bord = 0 # utilisé pendant la mise en place, désactiver pour imprimer un bulletin propre
h_cell = 0.4 # hauteur globale des p.cell()
# Logo
logo = "logo_lycée.png"
w_logo = 1.7 # largeur logo
# En-tête
w_periode = 11 # largeur du bloc "Bulletin du trimestre X"
w_adr_lycee = 4.5 # largeur du bloc des coordonnées du lycée
w_infos_classe = 4 # largeur du bloc "Année sco/Classe/PP"
# Appréciations prof
w_prof = 3.4 # largeur du bloc "matiere/enseignant" dans appr
w_appreciation = 15 # largeur du bloc appréciation (matiere+appr)
offset_appr = h_cell/4 # espace vide horizontal pour aérer les appréciations
height_appr = 3*h_cell + 2*offset_appr # hauteur d'un bloc "appréciation"
x_appr, y_appr = marge, marge+5*h_cell # coordonnées du bloc "Appréciations"

# Appréciation direction/mention
offset_appr_dir = 0.4
x_appr_dir, y_appr_dir = marge+marge+w_appreciation, height-marge-8*h_cell-offset_appr_dir
# Signature chef d'etbl
signature = 'fleur.png' # path de la signature
h_signature = 2*h_cell # largeur de la signature
x_chef = width-marge-2*w_prof # position du texte "chef"
y_chef = height-marge-2*h_cell-offset_appr_dir

# Bloc évaluation (matiere+couleur/thème)
w_bloc = 4
x_bloc = x_appr+w_appreciation+marge
y_bloc = y_appr
w_offset_blocs = 0.3 # ecart horizontal entre deux blocs
h_offset_blocs = 0.5 # ecart vertical entre deux blocs
rouge = (255,0,0)
orange = (250,145,56)
vert_clair = (181,213,0)
vert_fonce = (48,145,52)

lorem = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis,'
# Dictionnaire de matching entre l'intitulé long et l'intitulé court d'une matière
matieres = {'Français':'FRANCAIS', 'Anglais': 'LVA ANGLAIS', 'Espagnol': 'LVB ESPAGNOL',
            'Histoire-géographie': 'HIST.-GEOGRAPHIE','Enseignement moral et civique':'ENS. MORAL & CIV.',
            'Sciences économiques et sociales':'SC. ECO. & SOCIALES', 'Mathématiques':'MATHEMATIQUES',
            'Physique-chimie':'PHYSIQUE-CHIMIE','Sciences de la vie et de la terre':'SC. VIE & TERRE',
            'Education physique et sportive':'ED. PHY. & SPORT.',
            'Sciences numériques et technologie':'SC. NUM. & TECHNO.', 'Sciences & laboratoire': 'OPTION'}
moyenne_matiere = {"Restituer":2,"S'informer": 'Abs',"Communiquer": None, "Raisonner":3.1, "S'impliquer":3.5, "Utiliser":0}

#############################
#  Lecture du fichier JSON  #
#############################
with open("temp.json","r") as fichier_resultats:
    resultats = json.load(fichier_resultats)


##################################
#  Variables de chaque bulletin  #
##################################
# Année scolaire à indiquer (manuel)
annee_sco = '2020-2021'
# Choix de la période: Trimestre 1, Trimestre 2, Trimestre 3
periode = "Trimestre 1"

# TODO: Boucle sur les classes
# for classe in resultats:
classe = 'Classe test'

matiere_prof = {}
# Dico matiere <-> profs
for id in resultats[classe]['profs']:
    for matiere in resultats[classe]['profs'][id]['matiere']:
        matiere_prof[matiere] = resultats[classe]['profs'][id]['nom']

print(matiere_prof)
# Identification du PP de la classe
for prof in resultats[classe]['profs']:
    if resultats[classe]['profs'][prof]['pp']:
        prof_principal = resultats[classe]['profs'][prof]['nom']
        print('pp ',prof_principal)
        break


# Dans chaque entrée resultats[classe], les élèves sont repérés par leur id
# les autres infos ont des str en key
eleves = []
for k in resultats['Classe test']:
    match = re.search('^[0-9]+',k)
    if match is not None:
        eleves.append(match.group())


# Génération du bulletin pour chaque élève
for eleve in eleves:
    ## Infos personnelles
    # Nom et prénom de l'élève
    nom = resultats[classe][eleve]['nom'] + ' ' + resultats['Classe test'][eleve]['prenom']

    # TODO: INE, date de naissance

    ## TODO: Vie scolaire

    ### Appréciations matières

    ## On liste les matières de l'élève avec l'ens et l'appr de la période
    # NOTE: Inefficace, mais évite les problèmes de gestion d'options
    # (tel élève n'a pas telle matière, elle ne doit donc pas apparaître)
    moyennes = nested_dict()
    # Dictionnaire de matching entre l'intitulé long et l'intitulé court d'une matière
    # matieres = {'Français':'FRANCAIS', 'Anglais': 'LVA ANGLAIS', 'Espagnol': 'LVB ESPAGNOL', 'Histoire-géographie': 'HIST.-GEOGRAPHIE','Enseignement moral et civique':'ENS. MORAL & CIV.', 'Sciences économiques et sociales':'SC. ECO. & SOCIALES', 'Mathématiques':'MATHEMATIQUES', 'Physique-chimie':'PHYSIQUE-CHIMIE','Sciences de la vie et de la terre':'SC. VIE & TERRE', 'Education physique et sportive':'ED. PHY. & SPORT.', 'Sciences numériques et technologie':'SC. NUM. & TECHNO.'}

    for matiere in resultats[classe][eleve][periode]['moyennes']:
        try:
            moyennes[matieres[matiere]]['prof'] = matiere_prof[matiere]
            moyennes[matieres[matiere]]['appreciation'] = resultats[classe][eleve][periode]['appreciations'][matiere]
        except KeyError as e:
            moyennes[matieres[matiere]]['prof'] = ''
            moyennes[matieres[matiere]]['appreciation'] = ''
            print("La matière %s n'a pas d'entrée dans le dico prof-matière"%matiere)
            print("C'est parce qu'aucune appréciation n'a été rentrée !")
            # TODO: Gestion des matières et des profs à revoir


    print(moyennes)



    make_bulletin()
