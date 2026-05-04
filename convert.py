import pandas as pd

FILE_NAME = ['initial_model','final_model']

def convert(filename):
    pickle_file = f'{filename}.pkl'
    csv_file = f'{filename}.csv'
    df = pd.read_pickle(pickle_file)
    df = pd.DataFrame(df)
    df.to_csv(csv_file, index=False)

for file in FILE_NAME:
    convert(file)