#include <iostream>
#include <fstream>
#include <vector>
#include <string>

int main(int argc, char** argv) {
    // ./duplicate 4 test_csr.mtx test_csr_out.mtx
    // This duplication program will work like 123 -> 123123123123
    if (argc < 8) {
        std::cerr << "Usage: ./duplicate <number_of_copy> <input_file> <output_file> <N> <M> <NNZ> <skip_line>\n";
        return 1;
    }

    long duplication = std::stol(argv[1]);
    std::string input_file = argv[2];
    std::string output_file = argv[3];
    long N = std::stol(argv[4]);
    long M = std::stol(argv[5]);
    long NNZ = std::stol(argv[6]);
    long skip_line = std::stol(argv[7]);

    // Read the original CSR
    std::ifstream infile(input_file);
    if (!infile.is_open()) {
        std::cerr << "Error opening input file\n";
        return 1;
    }

    for (long i = 0; i < skip_line; i++) {
        std::string line;
        std::getline(infile, line);
    }

    std::vector<long> rowptr(N+1);
    rowptr[0] = 0;
    for (long i = 1; i <= N; i++) {
        infile >> rowptr[i];
        rowptr[i] /= 8;
    }

    std::vector<long> colidx(NNZ);
    for (long i = 0; i < NNZ; i++) {
        infile >> colidx[i];
    }

    std::vector<double> val(NNZ);
    for (long i = 0; i < NNZ; i++) {
        infile >> val[i];
    }

    infile.close();

    // We want to duplicate each row. That means the new number of rows = k*N.
    long N_new = duplication * N;

    // Count new NNZ
    long NNZ_new = duplication * NNZ;

    // Build new rowptr, colidx, val
    std::vector<long> rowptr_new(N_new + 1, 0);
    std::vector<long> colidx_new(NNZ_new);
    std::vector<double> val_new(NNZ_new);

    // We'll replicate each row k times in sequence
    long current_nnz = 0;
    for (long repeat = 0; repeat < duplication; repeat++) {
        for (long i = 0; i < N; i++) {
            long start = rowptr[i];
            long end = rowptr[i+1];
            long length = end - start;
            long new_row = N * repeat + i;
            rowptr_new[new_row] = current_nnz;
            for (long k = 0; k < length; k++) {
                colidx_new[current_nnz + k] = colidx[start + k];
                val_new[current_nnz + k] = val[start + k];
            }
            current_nnz += length;
        }
    }

    // The last entry of rowptr_new is the total number of non-zeros
    rowptr_new[N_new] = current_nnz;

    // Write the new CSR to the output file
    std::ofstream outfile(output_file);
    if (!outfile.is_open()) {
        std::cerr << "Error opening output file\n";
        return 1;
    }

    outfile << N_new << " " << M << " " << NNZ_new << "\n";
    for (long i = 1; i <= N_new; i++) {
        outfile << rowptr_new[i] * 8 << "\n";
    }
    for (long i = 0; i < NNZ_new; i++) {
        outfile << colidx_new[i] << "\n";
    }
    for (long i = 0; i < NNZ_new; i++) {
        outfile << val_new[i] << "\n";
    }
    // for (long i = 0; i < N_new + 1; i++) {
    //     for (long j = rowptr_new[i]; j < rowptr_new[i + 1]; j++) {
    //         outfile << i << " " << colidx_new[j] << "\n";
    //     }
    // }

    outfile.close();

    return 0;
}