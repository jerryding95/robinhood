import sys
from collections import defaultdict
import random

def main():
    input_name = sys.argv[1]
    mat_name = input_name.split('/')[-1]
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
        
        if '\t' in lines:
            l = lines.split("\t")
        else:
            l = lines.split(" ")
        if dim:
            h = int(l[0])
            w = int(l[1])
            nnz = int(l[2])
            dim = False
            continue

        m = int(l[0])
        n = int(l[1]) 

        # Need to convert to start with 0
        if len(l) > 2:
            val = float(l[2])
        else:
            val = random.random()
        
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

    outfile = open(output_name, "w")

    outfile.write(f"{h} {w} {nnz}\n")
    for i in range(h):
        outfile.write(f"{ptr[i]}\n")

    for i in range(h):
        for ele in mat_cols[i]:
            outfile.write(f"{ele}\n")

    for i in range(h):
        for ele in mat_data[i]:
            outfile.write(f"{ele}\n")
    
    
    print(h, w, nnz)

        
if __name__ == '__main__':
    main()

