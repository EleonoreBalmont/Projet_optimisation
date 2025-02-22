import random
import sys
import gurobipy as gp
from gurobipy import GRB

# on lit le fichier: 
def lecture(fichier):
    with open(fichier, 'r') as f:
        lignes = f.readlines()
    lignes = lignes[1:]
    donnees = []
    id = 0
    for ligne in lignes:
        ligne = ligne.strip().split()
        element = {"id": id, "ori": ligne[0], "tags": set(ligne[2:])}
        donnees.append(element)
        id += 1
    return donnees

# On crée les diapositives en fonction de l'orientation des photos: 
def creation(donnees):
    horiz = []
    vert = []
    for p in donnees:
        if p["ori"] == "H":
            horiz.append([p])
        else:
            vert.append(p)
    
    diapo = horiz[:]
    while len(vert) > 1:
        p1 = vert[0]
        p2 = max(vert[1:], key=lambda p: len(p1["tags"] ^ p["tags"]))
        diapo.append([p1, p2])
        vert.remove(p1)
        vert.remove(p2)
    
    return diapo

# Calcul du score: 
def evaluation(a, b):
    t1 = {t for p in a for t in p["tags"]}
    t2 = {t for p in b for t in p["tags"]}
    return min(len(t1 & t2), len(t1 - t2), len(t2 - t1))

# On utilise gurobipy pour optimiser notre diapo: 
def optimisation(diapo):
    m = gp.Model("Diapo")
    n = len(diapo)
    
    x = {(i, j): m.addVar(vtype=GRB.BINARY) for i in range(n) for j in range(n)}
    
    for i in range(n):
        m.addConstr(sum(x[i, j] for j in range(n)) == 1)
        m.addConstr(sum(x[j, i] for j in range(n)) == 1)
    
    m.setObjective(sum(evaluation(diapo[i], diapo[j]) * x[i, j] for i in range(n) for j in range(n)), GRB.MAXIMIZE)
    m.optimize()
    
    ordre = sorted(range(n), key=lambda j: sum(x[i, j].x for i in range(n)), reverse=True)
    return [diapo[i] for i in ordre]


def sortie(fichier_sortie, diapo):
    with open(fichier_sortie, 'w') as f:
        f.write(f"{len(diapo)}\n")
        for s in diapo:
            f.write(" ".join(str(p["id"]) for p in s) + "\n")


# fonction principale: 
def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py <fichierDonnees>")
        sys.exit(1)

    fichierDonnees = sys.argv[1]
    photos = lecture(fichierDonnees)
    diapositives = creation(photos)
    diaporama_optimise = optimisation(diapositives)
    sortie("slideshow.sol", diaporama_optimise)
    print("Diaporama optimisé généré dans slideshow.sol")

if __name__ == "__main__":
    main()