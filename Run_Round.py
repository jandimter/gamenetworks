# -*- coding: utf-8 -*-
"""
Created on Thu Dec  2 13:27:11 2021

@author: jesal
"""

import networkclass as ntc
import pickle as pk
import json
import os
import networkx as nx



def _student_from_payload(payload):
    if isinstance(payload, ntc.Student):
        return payload

    if isinstance(payload, dict):
        student_id = payload.get("id")
        if not student_id:
            raise ValueError("Missing student id in config payload")

        student = ntc.Student(str(student_id))
        student.add1 = payload.get("add1")
        student.add2 = payload.get("add2")
        student.rem = payload.get("rem")
        student.decided = bool(payload.get("decided", any([student.add1, student.add2, student.rem])))
        return student

    raise ValueError(f"Unsupported payload type: {type(payload).__name__}")


def load_student_config(user_file):
    with open(user_file, "rb") as config_user_file:
        raw = config_user_file.read()

    try:
        return _student_from_payload(pk.loads(raw))
    except Exception:
        try:
            parsed = json.loads(raw.decode("utf-8"))
            return _student_from_payload(parsed)
        except Exception as exc:
            raise ValueError(f"Invalid config format for {user_file}") from exc

path = './'

users_config = []
# r=root, d=directories, f = files
for r, d, f in os.walk(path):
    for file in f:
        if 'user_' in file:
            users_config.append(os.path.join(r, file))

students = []

for user_file in users_config:
    try:
        students.append(load_student_config(user_file))
    except ValueError as exc:
        print(f"Skipping {user_file}: {exc}")


with open('Users.txt') as f:
    data = f.read()
    Users = json.loads(data)
    f.close()

with open('Metadata.txt') as f:
    data = f.read()
    Metadata = json.loads(data)
    f.close()

graph_path = "Graph_Round"+str(Metadata["Round"])+".txt"

Game = ntc.Networks_Game(Users.keys(), graph_path, Round = Metadata["Round"])

Game.apply_changes(students)

print(list(Game.graph.edges))

Game.save_network("Graph_Round"+str(Game.round)+".txt")


for config_file in users_config:
    os.remove(config_file)
    

Metadata["Round"] = Game.round

with open('Metadata.txt', 'w') as fp:
    json.dump(Metadata, fp)
    fp.close()

import csv
import os

log_filename = 'log_changes.csv'
log_exists = os.path.exists(log_filename)

with open(log_filename, mode='a', newline='', encoding='utf-8') as logfile:
    logwriter = csv.writer(logfile)

    # Si el archivo es nuevo, escribe los encabezados
    if not log_exists:
        logwriter.writerow(['Round', 'UserID', 'Add1', 'Add2', 'Removed', 'Randomized'])

    for student in students:
        logwriter.writerow([
            Game.round,                              # Ronda actual
            student.id,                              # ID Usuario
            student.add1 if student.add1 else '',    # Conexión añadida 1
            student.add2 if student.add2 else '',    # Conexión añadida 2
            student.rem if student.rem else '',      # Conexión removida
            False                                    # No aleatorizado
        ])

    # Registro usuarios aleatorizados (usa conexiones reales del grafo)
    missing_students = [x for x in Game.students if Game.pending_changes[x]]

    for ID in missing_students:
        # Obtener las conexiones efectivamente asignadas en el grafo actual
        current_connections = set(Game.graph.successors(ID))

        # Las conexiones previas se leen desde el grafo anterior (antes de cambios)
        graph_path_prev = "Graph_Round" + str(Game.round - 1) + ".txt"
        graph_prev = nx.DiGraph()
        if os.path.exists(graph_path_prev) and os.path.getsize(graph_path_prev) > 0:
            graph_prev = nx.read_edgelist(graph_path_prev, create_using=nx.DiGraph())
        if ID in graph_prev:
            previous_connections = set(graph_prev.successors(ID))
        else:
            previous_connections = set()


        # Los nuevos enlaces asignados aleatoriamente son:
        new_connections = current_connections - previous_connections
        removed_connections = previous_connections - current_connections

        new_connections = list(new_connections)
        removed_connections = list(removed_connections)

        add1 = new_connections[0] if len(new_connections) >= 1 else ''
        add2 = new_connections[1] if len(new_connections) >= 2 else ''
        rem = removed_connections[0] if len(removed_connections) >= 1 else ''

        logwriter.writerow([
            Game.round,  # Ronda actual
            ID,          # ID Usuario
            add1,        # Aleatorio añadido 1
            add2,        # Aleatorio añadido 2
            rem,         # Aleatorio removido
            True         # Aleatorizado
        ])

