import sys
import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def lecture(fichier):
    with open(fichier, 'r') as f:
        lignes = f.readlines()
    lignes = lignes[1:]
    donnees = []
    for id, ligne in enumerate(lignes):
        ligne = ligne.strip().split()
        donnees.append({"id": id, "ori": ligne[0], "tags": set(ligne[2:])})
    return donnees

def creation(donnees):
    horiz = []
    vert = []
    for p in donnees:
        if p["ori"] == "H":
            horiz.append([p])
        else:
            vert.append(p)
    
    diapo = horiz[:]
    if len(vert) > 1:
        pairs = list(combinations(vert, 2))
        pairs.sort(key=lambda p: -len((p[0]["tags"] | p[1]["tags"]) - (p[0]["tags"] & p[1]["tags"])))
        used = set()
        for p1, p2 in pairs:
            if p1["id"] not in used and p2["id"] not in used:
                diapo.append([p1, p2])
                used.add(p1["id"])
                used.add(p2["id"])
    return diapo

def evaluation(a, b):
    t1 = {t for p in a for t in p["tags"]}
    t2 = {t for p in b for t in p["tags"]}
    common_tags = t1 & t2
    unique_a = t1 - t2
    unique_b = t2 - t1
    return min(len(common_tags), len(unique_a), len(unique_b)), common_tags

def optimisation(diapo):
    m = gp.Model("Diapo")
    n = len(diapo)
    
    x = {(i, j): m.addVar(vtype=GRB.BINARY) for i in range(n) for j in range(n) if i != j}
    u = {i: m.addVar(vtype=GRB.CONTINUOUS) for i in range(n)}
    
    for i in range(n):
        m.addConstr(sum(x[i, j] for j in range(n) if i != j) == 1)
        m.addConstr(sum(x[j, i] for j in range(n) if i != j) == 1)
    
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                m.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)
    
    m.setObjective(
        sum((evaluation(diapo[i], diapo[j])[0] ** 6) * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MAXIMIZE
    )
    
    m.optimize()
    
    ordre = []
    visited = set()
    current = max(range(n), key=lambda i: sum(evaluation(diapo[i], diapo[j])[0] for j in range(n) if i != j))
    ordre.append(current)
    visited.add(current)

    while len(ordre) < n:
        next_candidates = [j for j in range(n) if j not in visited]
        next_slide = max(next_candidates, key=lambda j: x[current, j].x if (current, j) in x else -1)
        ordre.append(next_slide)
        visited.add(next_slide)
        current = next_slide

    return [diapo[i] for i in ordre]

def sortie(fichier_sortie, diapo):
    with open(fichier_sortie, 'w') as f:
        f.write(f"{len(diapo)}\n")
        for s in diapo:
            f.write(" ".join(str(p["id"]) for p in s) + "\n")
    
    print("\nTransitions du diaporama optimisé :")
    score_total = 0
    for i in range(len(diapo) - 1):
        score, common_tags = evaluation(diapo[i], diapo[i+1])
        score_total += score
        print(f"Transition {i} -> {i+1} : Score = {score}, Tags communs = {common_tags}")
    print(f"Score total du diaporama : {score_total}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py <fichierDonnees>")
        sys.exit(1)

    fichierDonnees = sys.argv[1]
    photos = lecture(fichierDonnees)
    diapositives = creation(photos)
    diaporama_optimise = optimisation(diapositives)
    sortie("slideshow.sol", diaporama_optimise)
    
if __name__ == "__main__":
    main()
