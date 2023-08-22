
import pandas as pd
import hashlib

def reorganize_dataframe(df):
    """Reorganiza el DataFrame para que sea más fácil de trabajar con él."""
    data = []
    for index, row in df.iterrows():
        for i in range(1, 13):
            data.append({
                'Nombre': row['Nombre'],
                'Pregunta': row[f'Q{i}'],
                'Respuesta': row[f'A{i}']
            })
    new_df = pd.DataFrame(data)
    new_df['ID'] = new_df['Pregunta'].apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
    new_df.set_index(['Nombre', 'Pregunta'], inplace=True)
    return new_df
