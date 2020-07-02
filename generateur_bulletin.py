from fpdf import FPDF

# ################################
# #  Init et variables globales  #
# ################################
### Construction de l'objet FPDF
p = FPDF('L','cm','A4')
marge = 0.64
height, width = (21.0,29.7)
p.set_margins(marge,marge,marge) # marges (pas de marge_bottom, mais ligne suivante aide)
p.set_auto_page_break(False) # empêcher les page break automatiques (donc ~ pas de marge)

### variables globales
logo = "logo_lycée.png"


p.add_page()


p.image('logo_lycée.png',marge,marge, w=1.7)

p.output('bulletin.pdf', 'F')
