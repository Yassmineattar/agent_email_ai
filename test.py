import pandas as pd

df = pd.read_csv('data/mails_data_cleaned_final.csv')
duplicate_uids = df[df.duplicated(subset='uid', keep=False)]

print(f"{len(duplicate_uids)} doublons trouvés:")
print(duplicate_uids[['uid']])
