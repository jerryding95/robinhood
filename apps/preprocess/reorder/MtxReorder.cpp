#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <map>
#include <vector>
#include <cassert>
#include <algorithm>
#include <set>

typedef uint64_t* ptr;

typedef struct vertex{
  uint64_t deg;
  uint64_t id;
  ptr neigh;
} vertex_t;


using namespace std;

int nnodes = 0;
int nedeges = 0;
vector< set<int> > adj_list;
vector<int> deg_list;


vector< pair<int, int> > degree_vec;
map<int, int> index_map;
map<int, int> index_map2;

map<int, int> vertex_id;


int read_graph(char  * filename, int m)
{
    std::ifstream fin(filename);
    std::string line;
    while (std::getline(fin, line) && (line[0] == '#'))
    {
    //    cout << line << endl;
        ;
    }
    
    std::istringstream sin(line);
    printf("nnodes=%d\n",m);
    nnodes = m;
    nedeges = 0;
    adj_list.resize(nnodes);
    deg_list.resize(nnodes);
    int id = 0;
    vertex_id.clear();
    
    // while (getline(fin, line) && (line[0] != '\n'))
    do {
        std::istringstream sin(line);
        std::string tmp;
        int v1, v2;
//        cout << line << endl;
        sin >> v1 >> v2;
//        cout << v1 << v2;
    //    printf("%d %d\n",v1,v2);

        if(vertex_id.find(v1) == vertex_id.end())
        {
            vertex_id[v1] = id;
            // vertex_id[v1] = v1;
            id++;
        }
        if(vertex_id.find(v2) == vertex_id.end())
        {
            vertex_id[v2] = id;
            // vertex_id[v2] = v2;
            id++;
        }
        if(vertex_id[v1] != vertex_id[v2])
        {
            adj_list[vertex_id[v1]].insert(vertex_id[v2]);
            adj_list[vertex_id[v2]].insert(vertex_id[v1]);
        }
        else{
            printf("self loop edge : %d -> %d\n",v1,v2);
        }
        
    } while (getline(fin, line) && (line[0] != '\n'));

    nnodes = id;
    
    fin.close();
    return 0;
}


void build_degree_vec()
{
    degree_vec.clear();
    int i = 0;
    nedeges = 0;
    for(i=0; i<nnodes; i++){
        degree_vec.push_back(pair<int, int>(i,adj_list[i].size()));
        nedeges = adj_list[i].size() + nedeges;
    }
    // for(i=0; i<(nnodes-1); i++){
    //     if(degree_vec[i].second < degree_vec[i+1].second)
    //         printf("error degree deg[%d]=%d, deg[%d]=%d\n", degree_vec[i].first, degree_vec[i].second, degree_vec[i+1].first, degree_vec[i+1].second);
    // }
    
}

bool vec_cmp(pair<int, int> a, pair<int, int> b) {
    return a.second > b.second;
}

void node_index_reorder()
{
    int id;
    for(int i=0;i<nnodes;i++)
    {
        id = degree_vec[i].first;
        index_map.insert( pair<int, int>(id,i) );
        index_map2.insert( pair<int, int>(i,id) );
        
    }
}

void transfer_graph(char  * filename, char *output_filename)
{
    
    std::ifstream fin(filename);
    std::string line;
    std::ofstream fout(output_filename);
    while (std::getline(fin, line) && (line[0] == '#'))
    {
        fout << line << endl;
    }
    
    int tmp_i;
    for(tmp_i=0; tmp_i<nnodes; tmp_i++)
    {
        int i = index_map2[tmp_i];
        int degree = 0;
        set<int> list_tmp;
        for (set<int>::iterator iter = adj_list[i].begin(); iter != adj_list[i].end(); iter++)
        {
            list_tmp.insert(index_map[*iter]);
        }
        for (set<int>::iterator iter = list_tmp.begin(); iter != list_tmp.end(); iter++)
        {
            fout << tmp_i << " " << *iter << endl;
            degree++;
        }
        deg_list[tmp_i] = degree;

    }
    
    return;
}


