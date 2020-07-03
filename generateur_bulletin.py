from fpdf import FPDF

###############
#  Fonctions  #
###############

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
        r,g,b = (255,0,0)
    if moyenne >= 1.75 and moyenne < 2.5: # moyen: orange
        r,g,b = (235,200,53)
    if moyenne >= 2.5 and moyenne < 3.25: # bien: vert
        r,g,b = (203,253,93)
    if moyenne >= 3.25: # très bien: vert foncé
        r,g,b = (0,255,0)

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


################################
#  Init et variables globales  #
################################
### Construction de l'objet FPDF
p = FPDF('L','cm','A4')
marge = 0.64
height, width = (21.0,29.7)
p.set_margins(marge,marge,marge) # marges (pas de marge_bottom, mais ligne suivante aide)
p.set_auto_page_break(False) # empêcher les page break automatiques (donc ~ pas de marge en bas)

p.set_font('Arial','',8)

### variables globales
aff_bord = 1 # utilisé pendant la mise en place, désactiver pour imprimer un bulletin propre
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
offset_appr = h_cell/6 # espace vide horizontal pour aérer les appréciations
height_appr = 3*h_cell + 2*offset_appr # hauteur d'un bloc "appréciation"
x_appr, y_appr = marge,marge+5*h_cell # coordonnées du bloc "Appréciations"
# Appréciation direction/mention
x_appr_dir, y_appr_dir = marge, height-marge-4*h_cell
x_mention = x_appr_dir+marge+w_appreciation
# Signature chef d'etbl
signature = 'fleur.png' # path de la signature
h_signature = 2*h_cell # largeur de la signature
x_chef = width-marge-2*w_prof # position du texte "chef"
y_chef = height-marge-2*h_cell
# Bloc évaluation (matiere+couleur/thème)
w_bloc = 4
x_bloc = x_appr+w_appreciation+marge
y_bloc = y_appr

lorem = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis,'
matieres = ['FRANCAIS', 'LVA ANGLAIS', 'LVB ESPAGNOL', 'HIST.-GEOGRAPHIE','ENS. MORAL & CIV.', 'SC. ECO. & SOCIALES', 'MATHEMATIQUES', 'PHYSIQUE-CHIMIE','SC. VIE & TERRE', 'ED. PHY. & SPORT.', 'SC. NUM. & TECHNO.', 'OPTION']
moyenne_matiere = {"Restituer":2,"S'informer": 'AB',"Communiquer": None, "Raisonner":3.1, "S'impliquer":3.5, "Utiliser":0}

### Il faut explicitement ajouter les pages, donc page 1
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
# TODO: Période
p.set_font('Arial','B',9)
p.cell(w_periode,h_cell,"Bulletin du 1er trimestre",aff_bord,0,'C')
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
# TODO: Variables classe et PP (+ année scolaire ?)
infos_classe = "Année scolaire 2020-2021\nClasse: Classe test\nPP: Mme Professeure"
p.multi_cell(w_infos_classe,h_cell,infos_classe,aff_bord,'L',False)

# TODO: prénom
p.set_font('Arial','B',9)
prenom = "DUPONT Jean Enzo Kevin"
p.cell(w_periode-w_infos_classe,h_cell,prenom,aff_bord,2,'L')

# Infos persos élève (TODO)
p.set_font('Arial','',9)
infos_perso = "Né le 01/01/2005\nINE : 0123456789A"
p.multi_cell(w_periode-w_infos_classe,h_cell,infos_perso,aff_bord,'L')

# Absences + appréciation vie sco (TODO)
p.set_xy(p.get_x(),p.get_y()-h_cell)
texte_viesco = "Absences : 3 demi-journées dont 1 non-réglée.\nAppréciation : Rien à signaler."
p.multi_cell(0,h_cell,texte_viesco,aff_bord,'L')

########################
#  Bloc appréciations  #
########################

# Test fonction
for i in range(12):
    ligne_appreciation(x_appr,y_appr,(matieres[i],'Mme. Professeure',lorem))
    y_appr+=height_appr

# Ne pas oublier de re-régler la police après avoir appelé ligne_appreciation
p.set_font('Arial','',8)

#############################
#  Appr. générale/mentions  #
#############################

# Appréciation de la direction/PP
p.set_font('Arial','B',8)
p.set_xy(x_appr_dir,y_appr_dir)
p.cell(w_prof,h_cell,'Appréciation globale :',aff_bord,0)
p.set_font('Arial','',8)
p.multi_cell(w_appreciation-w_prof,h_cell,lorem,aff_bord,'L')

# Mention
# TODO: Question à poser: "mention:" apparaît toujours même si pas de mention ?
p.set_font('Arial','B',8)
p.set_xy(x_mention,y_appr_dir)
p.cell(w_prof/2,h_cell,'Mention :',aff_bord,0)
p.set_font('Arial','',8)
p.cell(0,h_cell,'Félicitations du conseil de classe',aff_bord,0) # TODO var

####################
#  Signature chef  #
####################
# Mention "le chef d'établissement" + signature
p.set_xy(x_chef,y_chef)
p.cell(w_prof,h_cell,"Le chef d'établissement",aff_bord,0)
p.image(signature,p.get_x(),p.get_y()-0.5*h_cell, h=h_signature)


bloc_eval(x_bloc,y_bloc,'matiere',moyenne_matiere)


### Création du fichier
p.output('bulletin.pdf', 'F')
