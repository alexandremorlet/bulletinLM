from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Image


################################
#  Init et variables globales  #
################################
c = canvas.Canvas("bulletin.pdf", pagesize=landscape(A4))
height, width = A4 # ! usuellement w,h=A4, mais on réfléchit en paysage ici

marge = 0.64*cm # marges étroites
logo = "logo_lycée.png"

#######################
#  Coordonnées lycée  #
#######################
## En haut à gauche de la page, logo + adresse du lycée
# LOGO
height_logo = 1.7*cm
width_logo = 1.8*cm
c.drawImage(logo,marge,height-marge-height_logo,height=height_logo, width=1.8*cm)



c.showPage() # enregistre le canvas (page courante)
             # commence une nouvelle page si suivi d'autres commandes
c.save()     # génère le PDF
