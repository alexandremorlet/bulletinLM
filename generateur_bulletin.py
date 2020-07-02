from fpdf import FPDF

###############
#  Fonctions  #
###############


################################
#  Init et variables globales  #
################################
### Construction de l'objet FPDF
p = FPDF('L','cm','A4')
marge = 0.64
height, width = (21.0,29.7)
p.set_margins(marge,marge,marge) # marges (pas de marge_bottom, mais ligne suivante aide)
p.set_auto_page_break(False) # empêcher les page break automatiques (donc ~ pas de marge)

p.set_font('Arial','',8)

### variables globales
aff_bord = 1 # utilisé pendant la mise en place, désactiver pour imprimer un bulletin propre
logo = "logo_lycée.png"
w_logo = 1.7

### Il faut explicitement ajouter les pages, donc page 1
p.add_page()

#################################
#  Logo + coordonnées du lycée  #
#################################

# Logo
p.image('logo_lycée.png',marge,marge, w=w_logo)

# Adresse
p.set_xy(w_logo+marge,marge)
adr_lycee = "Académie de Créteil\nLycée Polyvalent Louise Michel\n7 Rue Pierre Marie Derrien\n94500 Champigny-sur-Marne\nTél. : 01.48.82.07.35"
p.multi_cell(4.5,0.4,adr_lycee,aff_bord,'C',False)


### Création du fichier
p.output('bulletin.pdf', 'F')
