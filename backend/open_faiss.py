'''
import faiss
import numpy as np

# Load index
index = faiss.read_index("job_index.faiss")

# Number of vectors
n = index.ntotal
d = index.d  # vector dimension

# Reconstruct all vectors
all_vectors = np.zeros((n, d), dtype='float32')
for i in range(n):
    all_vectors[i] = index.reconstruct(i)

# Print all vectors
np.set_printoptions(suppress=True, precision=4)
print(all_vectors)
'''
from ml_model.dl_pipeline import DLPipeline

pipeline = DLPipeline()
print("Loaded jobs:", len(pipeline.metadata))

resume_text = "Python, Machine Learning, Data Analysis"
results = pipeline.search_jobs(resume_text)
print(results)
