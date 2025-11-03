import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def optimize_pokemon_team(matchups_csv_path, team_size=3):
    """
    Usa Gurobi para encontrar el equipo de Pokémon de tamaño 'team_size'
    que maximiza la cobertura del metagame.
    """
    
    # --- 1. Cargar y Preparar los Datos ---
    try:
        df = pd.read_csv(matchups_csv_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{matchups_csv_path}'")
        return

    # Obtener la lista de todos los Pokémon únicos
    pokemon_list = list(df['Pokemon_A'].unique())
    
    # Crear un diccionario con los scores (i, j) -> score
    # Esto es 's_ij' en nuestro modelo: el score de Pokémon 'i' vs 'j'
    scores = {}
    for row in df.itertuples():
        scores[(row.Pokemon_A, row.Pokemon_B)] = row.Matchup_Score

    print(f"Optimizando un equipo de {team_size} de un pool de {len(pokemon_list)} Pokémon.")

    # --- 2. Configurar el Modelo Gurobi ---
    m = gp.Model("PokemonTeamOptimizer")

    m.setParam('TimeLimit', 300) # Limitar a segundos

    # Un valor "infinito negativo" para matchups de Pokémon no seleccionados
    M_NEG = -1000.0 

    # --- 3. Crear Variables de Decisión ---
    
    # x[i]: Variable binaria, 1 si elegimos Pokémon 'i', 0 si no.
    x = m.addVars(pokemon_list, vtype=GRB.BINARY, name="x")
    
    # y[j]: Variable continua, representará el MEJOR score que nuestro
    #       equipo tiene contra el oponente 'j'.
    y = m.addVars(pokemon_list, vtype=GRB.CONTINUOUS, lb=M_NEG, name="y")
    
    # z[i, j]: Variable continua, representa el score "efectivo" de
    #          nuestro Pokémon 'i' contra el oponente 'j'.
    #          Será 'scores[i, j]' si x[i]=1, o M_NEG si x[i]=0.
    z = m.addVars(pokemon_list, pokemon_list, vtype=GRB.CONTINUOUS, lb=M_NEG, name="z")

    # --- 4. Definir las Restricciones ---
    
    # Restricción 1: El tamaño del equipo debe ser exactamente 'team_size'
    m.addConstr(gp.quicksum(x[i] for i in pokemon_list) == team_size, "TeamSize")

    # Restricción 2: No podemos elegir a Oshawott.
    m.addConstr(x['Oshawott'] == 0, "No_Oshawott")
    
    # Restricción 3: No podemos elegir a Snivy.
    m.addConstr(x['Snivy'] == 0, "No_Snivy")

    # Restricción X: Obligar a incluir a pokemon Apokemon en el equipo
    # m.addConstr(x['Apokemon'] == 1, "Must_Have_Apokemon")

    # Restricciones 2 y 3 (El corazón del modelo):
    # Ligar 'x' con 'z' y 'z' con 'y'
    
    for j in pokemon_list: # Para cada oponente 'j'
        z_list_for_j = []
        for i in pokemon_list: # Para cada miembro potencial del equipo 'i'
            
            s_ij = scores.get((i, j), 0) # Score de i vs j
            
            # Restricción 2: Constraints 'Indicador'
            # Si x[i] = 1 (elegido), entonces z[i, j] = s_ij
            m.addGenConstrIndicator(x[i], 1, z[i, j] == s_ij, name=f"z_on_{i}_{j}")
            # Si x[i] = 0 (no elegido), entonces z[i, j] = M_NEG
            m.addGenConstrIndicator(x[i], 0, z[i, j] == M_NEG, name=f"z_off_{i}_{j}")
            
            z_list_for_j.append(z[i, j])
            
        # Restricción 3: Constraint 'Max'
        # y[j] (score vs oponente j) debe ser el MÁXIMO de todos 
        # los scores efectivos (z) de nuestro equipo contra él.
        m.addGenConstrMax(y[j], z_list_for_j, name=f"y_max_{j}")

    # --- 5. Definir la Función Objetivo ---
    # Maximizar la suma de los "mejores" scores contra cada oponente
    m.setObjective(gp.quicksum(y[j] for j in pokemon_list), GRB.MAXIMIZE)

    # --- 6. Resolver la Optimización ---
    print("\nIniciando optimización con Gurobi...")
    m.optimize()

# --- 7. Mostrar Resultados (CORREGIDO) ---
    
    # m.SolCount > 0 significa que Gurobi encontró al menos UNA solución válida
    if m.SolCount > 0:
        print("\n--- ¡Optimización completada! ---")
        
        # Informar por qué se detuvo
        if m.status == GRB.OPTIMAL:
            print("Se encontró la solución ÓPTIMA (comprobada).")
        elif m.status == GRB.TIME_LIMIT:
            print("Se alcanzó el límite de tiempo. Mostrando la mejor solución encontrada.")
        else:
            print(f"Detenido con estado: {m.status}")

        print(f"Puntuación Total de Cobertura del Equipo: {m.ObjVal:.2f}")
        print(f"\nEl mejor equipo de {team_size} encontrado es:")
        
        team = []
        for i in pokemon_list:
            if x[i].X > 0.5: # Si la variable binaria es 1
                team.append(i)
                print(f"  - {i}")
        return team
        
    else:
        print("No se encontró ninguna solución válida que cumpla las restricciones.")
        return None
# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    
    # Nombre del archivo que generamos en el paso anterior
    matchups_file = "all_matchups.csv" 
    
    # ¡Cambiamos a 3!
    optimal_team = optimize_pokemon_team(matchups_file, team_size=3)