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


lorem = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis,'

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
    ligne_appreciation(x_appr,y_appr,('SC. ECO. & SOCIALES','Mme. Professeure',lorem))
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

### Création du fichier
p.output('bulletin.pdf', 'F')
