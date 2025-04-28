import sys
from collections import defaultdict
import numpy as np

def main():
    input_name = sys.argv[1]
    f = open(input_name)
    dim = True
    h = 0
    w = 0
    nnz = 0
    
    mat_data = defaultdict(list)
    mat_cols = defaultdict(list)

    c = 0
    for lines in f:
        if str(lines[0]) == "%":
            continue
        
        l = lines.split(" ")
        if dim:
            h = int(l[0])
            w = int(l[1])
            nnz = int(l[2])
            dim = False
            continue

        m = int(l[0]) - 1
        n = int(l[1]) - 1 
        # Need to convert to start with 0
        val = float(l[2])
        
        mat_data[m].append(val)
        mat_cols[m].append(n)
        c += 1

    ptr = []
    base = 0
    zc = 0
    for i in range(h):
        if i in mat_cols:
            base = base + len(mat_cols[i]) * 8
            sorted_vals = [x for _,x in sorted(zip(mat_cols[i],mat_data[i]))]
            mat_cols[i].sort()
            mat_data[i] = sorted_vals

        ptr.append(base)
    
    prefix = "".join(input_name.split(".")[:-1])
    file_type = input_name.split(".")[-1]
    output_name =  prefix + "_csr." + file_type

    array = np.array([h, w, nnz], dtype=np.uint64)

    ptr_full = []
    prev_val = 0
    for i in range(h):
        ptr_full += [prev_val, ptr[i]]
        prev_val = ptr[i]

    matcols = []
    for i in range(h):
        matcols += mat_cols[i]
    matdata = []
    for i in range(h):
        matdata += mat_data[i]
    
    ptr_full = np.array(ptr_full, dtype=np.uint64)
    mat_cols = np.array(matcols, dtype=np.uint64)
    mat_data = np.array(matdata, dtype=np.double)

    with open(f'{output_name}.bin', 'wb') as file:
        file.write(array.tobytes())
        file.write(ptr_full.tobytes())
        file.write(mat_cols.tobytes())
        file.write(mat_data.tobytes())

    
    
    print(h, w, nnz)

        
if __name__ == '__main__':
    main()

