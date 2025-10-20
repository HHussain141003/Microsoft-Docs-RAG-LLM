import faiss
import numpy as np

# Load original index
index = faiss.read_index("../microsoft_learn_index.faiss")

# Extract vectors
n_vectors = index.ntotal
dim = index.d

vectors = np.zeros((n_vectors, dim), dtype='float32')
for i in range(n_vectors):
    vectors[i] = index.reconstruct(i)

nlist = min(100, n_vectors // 10) 
quantizer = faiss.IndexFlatL2(dim)
new_index = faiss.IndexIVFFlat(quantizer, dim, nlist)

# Train and add vectors
new_index.train(vectors)
new_index.add(vectors)

faiss.write_index(new_index, "visualisation_index.faiss")
