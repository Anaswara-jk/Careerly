import pickle

with open("job_metadata.pkl", "rb") as f:
    data = pickle.load(f)

print(type(data))
print(data)
