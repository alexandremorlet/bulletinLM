"""
Script qui permet de fusionner tous les bulletins pour faire un fichier imprimable.
Deux fichiers en sortie: un à destination de l'équipe pédagogique (1 bulletin/élève,
sans coordonnées des parents) et un pour la direction (1 bulletin/responsable).
"""

from PyPDF2 import PdfFileMerger, PdfFileReader
import os

bulletins_dir = "./bulletin/"
bulletins = os.listdir(bulletins_dir)

# Simple merge pour version à imprimer et à envoyer aux parents
merger = PdfFileMerger()

for bulletin in bulletins:
    merger.append(PdfFileReader(open(bulletins_dir+bulletin, 'rb')))

merger.write("bulletins_parents.pdf")


# Merge où on enlève les doublons et la page 2 (adresse des parents)
merger = PdfFileMerger()

print(bulletins)
for b in bulletins:
    if "2" in b:
        pass
    else:
        merger.append(PdfFileReader(open(bulletins_dir+b, 'rb')), pages=(0,1))

merger.write("bulletins_equipe.pdf")
