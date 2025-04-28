import random
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

def generate_coo_matrix(height, width, density, filename, seed=None):
    """
    Generate a random COO sparse matrix and write non-zero elements to a file.
    
    Parameters:
    height (int): Number of rows in the matrix.
    width (int): Number of columns in the matrix.
    density (float): Fraction of the matrix's elements that are non-zero.
    filename (str): The name of the file to write the non-zero elements.
    
    Returns:
    list of tuples: The non-zero elements as (row, col, value).
    """
    # Calculate the number of non-zero elements
    num_elements = height * width
    num_nonzeros = int(num_elements * density)
    print(num_nonzeros)

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Generate random positions and values for the non-zero elements
    rows = random.choices(range(1, height + 1), k=num_nonzeros)
    cols = random.choices(range(1, width + 1), k=num_nonzeros)
    values = np.random.rand(num_nonzeros)
    
    # Combine rows, cols, and values into a list of tuples
    non_zeros = list(zip(rows, cols, values))
    
    # Write the non-zero elements to the file
    with open(filename, 'w') as file:
        file.write(f'{height} {width} {num_nonzeros}\n')
        for row, col, value in non_zeros:
            file.write(f"{row} {col} {value}\n")
    
    return non_zeros

def generate_coo_matrix_norepeat(height, width, density, filename, seed=None):
    """
    Generate a random COO sparse matrix and write non-zero elements to a file.
    
    Parameters:
    height (int): Number of rows in the matrix.
    width (int): Number of columns in the matrix.
    density (float): Fraction of the matrix's elements that are non-zero.
    filename (str): The name of the file to write the non-zero elements.
    
    Returns:
    list of tuples: The non-zero elements as (row, col, value).
    """
    # Calculate the number of non-zero elements
    num_elements = height * width
    num_nonzeros = int(num_elements * density)
    print(num_nonzeros)

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Generate random positions and values for the non-zero elements
    rows = random.choices(range(1, height + 1), k=num_nonzeros)
    values = np.random.rand(num_nonzeros)

    rows.sort()
    count = defaultdict(int)
    for idx in range(len(rows)):
        count[rows[idx]] += 1

    cols = np.array([])
    cols = cols.astype(int)
    for ele in count:
        cols = np.append(cols, random.sample(range(1, width + 1), k=count[ele]))

    
    # Combine rows, cols, and values into a list of tuples
    non_zeros = list(zip(rows, cols, values))
    
    # Write the non-zero elements to the file
    with open(filename, 'w') as file:
        file.write(f'{height} {width} {num_nonzeros}\n')
        for row, col, value in non_zeros:
            file.write(f"{row} {col} {value}\n")
    
    return non_zeros

def plot_coo_matrix(non_zeros, height, width):
    """
    Plot the non-zero elements of a COO sparse matrix.
    
    Parameters:
    non_zeros (list of tuples): The non-zero elements as (row, col, value).
    height (int): Number of rows in the matrix.
    width (int): Number of columns in the matrix.
    """
    rows, cols, values = zip(*non_zeros)
    
    plt.figure(figsize=(10, 10))
    plt.scatter(cols, rows, c=values, cmap='viridis', marker='s', s=0.001)
    plt.colorbar(label='Value')
    plt.gca().invert_yaxis()
    plt.xlabel('Column')
    plt.ylabel('Row')
    plt.title('Non-Zero Elements of the COO Sparse Matrix')
    plt.savefig("sp_mat.png") 

def summary_stats(non_zeros):
    count = defaultdict(int)
    vals = defaultdict(set)
    m = 0
    for row, col, value in non_zeros:
        count[row] += 1
        if col in vals[row]:
            m += 1
        vals[row].add(col)

    max_val = 0
    min_val = 10000

    for ele in count:
        max_val = max(count[ele], max_val)
        min_val = min(count[ele], min_val)
    print(len(count), max_val, min_val, m)


# Example usage
height = 12288  # Number of rows
width = 12288   # Number of columns
density = 0.04  # Density of non-zero elements (10%)
filename = f'coo_{density}_{height}x{width}_matrix.txt'  # Output file name

non_zeros = generate_coo_matrix_norepeat(height, width, density, filename, seed=1)
#summary_stats(non_zeros)
#plot_coo_matrix(non_zeros, height, width)
