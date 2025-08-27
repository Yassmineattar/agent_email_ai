import pickle

with open("db/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# Affiche le nombre d'éléments
print(f"Nombre de documents indexés : {len(metadata)}")

# Affiche les 5 premiers éléments
for i in range(min(5, len(metadata))):
    print(f"\nDocument {i} :")
    for key, value in metadata[i].items():
        print(f"  {key}: {value}")
