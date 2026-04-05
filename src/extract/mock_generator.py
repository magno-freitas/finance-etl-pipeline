import pandas as pd
import random
import os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')

def generate_messy_financial_data(num_rows=50):
    """Generates mock financial data with typical real-world messiness."""
    data = []
    
    # Intentionally add some blank rows or garbage rows to simulate messy Excel
    for _ in range(num_rows):
        is_messy = random.choice([True, False, False, False]) # 25% chance of being messy
        
        if is_messy:
            # Add a row with formatting issues or missing data
            row = {
                "Data Pgto": fake.date_between(start_date="-30d", end_date="today").strftime("%d/%m/%Y") if random.choice([True, False]) else None,
                "Descrição Cliente": fake.company(),
                "Valor(BRL)": f"R$ {random.uniform(100, 5000):.2f}".replace('.', ',') if random.choice([True, False]) else None,
                "Status Sistema": random.choice(["Pago", "Pendente", "Cancelado", "PAGO", " pendente", np.nan if 'np' in globals() else None]),
                "OBS": fake.text(max_nb_chars=20)
            }
        else:
            # Clean row
            date_val = fake.date_between(start_date="-30d", end_date="today")
            row = {
                "Data Pgto": date_val.strftime("%Y-%m-%d"), # Different format to test cleaning
                "Descrição Cliente": fake.company(),
                "Valor(BRL)": random.uniform(100, 5000),
                "Status Sistema": random.choice(["Pago", "Pendente", "Cancelado"]),
                "OBS": ""
            }
        data.append(row)
        
    df = pd.DataFrame(data)
    
    # Add a few completely empty rows
    for _ in range(3):
        df.loc[len(df)] = [None, None, None, None, None]
        
    # Shuffle
    df = df.sample(frac=1).reset_index(drop=True)
    return df

def create_mock_excel_cluster(output_dir="data/raw", num_files=3):
    """Creates multiple messy Excel files in the raw data directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating {num_files} messy Excel files into {output_dir}...")
    
    file_paths = []
    for i in range(num_files):
        df = generate_messy_financial_data(random.randint(20, 100))
        
        # Simulate different namings sent by the user (Wagner)
        date_str = datetime.now().strftime("%Y%m%d")
        filenames = [
            f"Relatorio_Fin_{date_str}_{i}.xlsx",
            f"base_wagner_v{i}_final.xlsx",
            f"financeiro_fechamento_pt{i}.xlsx"
        ]
        
        filepath = os.path.join(output_dir, random.choice(filenames))
        
        # Excel saving with potential formatting caveats
        df.to_excel(filepath, index=False)
        file_paths.append(filepath)
        print(f"Created: {filepath}")
        
    return file_paths

if __name__ == "__main__":
    create_mock_excel_cluster()
