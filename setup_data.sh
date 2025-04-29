mkdir $UPDOWN_DATA_DIR
wget -P $UPDOWN_DATA_DIR https://snap.stanford.edu/data/ca-AstroPh.txt.gz
gunzip $UPDOWN_DATA_DIR/ca-AstroPh.txt

# wget https://snap.stanford.edu/data/ca-HepPh.txt.gz