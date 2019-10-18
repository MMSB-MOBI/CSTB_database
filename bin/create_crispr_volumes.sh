for i in $(seq 1 63); do 
    echo crispr_rc01_v$i
    curl -X PUT http://localhost:5984/crispr_rc01_v$i
done