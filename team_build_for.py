import pandas as pd
import gurobipy as gp
from gurobipy import GRB

def optimize_pokemon_team(matchups_csv_path, team_size=3, num_solutions_to_find=5):
    """
    Usa Gurobi para encontrar el equipo de Pokémon de tamaño 'team_size'
    que maximiza la cobertura del metagame.
    
    Esta versión busca iterativamente 'num_solutions_to_find' equipos
    añadiendo "cortes" (restricciones) después de cada solución.
    """
    
    # --- 1. Cargar y Preparar los Datos ---
    try:
        df = pd.read_csv(matchups_csv_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{matchups_csv_path}'")
        return

    pokemon_list = list(df['Pokemon_A'].unique())
    scores = {}
    for row in df.itertuples():
        scores[(row.Pokemon_A, row.Pokemon_B)] = row.Matchup_Score

    print(f"Optimizando un equipo de {team_size} de un pool de {len(pokemon_list)} Pokémon.")

    # --- 2. Configurar el Modelo Gurobi ---
    m = gp.Model("PokemonTeamOptimizer")
    
    # NOTA: Este TimeLimit se aplicará a CADA búsqueda.
    # 5 soluciones * 50s = 250s (4 min 10 seg) en total como máximo.
    m.setParam('TimeLimit', 50)

    M_NEG = -1000.0 

    # --- 3. Crear Variables de Decisión ---
    x = m.addVars(pokemon_list, vtype=GRB.BINARY, name="x")
    y = m.addVars(pokemon_list, vtype=GRB.CONTINUOUS, lb=M_NEG, name="y")
    z = m.addVars(pokemon_list, pokemon_list, vtype=GRB.CONTINUOUS, lb=M_NEG, name="z")

    # --- 4. Definir las Restricciones ---
    m.addConstr(gp.quicksum(x[i] for i in pokemon_list) == team_size, "TeamSize")
    m.addConstr(x['Oshawott'] == 0, "No_Oshawott")
    m.addConstr(x['Snivy'] == 0, "No_Snivy")

    for j in pokemon_list:
        z_list_for_j = []
        for i in pokemon_list:
            s_ij = scores.get((i, j), 0)
            m.addGenConstrIndicator(x[i], 1, z[i, j] == s_ij, name=f"z_on_{i}_{j}")
            m.addGenConstrIndicator(x[i], 0, z[i, j] == M_NEG, name=f"z_off_{i}_{j}")
            z_list_for_j.append(z[i, j])
        m.addGenConstrMax(y[j], z_list_for_j, name=f"y_max_{j}")

    # --- 5. Definir la Función Objetivo ---
    m.setObjective(gp.quicksum(y[j] for j in pokemon_list), GRB.MAXIMIZE)

    # --- 6. y 7. Resolver Iterativamente y Mostrar Resultados ---
    
    print(f"\nIniciando búsqueda iterativa para {num_solutions_to_find} equipos...")
    
    all_teams_found = []
    
    for sol_num in range(num_solutions_to_find):
        print(f"\n--- Buscando Equipo #{sol_num + 1} ---")
        
        m.optimize() # Resolver el modelo
        
        # Verificar si se encontró una solución en esta iteración
        if m.SolCount > 0:
            print("\n¡Solución encontrada!")
            
            # Informar por qué se detuvo
            if m.status == GRB.OPTIMAL:
                print("Se encontró la solución ÓPTIMA (comprobada) para esta iteración.")
            elif m.status == GRB.TIME_LIMIT:
                print("Se alcanzó el límite de tiempo. Mostrando la mejor solución encontrada.")
            else:
                print(f"Detenido con estado: {m.status}")

            print(f"Puntuación Total de Cobertura: {m.ObjVal:.2f}")
            print(f"El equipo encontrado es:")
            
            current_team = []
            for i in pokemon_list:
                if x[i].X > 0.5: # Si la variable binaria es 1
                    current_team.append(i)
                    print(f"   - {i}")
            
            all_teams_found.append(current_team)
            
            # --- LA MAGIA: Añadir la restricción de "corte" ---
            # Obtenemos las variables 'x' de los Pokémon en el equipo actual
            team_vars = [x[p_name] for p_name in current_team]
            
            # Añadimos una restricción que dice:
            # "La suma de estas 3 variables no puede ser 3 de nuevo"
            # O, lo que es lo mismo: "debe ser 2 o menos"
            m.addConstr(gp.quicksum(team_vars) <= team_size - 1, f"cut_solution_{sol_num}")

        else:
            # Si Gurobi no encuentra más soluciones, es porque ya no hay
            # más combinaciones válidas que cumplan las restricciones.
            print("\nNo se encontraron más soluciones válidas.")
            break # Salir del bucle 'for'
            
    return all_teams_found

# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    
    matchups_file = "all_matchups.csv" 
    
    # ¡Llamamos a la función pidiendo 5 equipos!
    optimal_teams = optimize_pokemon_team(matchups_file, team_size=3, num_solutions_to_find=5)
    
    print("\n--- Búsqueda Iterativa Finalizada ---")
    print(f"Se encontraron un total de {len(optimal_teams)} equipos.")