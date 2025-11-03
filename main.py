import pandas as pd

# Tu función para parsear números con comas
def parse_number(value):
    if pd.isna(value):
        # Si el tipo es NaN, no podemos saber el multiplicador. 
        # Asumir 1.0 (neutral) es lo más seguro.
        return 1.0 
    if isinstance(value, str):
        value = value.replace(',', '.')
    
    # Manejar el caso de que el valor sea un string vacío o no numérico
    try:
        return float(value)
    except ValueError:
        return 1.0 # Asumir neutral si el dato es inválido

def rank_pokemon_meta(csv_file_path):
    """
    Carga un CSV de Pokémon, calcula un ranking de meta y genera un
    informe detallado de matchups.
    """
    
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{csv_file_path}'")
        return

    # Nombres de columna de tipo (con tu corrección 'fighting')
    type_columns = [
        'bug', 'dark', 'dragon', 'electric', 'fairy', 'fighting', 'fire', 
        'flying', 'ghost', 'grass', 'ground', 'ice', 'normal', 'poison', 
        'psychic', 'rock', 'steel', 'water'
    ]
    
    pokemon_list_df = df.copy()

    # --- NUEVO: Lista para guardar CADA matchup individual ---
    all_matchups_data = [] 
    
    meta_scores = {}

    # --- El Corazón del Algoritmo ---
    for index_A, row_A in pokemon_list_df.iterrows():
        pokemon_A_name = row_A['name']
        type1_A = row_A['type1']
        type2_A = row_A['type2']
        
        defensive_profile_A = row_A[type_columns]
        current_score = 0

        # Itera por cada *oponente* (Pokémon B)
        for index_B, row_B in pokemon_list_df.iterrows():
            if index_A == index_B:
                continue

            pokemon_B_name = row_B['name']
            type1_B = row_B['type1']
            type2_B = row_B['type2']
            defensive_profile_B = row_B[type_columns]

            # --- Lógica de Puntuación (Refinada) ---
            
            # 1. Puntos Ofensivos (A ataca a B)
            off_mult_1 = parse_number(defensive_profile_B.get(type1_A, 1.0))
            off_mult_2 = 1.0
            if pd.notna(type2_A):
                off_mult_2 = parse_number(defensive_profile_B.get(type2_A, 1.0))
            best_offense = max(off_mult_1, off_mult_2)
            
            offensive_points = 0
            if best_offense >= 2:
                offensive_points = 1
            elif best_offense <= 0.5:
                offensive_points = -1

            # 2. Puntos Defensivos (B ataca a A)
            def_mult_1 = parse_number(defensive_profile_A.get(type1_B, 1.0))
            def_mult_2 = 1.0
            if pd.notna(type2_B):
                def_mult_2 = parse_number(defensive_profile_A.get(type2_B, 1.0))
            worst_weakness = max(def_mult_1, def_mult_2)

            defensive_points = 0
            if worst_weakness >= 2:
                defensive_points = -1
            elif worst_weakness <= 0.5:
                defensive_points = 1

            # --- NUEVO: Calcular y guardar el score de este matchup ---
            # Puntuación final del matchup A vs B
            individual_score = offensive_points + defensive_points
            
            all_matchups_data.append({
                'Pokemon_A': pokemon_A_name,
                'Pokemon_B': pokemon_B_name,
                'Matchup_Score': individual_score
            })

            # Añadir al meta-score total de Pokémon A
            current_score += individual_score

        meta_scores[pokemon_A_name] = current_score

    # --- 3. RESULTADOS (Ranking Principal) ---
    ranked_df = pd.DataFrame(meta_scores.items(), columns=['Pokemon', 'Meta_Score'])
    ranked_df = ranked_df.sort_values(by='Meta_Score', ascending=False)
    
    # --- NUEVO: 4. PROCESAR Y GUARDAR MATCHUPS ---
    
    # Convertir la lista de matchups en un DataFrame
    matchups_df = pd.DataFrame(all_matchups_data)
    
    # Guardar el CSV con todos los datos en crudo
    try:
        matchups_df.to_csv("all_matchups.csv", index=False, encoding='utf-8')
        print("\nArchivo 'all_matchups.csv' guardado con éxito.")
    except Exception as e:
        print(f"Error al guardar 'all_matchups.csv': {e}")

    # --- NUEVO: 5. GENERAR INFORME DE ANÁLISIS .TXT ---
    
    try:
        with open("matchup_analysis.txt", "w", encoding='utf-8') as f:
            f.write("--- ANÁLISIS DE MATCHUPS DEL METAGAME ---\n")
            f.write("Generado basado en el ranking de Meta Score.\n")
            f.write("Matchup Score = (Puntos Ofensivos + Puntos Defensivos)\n")
            f.write("==================================================\n")

            # Iterar por el ranking principal (ordenado por Meta Score)
            for index, row in ranked_df.iterrows():
                pokemon_name = row['Pokemon']
                meta_score = row['Meta_Score']
                
                f.write(f"\n# {index + 1}. {pokemon_name.upper()} (Meta Score: {meta_score})\n")
                
                # Filtrar todos los matchups de este Pokémon
                pokemon_matchups = matchups_df[matchups_df['Pokemon_A'] == pokemon_name]
                
                # Obtener Top 5 Mejores Matchups
                top_5 = pokemon_matchups.sort_values(by='Matchup_Score', ascending=False).head(5)
                f.write("  [+] Mejores 5 Matchups:\n")
                for _, matchup in top_5.iterrows():
                    f.write(f"      vs {matchup['Pokemon_B']:<15} (Score: {matchup['Matchup_Score']})\n")
                    
                # Obtener Top 5 Peores Matchups
                worst_5 = pokemon_matchups.sort_values(by='Matchup_Score', ascending=True).head(5)
                f.write("  [-] Peores 5 Matchups:\n")
                for _, matchup in worst_5.iterrows():
                    f.write(f"      vs {matchup['Pokemon_B']:<15} (Score: {matchup['Matchup_Score']})\n")
        
        print("Archivo 'matchup_analysis.txt' guardado con éxito.")

    except Exception as e:
        print(f"Error al guardar 'matchup_analysis.txt': {e}")

    return ranked_df

# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    
    ranking = rank_pokemon_meta("pokemon_db.csv") 
    
    if ranking is not None:
        print("\n--- Ranking de Poder del Metagame ---")
        print(ranking)
        
        print("\n--- Top 6 Pokémon Sugeridos (Individualmente) ---")
        print(ranking.head(6))