void transfer2bin(char  * filename)
{

    uint64_t **adjlists; // Adjacency lists
    uint64_t* vertices;
    uint64_t* degrees;

    std::string binfile, binfile_gv, binfile_nl, binfile_jac;
    char* binfilename;
    FILE* out_file, *in_file;

    uint64_t num_nodes = nnodes;

    printf("num_nodes = %ld\n",num_nodes);
    printf("num_edge = %d\n",nedeges);

    adjlists = (uint64_t**)malloc(num_nodes*sizeof(uint64_t*));
    vertices = (uint64_t*)malloc(num_nodes*sizeof(uint64_t));
    degrees = (uint64_t*)malloc(num_nodes*sizeof(uint64_t));


    int data;
    struct vertex *g_v_bin = (struct vertex*)malloc(num_nodes*sizeof(struct vertex));
    int ranked=0;
    uint64_t neighbor_array_size=0;
  
    int ii = 0;
    int kk = 0;
    int max_deg = adj_list[0].size();
 
    for(kk=0; kk<num_nodes; kk++){
        int i = index_map2[kk];
        vertices[ranked] = kk;
        degrees[ranked] = deg_list[kk]; 
        uint64_t* adjlist_local = NULL;
        if (degrees[ranked] > 0)
        {
            adjlist_local = new uint64_t[degrees[ranked]];
            neighbor_array_size += degrees[ranked];
            int e=0;
            set<int> list_tmp;
            for (set<int>::iterator iter = adj_list[i].begin(); iter != adj_list[i].end(); iter++)
            {
                list_tmp.insert(index_map[*iter]);
            }
            for (set<int>::iterator iter = list_tmp.begin(); e < degrees[ranked] && iter != list_tmp.end(); iter++)
            {
                uint64_t vid = (*iter);
                adjlist_local[e] = vid;
                e++;
            }
        }
        adjlists[ii++] = adjlist_local;
        ranked++;
    }
    printf("Adjacency Lists created\n");

    binfile = std::string(filename) + ".bin";
    binfile_gv = std::string(filename) + "_gv" + ".bin";
    binfile_nl = std::string(filename) + "_nl" + ".bin";
    
    binfilename = const_cast<char*>(binfile.c_str()); 

    printf("Binfile:%s\n", binfilename);
    out_file = fopen(binfilename, "wb");
    if (!out_file) {
          exit(EXIT_FAILURE);
    }
    fseek(out_file, 0, SEEK_SET);
    printf("Size of uint64_t:%ld, writing num_nodes:%ld, neighbor_array_size:%ld\n", sizeof(uint64_t), num_nodes, neighbor_array_size);
    fwrite(&num_nodes, sizeof(uint64_t), 1, out_file);
    fwrite(&neighbor_array_size, sizeof(uint64_t), 1, out_file);
    for(int i = 0; i < num_nodes; i++){
      fwrite(&degrees[i], sizeof(degrees[i]), 1, out_file);
      fwrite(&vertices[i], sizeof(vertices[i]), 1, out_file);
      fwrite(adjlists[i], sizeof(uint64_t), degrees[i], out_file);
    }
    fclose(out_file);

    binfilename = const_cast<char*>(binfile_gv.c_str()); 
    printf("Binfile:%s\n", binfilename);
    out_file = fopen(binfilename, "wb");
    if (!out_file) {
          exit(EXIT_FAILURE);
    }
    fseek(out_file, 0, SEEK_SET);
    printf("Size of uint64_t:%ld, writing num_nodes:%lu in new file\n", sizeof(uint64_t), num_nodes);
    fwrite(&num_nodes,sizeof(uint64_t),1,out_file);
    for(int i=0; i< num_nodes;i++){
      fwrite(&degrees[i], sizeof(degrees[i]), 1, out_file);
      fwrite(&vertices[i], sizeof(vertices[i]), 1, out_file);
      fwrite(&adjlists[i], sizeof(adjlists[i]), 1, out_file);
    }
    fclose(out_file);

  
    binfilename = const_cast<char*>(binfile_nl.c_str()); 
    printf("Binfile:%s\n", binfilename);
    out_file = fopen(binfilename, "wb");
    if (!out_file) {
          exit(EXIT_FAILURE);
    }
    fseek(out_file, 0, SEEK_SET);
    printf("Size of uint64_t:%ld, writing nlarray:%ld in NL\n", sizeof(uint64_t), neighbor_array_size);
    fwrite(&neighbor_array_size,sizeof(uint64_t), 1, out_file);
    for(int i=0; i< num_nodes;i++)
    {
      fwrite(adjlists[i], sizeof(uint64_t), degrees[i], out_file);
    }
    fclose(out_file);
}

int main(int argc, char *argv[])
{
    if(argc!= 4)
    {
        printf("%s <input_filename> <output_filename> <num_vertex>\n",argv[0]);
    }
    char* input_filename = argv[1];
    char* output_filename = argv[2];
    
    int num_v = atoi(argv[3]);
    
    read_graph(input_filename, num_v);
    build_degree_vec();
    sort(degree_vec.begin(), degree_vec.end(), vec_cmp);
    int i = 0;
    node_index_reorder();
    transfer_graph(input_filename, output_filename);
    transfer2bin(output_filename);
    
    return 0;
    
}

