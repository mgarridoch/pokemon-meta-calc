import pandas as pd

# Create function that receives a number that CAN be NaN, or any number.
# It turns the number from string to float, but it also handles numbers with commas as "0,5" instead of "0.5"
def parse_number(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.replace(',', '.')
    return float(value)

def rank_pokemon_meta(csv_file_path):
    """
    Carga un CSV de Pokémon y calcula un "ranking de meta" basado en
    ventajas y desventajas de tipo contra todos los demás en la lista.
    """
    
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{csv_file_path}'")
        return

    # Asegurarnos de que los nombres de las columnas de tipo están limpios
    # (Tu hoja ya debería tener 'bug', 'dark', etc. como nombres de columna)
    type_columns = [
        'bug', 'dark', 'dragon', 'electric', 'fairy', 'fighting', 'fire', 
        'flying', 'ghost', 'grass', 'ground', 'ice', 'normal', 'poison', 
        'psychic', 'rock', 'steel', 'water'
    ]
    
    # Filtra el DataFrame para quedarnos solo con los Pokémon de tu lista.
    # Por ahora, asumiremos que *todo* el CSV es tu lista.
    pokemon_list_df = df.copy()

    # Un diccionario para guardar la puntuación de cada Pokémon
    meta_scores = {}

    # --- El Corazón del Algoritmo ---
    # Itera por cada Pokémon (Pokémon A)
    for index_A, row_A in pokemon_list_df.iterrows():
        pokemon_A_name = row_A['name']
        type1_A = row_A['type1']
        type2_A = row_A['type2'] # Puede ser NaN (vacío)
        
        # Este es el perfil defensivo de A (ej: {'bug': 1, 'dark': 1, 'fire': 2, ...})
        defensive_profile_A = row_A[type_columns]
        
        current_score = 0

        # Itera por cada *oponente* (Pokémon B)
        for index_B, row_B in pokemon_list_df.iterrows():
            
            # No te compares contigo mismo
            if index_A == index_B:
                continue

            type1_B = row_B['type1']
            type2_B = row_B['type2']
            
            # Este es el perfil defensivo de B
            defensive_profile_B = row_B[type_columns]

            # --- 1. CÁLCULO OFENSIVO (A ataca a B) ---
            # Revisa el mejor multiplicador que A tiene contra B
            
            # Multiplicador del Tipo 1 de A contra B
            off_mult_1 = parse_number(defensive_profile_B[type1_A] )
            
            # Multiplicador del Tipo 2 de A contra B
            off_mult_2 = 1.0 # Asume 1 si no hay tipo 2
            if pd.notna(type2_A):
                off_mult_2 = parse_number(defensive_profile_B[type2_A])
                
            best_offense = max(off_mult_1, off_mult_2)

            if best_offense >= 2:
                current_score += 1  # +1 si A es súper-efectivo contra B
            elif best_offense <= 0.5:
                current_score -= 1  # -1 si A es resistido por B

            # --- 2. CÁLCULO DEFENSIVO (B ataca a A) ---
            # Revisa la peor debilidad que A tiene contra B
            
            # Multiplicador del Tipo 1 de B contra A
            def_mult_1 = parse_number(defensive_profile_A[type1_B])
            
            # Multiplicador del Tipo 2 de B contra A
            def_mult_2 = 1.0 # Asume 1 si no hay tipo 2
            if pd.notna(type2_B):
                def_mult_2 = parse_number(defensive_profile_A[type2_B])
            
            worst_weakness = max(def_mult_1, def_mult_2)
            
            if worst_weakness >= 2:
                current_score -= 1  # -1 si A es débil contra B
            elif worst_weakness <= 0.5:
                current_score += 1  # +1 si A resiste a B

        # Guarda la puntuación final de Pokémon A
        meta_scores[pokemon_A_name] = current_score

    # --- 3. RESULTADOS ---
    # Convierte el diccionario de puntuaciones en un DataFrame de Pandas
    ranked_df = pd.DataFrame(meta_scores.items(), columns=['Pokemon', 'Meta_Score'])
    
    # Ordena de mejor a peor
    ranked_df = ranked_df.sort_values(by='Meta_Score', ascending=False)
    
    return ranked_df

# --- EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    
    # Asegúrate de que este es el nombre de tu archivo
    ranking = rank_pokemon_meta("pokemon_db.csv") 
    
    if ranking is not None:
        print("--- Ranking de Poder del Metagame ---")
        print(ranking)
        
        print("\n--- Top 6 Pokémon Sugeridos (Individualmente) ---")
        print(ranking.head(6))