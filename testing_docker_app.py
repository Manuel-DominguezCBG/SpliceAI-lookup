import pandas as pd
import requests
import json
import numpy as np  # Import NumPy for NaN

df = pd.read_csv("./spliceai_control.csv")

columns_to_convert = ['DS_AG-CONTROL', 'DS_AL-CONTROL', 'DS_DG-CONTROL', 'DS_DL-CONTROL', 'DP_AG-CONTROL']
df[columns_to_convert] = df[columns_to_convert].astype(float)

print(df)


# Add new columns for storing the filtered values
columns_to_add = ['DS_AG', 'DS_AL', 'DS_DG', 'DS_DL', 'DP_AG', 'DP_AL', 'DP_DG', 'DP_DL']
for col in columns_to_add:
    df[col] = None  # Initialize with None or any default value you'd like


# Function to compare individual columns
def compare_single_column(row, control_col, test_col):
    return row[control_col] == row[test_col]

# Function to perform custom comparison (when there are Nan involve)
def custom_compare(row, col1, col2):
    val1, val2 = row[col1], row[col2]
    if pd.isna(val1) and pd.isna(val2):
        return True
    return val1 == val2


for index, row in df.iterrows():
    chr_value = row['Chr']
    pos_value = row['Pos']
    ref_value = row['Ref']
    alt_value = row['Alt']

    # Construct the URL by substituting the values from the DataFrame
    url = f"http://0.0.0.0:8080/spliceai/?hg=37&distance=50&mask=1&variant={chr_value}-{pos_value}-{ref_value}-{alt_value}&raw=chr{chr_value}-{pos_value}-{ref_value}-{alt_value}"
    
    # Make the GET request
    response = requests.get(url)
    print(response)
    # Parse JSON response
    parsed_response = json.loads(response.text)
    print(parsed_response)
    # Loop through the scores
    for score in parsed_response.get('scores', []):
        if 'WRGL4' in score.get('SYMBOL', ''):
            # Update DataFrame
            df.at[index, 'DS_AG'] = round(float(score['DS_AG']), 2)
            df.at[index, 'DS_AL'] = round(float(score['DS_AL']), 2)
            df.at[index, 'DS_DG'] = round(float(score['DS_DG']), 2)
            df.at[index, 'DS_DL'] = round(float(score['DS_DL']), 2)
            df.at[index, 'DP_AG'] = score['DP_AG']
            df.at[index, 'DP_AL'] = score['DP_AL']
            df.at[index, 'DP_DG'] = score['DP_DG']
            df.at[index, 'DP_DL'] = score['DP_DL']

            # Set "DP" columns to NaN if corresponding "DS" is 0.00
            # To match control group because when value in DS is 0.00
            # I oginally ignored the equivalent DP. This is also perfomed 
            # in the website but the json response provide the value and I don't need this
            ds_cols = ['DS_AG', 'DS_AL', 'DS_DG', 'DS_DL']
            dp_cols = ['DP_AG', 'DP_AL', 'DP_DG', 'DP_DL']
        
            for ds_col, dp_col in zip(ds_cols, dp_cols):
                if df.at[index, ds_col] == 0.00:
                    df.at[index, dp_col] = np.nan
            

             # Perform comparisons for DS
            for control_col, test_col in zip(['DS_AG-CONTROL', 'DS_AL-CONTROL', 'DS_DG-CONTROL', 'DS_DL-CONTROL' ],
                                     ['DS_AG', 'DS_AL', 'DS_DG', 'DS_DL' ]):
                new_col_name = f"Comparison_{test_col}"
                df.at[index, new_col_name] = compare_single_column(df.loc[index], control_col, test_col)
            
            # In Python, the comparison NaN == NaN returns False.
            # This is part of the IEEE 754 floating-point standard, which Python follows.
            # the custom comparison function avoid this
            for control_col, test_col in zip(['DP_AG-CONTROL', 'DP_AL-CONTROL', 'DP_DG-CONTROL', 'DP_DL-CONTROL'],
                                             ['DP_AG', 'DP_AL', 'DP_DG', 'DP_DL']):
                new_col_name = f"Comparison_{test_col.split('_')[1]}"
                df.at[index, new_col_name] = custom_compare(df.loc[index], control_col, test_col)

            print(df.loc[[index]])  # Print the row that was just processed
            # Perform comparisons DS
            break  # Exit the loop after the first match     

df.to_csv('./results.csv', index=False)  # Set index=False to avoid writing row numbers

        



