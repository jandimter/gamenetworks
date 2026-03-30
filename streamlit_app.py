# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 10:28:14 2021

@author: jesal
"""


import streamlit as st
import networkclass as ntc
import json
import pickle as pk
import os
import glob
import re
from io import BytesIO
import zipfile
import subprocess


def load_users():
    with open("Users.txt") as f:
        return json.loads(f.read())


def load_admins():
    if not os.path.exists("Admins.txt"):
        return {"admin": "admin"}
    try:
        with open("Admins.txt") as f:
            return json.loads(f.read())
    except Exception:
        return {"admin": "admin"}


def load_aliases(user_ids):
    default_aliases = {user_id: user_id for user_id in user_ids}

    if not os.path.exists("Aliases.txt"):
        return default_aliases

    try:
        with open("Aliases.txt") as f:
            aliases_from_file = json.loads(f.read())
    except Exception:
        return default_aliases

    for user_id in user_ids:
        alias = aliases_from_file.get(user_id)
        if isinstance(alias, str) and alias.strip():
            default_aliases[user_id] = alias.strip()

    return default_aliases


def build_rankings(game):
    has_edges_current_round = game.graph.number_of_edges() > 0

    nodes_stats = []
    for node in game.graph.nodes:
        attrs = game.graph.nodes[node]
        nodes_stats.append(
            {
                "User": node,
                "Alias": game.aliases.get(node, node),
                "Indegree": attrs.get("indegree", 0),
                "Clustering": round(attrs.get("clustering", 0), 4),
                "Betweenness": round(attrs.get("BTC", 0), 4),
            }
        )

    metric_configs = [
        ("Indegree", True),
        ("Clustering", True),
        ("Betweenness", True),
    ]

    per_metric_rank = {entry[0]: {} for entry in metric_configs}

    if has_edges_current_round:
        for metric, descending in metric_configs:
            ordered = sorted(nodes_stats, key=lambda x: (-x[metric], x["User"]) if descending else (x[metric], x["User"]))
            for idx, item in enumerate(ordered, start=1):
                per_metric_rank[metric][item["User"]] = idx

    previous_round_rank = None
    previous_round = game.round - 1
    previous_round_file = f"Graph_Round{previous_round}.txt"

    if previous_round >= 0 and os.path.exists(previous_round_file):
        prev_game = ntc.Networks_Game(game.students, previous_round_file, previous_round, aliases=game.aliases)
        has_edges_previous_round = prev_game.graph.number_of_edges() > 0

        if has_edges_previous_round:
            prev_game.compute_ranking()

            prev_nodes_stats = []
            for node in prev_game.graph.nodes:
                prev_attrs = prev_game.graph.nodes[node]
                prev_nodes_stats.append(
                    {
                        "User": node,
                        "Indegree": prev_attrs.get("indegree", 0),
                        "Clustering": round(prev_attrs.get("clustering", 0), 4),
                        "Betweenness": round(prev_attrs.get("BTC", 0), 4),
                    }
                )

            previous_round_rank = {entry[0]: {} for entry in metric_configs}
            for metric, descending in metric_configs:
                ordered_prev = sorted(
                    prev_nodes_stats,
                    key=lambda x: (-x[metric], x["User"]) if descending else (x[metric], x["User"]),
                )
                for idx, item in enumerate(ordered_prev, start=1):
                    previous_round_rank[metric][item["User"]] = idx

    rankings = []
    for item in nodes_stats:
        row = {
            "Alias": item["Alias"],
            "User": item["User"],
            "Indegree": item["Indegree"],
            "Clustering": item["Clustering"],
            "Betweenness": item["Betweenness"],
            "Rank Indegree": per_metric_rank["Indegree"].get(item["User"], "—"),
            "Rank Clustering": per_metric_rank["Clustering"].get(item["User"], "—"),
            "Rank Betweenness": per_metric_rank["Betweenness"].get(item["User"], "—"),
        }

        for metric_name in ["Indegree", "Clustering", "Betweenness"]:
            delta_key = f"Δ {metric_name}"
            if (
                not has_edges_current_round
                or previous_round_rank is None
                or item["User"] not in previous_round_rank[metric_name]
                or item["User"] not in per_metric_rank[metric_name]
            ):
                row[delta_key] = "—"
            else:
                delta = previous_round_rank[metric_name][item["User"]] - per_metric_rank[metric_name][item["User"]]
                if delta > 0:
                    row[delta_key] = f"↑ {delta}"
                elif delta < 0:
                    row[delta_key] = f"↓ {abs(delta)}"
                else:
                    row[delta_key] = "= 0"

        rankings.append(row)

    return sorted(rankings, key=lambda x: (-x["Indegree"], x["User"]))

def check_identity(ID, PASSWORD):
    admins = load_admins()
    users = load_users()

    if ID in admins and admins[ID] == PASSWORD:
        return True, "admin", list(users.keys())

    if ID in users and users[ID] == PASSWORD:
        return True, "user", list(users.keys())

    if ID in admins or ID in users:
        st.error("Wrong Password")
    else:
        st.error("Wrong ID")

    return False, None, None

def Init_Game(ID_List, Round):
    aliases = load_aliases(ID_List)
    Game = ntc.Networks_Game(ID_List, "Graph_Round"+str(Round)+".txt", Round, aliases=aliases)
    return Game

def Log_in():
    
    placeholder = st.container()

    with placeholder:
            "Introduce your user id and password:"
            
            USER_ID = st.text_input("Enter your student ID", "", 18,"USER_ID")
            
            PASSWORD = st.text_input("Enter your password", "", 18,"PASSWORD", type = "password")
            
            LOGIN = st.button("ENTER", "Login_Button")
            
            if LOGIN:
                attempt, role, ID_List = check_identity(USER_ID, PASSWORD)
                if attempt:
                    st.success("Log in successful")
                    st.session_state.LogedIn = True
                    st.session_state.IsAdmin = (role == "admin")
                    with open('Metadata.txt') as f:
                        data = f.read()
                        Metadata = json.loads(data)
                        f.close()
                    st.session_state.Game = Init_Game(ID_List, Round = Metadata["Round"])
                    if st.session_state.IsAdmin:
                        st.session_state.AdminID = USER_ID
                    else:
                        try:
                             with open('user_'+USER_ID+".config", 'rb') as config_user_file:
     
                                 # Step 3
                                 st.session_state.User = pk.load(config_user_file)
                                 config_user_file.close()
                        except:
                            st.session_state.User = ntc.Student(USER_ID)
                    placeholder.empty()
                    st.rerun()
                else:
                    st.error("Log in failed")


def Admin_dashboard():
    st.title("Panel de administración")

    metadata = {"Round": st.session_state.Game.round}
    if os.path.exists("Metadata.txt"):
        with open("Metadata.txt") as f:
            metadata = json.loads(f.read())

    users = load_users()
    aliases = st.session_state.Game.aliases
    submitted_files = glob.glob("user_*.config")
    submitted_ids = sorted(
        [os.path.basename(path).replace("user_", "").replace(".config", "") for path in submitted_files]
    )

    total_users = len(users)
    submitted_count = len([user_id for user_id in submitted_ids if user_id in users])
    pending_count = max(total_users - submitted_count, 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ronda actual", metadata.get("Round", 0))
    c2.metric("Respuestas recibidas", submitted_count)
    c3.metric("Usuarios pendientes", pending_count)

    st.subheader("Estado de participación")
    status_rows = []
    for user_id in sorted(users.keys()):
        status_rows.append(
            {
                "Alias": aliases.get(user_id, user_id),
                "User ID": user_id,
                "Estado": "Enviado" if user_id in submitted_ids else "Pendiente",
            }
        )

    st.dataframe(status_rows, use_container_width=True, hide_index=True)

    st.subheader("Control de ronda")
    st.caption("Ejecuta el cierre de ronda y genera el siguiente archivo de red.")
    if st.button("Run round", key="run_round_admin"):
        with st.spinner("Ejecutando cierre de ronda..."):
            result = subprocess.run(
                ["python", "Run_Round.py"],
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            st.success("Ronda ejecutada correctamente.")
            if result.stdout.strip():
                st.code(result.stdout.strip())
            with open("Metadata.txt") as f:
                metadata = json.loads(f.read())
            st.session_state.Game = Init_Game(list(users.keys()), Round=metadata["Round"])
            st.session_state.pop("RANK_DONE", None)
            st.rerun()
        else:
            st.error("No se pudo ejecutar la ronda.")
            if result.stderr.strip():
                st.code(result.stderr.strip())
            elif result.stdout.strip():
                st.code(result.stdout.strip())
                    
def Changes_screen():
    Round = st.session_state["Game"].round
    st.title("Game of Networks Round: " + str(Round))
    alias_map = st.session_state.Game.aliases

    def alias_label(user_id):
        alias = alias_map.get(user_id, user_id)
        if alias != user_id and list(alias_map.values()).count(alias) > 1:
            return f"{alias} ({user_id})"
        return alias

    def to_alias_options(user_ids):
        return [alias_label(user_id) for user_id in user_ids]

    def alias_to_user_map(user_ids):
        return {alias_label(user_id): user_id for user_id in user_ids}
    
    if Round == 0:
        with st.form("NewConnections"):
            Available = st.session_state.Game.unconnectedOF(st.session_state.User.id)
            available_aliases = ["-- No change --"] + to_alias_options(Available)
            available_alias_lookup = alias_to_user_map(Available)
            "Choose 2 connections to add"
            "Connection 1"
            add1 = st.selectbox(
                "Add this connection",
                available_aliases,
                key="add1",
            )
            "Connection 2"
            add2 = st.selectbox(
                "Add this connection",
                available_aliases,
                key="add2",
            )
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                add1_user = available_alias_lookup.get(add1)
                add2_user = available_alias_lookup.get(add2)
                
                SUBMISSION, MESSAGE = st.session_state.Game.new_change(st.session_state.User, add1_user, add2_user)
                
                if SUBMISSION:
                    st.success(MESSAGE)
                    with open('user_'+st.session_state.User.id+".config", 'wb') as config_user_file:
 
                        # Step 3
                        pk.dump(st.session_state.User, config_user_file)
                        config_user_file.close()
                    st.empty()
                else:
                    st.error(MESSAGE)
                    
            
                    
    else:
        with st.form("NewConnections"):
            Available = st.session_state.Game.unconnectedOF(st.session_state.User.id)
            Connected = st.session_state.Game.connectionsOF(st.session_state.User.id)
            available_aliases = ["-- No change --"] + to_alias_options(Available)
            connected_aliases = ["-- No change --"] + to_alias_options(Connected)
            available_alias_lookup = alias_to_user_map(Available)
            connected_alias_lookup = alias_to_user_map(Connected)
            "Choose 2 connections to add"
            "Connection 1"
            add1 = st.selectbox(
                "Add this connection",
                available_aliases,
                key="add1",
            )
            "Connection 2"
            add2 = st.selectbox(
                "Add this connection",
                available_aliases,
                key="add2",
            )
            "Remove Connection"
            rem = st.selectbox(
                "Remove this connection",
                connected_aliases,
                key="rem",
            )
            submitted = st.form_submit_button("Submit")
                
            if submitted:
                add1_user = available_alias_lookup.get(add1)
                add2_user = available_alias_lookup.get(add2)
                rem_user = connected_alias_lookup.get(rem)
                
                SUBMISSION, MESSAGE = st.session_state.Game.new_change(
                    st.session_state.User, add1_user, add2_user, rem_user
                )
                
                if SUBMISSION:
                    st.success(MESSAGE)
                    with open('user_'+st.session_state.User.id+".config", 'wb') as config_user_file:
 
                        # Step 3
                        pk.dump(st.session_state.User, config_user_file)
                        config_user_file.close()
                    st.empty()
                else:
                    st.error(MESSAGE)
                    
            
    reset = st.container()
    with reset:
        st.button("Reset changes", key="ResetBut")
        if st.session_state.ResetBut:
            st.session_state.User.reset_changes()
            if os.path.exists("user_"+st.session_state.User.id+".config"):
                os.remove("user_"+st.session_state.User.id+".config")
            
            st.warning("Your changes were removed.")
            
                
def Visualization():
    
    if "RANK_DONE" not in st.session_state:
        
        st.session_state.Game.compute_ranking()
        
        st.session_state.RANK_DONE = st.session_state.Game.visualize()


def Rankings_section():
    st.subheader("Ranking de usuarios por stats")
    st.caption("Ordenado por indegree. Cada stat incluye su ranking y variación respecto de la ronda anterior.")

    rankings = build_rankings(st.session_state.Game)

    st.dataframe(
        rankings,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "Alias",
            "Indegree",
            "Rank Indegree",
            "Δ Indegree",
            "Clustering",
            "Rank Clustering",
            "Δ Clustering",
            "Betweenness",
            "Rank Betweenness",
            "Δ Betweenness",
        ],
    )


def round_from_filename(path):
    match = re.search(r"Graph_Round(\d+)\.txt$", os.path.basename(path))
    if match:
        return int(match.group(1))
    return -1


def Network_downloads_section():
    st.subheader("Descarga de archivos de red")
    st.caption("Exporta las rondas para análisis y respaldo de la evolución del juego.")

    round_files = sorted(glob.glob("Graph_Round*.txt"), key=round_from_filename, reverse=True)

    if not round_files:
        st.info("No hay archivos de rondas disponibles para descargar.")
        return

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file_path in round_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))
    zip_buffer.seek(0)

    top_left, top_right = st.columns([2, 1])
    with top_left:
        st.markdown(f"**{len(round_files)} archivos disponibles**")
    with top_right:
        st.download_button(
            label="⬇️ Descargar todo (.zip)",
            data=zip_buffer.getvalue(),
            file_name="GameNetworks_Rounds.zip",
            mime="application/zip",
            key="download_all_rounds",
            use_container_width=True,
        )

    st.markdown("#### Descarga por ronda")
    for file_path in round_files:
        round_num = round_from_filename(file_path)
        with open(file_path, "rb") as f:
            content = f.read()

        file_size_kb = max(len(content) / 1024, 0.1)
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown(f"**Ronda {round_num}**")
        c2.caption(f"{file_size_kb:.1f} KB")
        c3.download_button(
            label="Descargar",
            data=content,
            file_name=os.path.basename(file_path),
            mime="text/plain",
            key=f"download_round_{round_num}",
            use_container_width=True,
        )
    

def main():
    
    st.title("Game of Networks")

    if 'LogedIn' not in st.session_state:
        st.session_state.LogedIn = False
    if 'IsAdmin' not in st.session_state:
        st.session_state.IsAdmin = False
        
        
    if st.session_state.LogedIn == False:
        Log_in()
    
    else:
        if st.session_state.IsAdmin:
            Admin_dashboard()
        else:
            Changes_screen()
        Visualization()
        with st.container():
            st.bokeh_chart(st.session_state.RANK_DONE, use_container_width=True)
        Rankings_section()
        Network_downloads_section()
        
        
            
        
main()
