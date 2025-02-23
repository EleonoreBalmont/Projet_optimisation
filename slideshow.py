import sys
import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def lect(fichier):
    with open(fichier, 'r') as f:
        lignes = f.readlines()
    lignes = lignes[1:]
    donnees = []
    for idf, ligne in enumerate(lignes):
        ligne = ligne.strip().split()
        donnees.append({"id": idf, "ori": ligne[0], "tags": set(ligne[2:])})
    return donnees

def creat(donnees):
    horiz, vert = [], []
    for p in donnees:
        if p["ori"] == "H":
            horiz.append([p])
        else:
            vert.append(p)
    
    diapo = horiz[:]
    if len(vert) > 1:
        paires = list(combinations(vert, 2))
        paires.sort(key=lambda p: -len(p[0]["tags"] ^ p[1]["tags"]))
        util = set()
        for p1, p2 in paires:
            if p1["id"] not in util and p2["id"] not in util:
                diapo.append([p1, p2])
                util.add(p1["id"])
                util.add(p2["id"])
    return diapo

def eval(a, b):
    t1, t2 = {t for p in a for t in p["tags"]}, {t for p in b for t in p["tags"]}
    com, uniq_a, uniq_b = t1 & t2, t1 - t2, t2 - t1
    return min(len(com), len(uniq_a), len(uniq_b)), com

def opti(diapo):
    m = gp.Model("Diapo")
    n = len(diapo)
    
    x = {(i, j): m.addVar(vtype=GRB.BINARY) for i in range(n) for j in range(n) if i != j}
    r = {i: m.addVar(vtype=GRB.CONTINUOUS) for i in range(n)}
    
    for i in range(n):
        m.addConstr(sum(x[i, j] for j in range(n) if i != j) == 1)
        m.addConstr(sum(x[j, i] for j in range(n) if i != j) == 1)
    
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                m.addConstr(r[i] - r[j] + n * x[i, j] <= n - 1)
    
    m.setObjective(
        sum((eval(diapo[i], diapo[j])[0] ** 5) * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MAXIMIZE
    )
    
    m.optimize()
    
    ordre, vis = [], set()
    cour = max(range(n), key=lambda i: sum(eval(diapo[i], diapo[j])[0] for j in range(n) if i != j))
    ordre.append(cour)
    vis.add(cour)

    while len(ordre) < n:
        cand = [j for j in range(n) if j not in vis]
        suiv = max(cand, key=lambda j: x[cour, j].x if (cour, j) in x else -1)
        ordre.append(suiv)
        vis.add(suiv)
        cour = suiv
    
    return post_process([diapo[i] for i in ordre])

def post_process(diapo):
    improved = True
    while improved:
        improved = False
        for i in range(len(diapo) - 1):
            for j in range(i + 1, len(diapo)):
                if eval(diapo[i], diapo[j])[0] > eval(diapo[i], diapo[i + 1])[0]:
                    diapo[i + 1], diapo[j] = diapo[j], diapo[i + 1]
                    improved = True
    return diapo

def sortie(f_sortie, diapo):
    with open(f_sortie, 'w') as f:
        f.write(f"{len(diapo)}\n")
        for s in diapo:
            f.write(" ".join(str(p["id"]) for p in s) + "\n")
    
    print("\nTransitions du diaporama optimise :")
    score_tot = 0
    for i in range(len(diapo) - 1):
        score, com = eval(diapo[i], diapo[i+1])
        score_tot += score
        print(f"Transition {i} -> {i+1} : Score = {score}, Tags communs = {com}")
    print(f"Score total du diaporama : {score_tot}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python slideshow.py <fichier_donnees>")
        sys.exit(1)

    f_donnees = sys.argv[1]
    photos = lect(f_donnees)
    diap = creat(photos)
    diapo_opti = opti(diap)
    sortie("slideshow.sol", diapo_opti)
    
if __name__ == "__main__":
    main()