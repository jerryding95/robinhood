#!/usr/bin/python

# generate a data input file for 
# spmv on udweave.
# the file is just going to be a binary coded file with non-zero information
# File: Header Entry*nentries VectorEntry*ncols 
# Header: nrows::Int64 ncols::Int64 nentries::Int64
# Entry: row::Int64 col::Int64 val::Double
# VectorEntry: val::Double 

# written from the following ChatGPT prompt
"""
Can we generate a python program to generate a random sparse matrix with scipy and output it in binary in the following format

# File: Header Entry*nentries VectorEntry*ncols 
# Header: nrows::Int64 ncols::Int64 nentries::Int64
# Entry: row::Int64 col::Int64 val::Double
# VectorEntry: val::Double 

nentries is the number of entries in the sparse matrix.

The vector entries should just be random double values from 0 to 1. 

I want to take nrows, ncols and the sparsity probability from the command line.
"""

import sys
import random
import numpy as np
import struct
from scipy.sparse import random as sp_random

def main():
    if len(sys.argv) != 4:
        print("Usage: python generate_sparse_matrix.py nrows ncols sparsity_probability")
        sys.exit(1)

    nrows = int(sys.argv[1])
    ncols = int(sys.argv[2])
    sparsity_probability = float(sys.argv[3])

    sparse_matrix = generate_random_sparse_matrix(nrows, ncols, sparsity_probability)
    random_vector = generate_random_vector(ncols)
    output_binary(sparse_matrix, random_vector, 'sparse_matrix.bin')

def generate_random_sparse_matrix(nrows, ncols, sparsity_probability):
    return sp_random(nrows, ncols, density=sparsity_probability)

def generate_random_vector(size):
    return np.random.rand(size)

def output_binary(sparse_matrix, random_vector, output_file):
    nentries = sparse_matrix.nnz
    nrows, ncols = sparse_matrix.shape
    row, col = sparse_matrix.nonzero()
    data = sparse_matrix.data

    with open(output_file, 'wb') as f:
        f.write(struct.pack('qqq', nrows, ncols, nentries))

        for i in range(nentries):
            f.write(struct.pack('qqd', row[i], col[i], data[i]))

        for val in random_vector:
            f.write(struct.pack('d', val))

if __name__ == "__main__":
    main()