# First step: run the following command to setup environment variables
```
source setup_env.sh
```

# Download data
The input data is divided into three categories, large graphs, small graphs, and matrices. We provide three scripts to automatically download the data.
```
./download_graph_large.sh
./download_graph_small.sh
./download_matrix.sh
```
Note the mico in large graphs are preloaded in the `data` directory.

# Compile the applications
To compile the repository, execute the following commands
```
mkdir build
cd build
cmake $UPDOWN_SOURCE_CODE -DUPDOWNRT_ENABLE_LIBRARIES=ON -DCMAKE_INSTALL_PREFIX=$UPDOWN_INSTALL_DIR -DUPDOWNRT_ENABLE_APPS=ON -DUPDOWN_ENABLE_FASTSIM=ON -DUPDOWN_ENABLE_BASIM=ON -DUPDOWN_NODES=512 -DUPDOWN_SENDPOLICY=ON
make -j
make -j install
```


# Preprocess data
For a few applications, raw data needs to be preprocessed before execution. We include a `prep.sh` script in each of such application directories to preprocess the data. We explain by applications below.

### SPMV_CSR
The raw matrix files is in COO format. Run the following command to convert them into csr format.
```
./apps/spmv_csr/prep.sh
```

### PR/TC/JS
The raw graph files are edge lists. Run the following command to convert them into neighbor lists.
```
./apps/<app>/prep.sh
```
Replace \<app\> with either pr/tc/js.

### ScaleUp
Since the raw data is not large enough to fill a 512-node machine, run the following command to extrapolate and preprocess the data.
```
./apps/scaleup/prep.sh
```


# Run the applications
The applications are in directory `apps`. We include a script `run.sh` in each application to execute the experiment set and reproduce the results in the paper. To run the full experiment of an application, execute the following command.

```
./apps/<app>/run.sh
```

Replace \<app\> with spmv_coo/spmv_csr/pr/tc/js/gcn_vanilla/sorting/scaleup

For sorting, there are three applications (Bucket Quick Sort - Map / Bucket Quick Sort - Reduce / Bucket Insertion Sort). `./apps/sorting/run.sh` will run all three applicaitons.

For scale-up experiment, the run script will run SPMV_CSR on Freescale extrapolated by 64 times, and TC on LiveJournal extrapolated by 32 times.
