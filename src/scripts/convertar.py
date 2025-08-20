import pandas as pd
import os

for file in os.listdir(os.getcwd()):
    if file.endswith('.txt'):
        input_file = file
        output_file = f'data/{file.split('.')[0]}.csv'

        with open(input_file, 'r', encoding='windows-1256', errors='replace') as f:
            df = pd.read_csv(f)

        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        os.remove(input_file)
