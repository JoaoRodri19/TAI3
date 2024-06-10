if [ -d "../complete_musics" ]; then
    python3 run.py seg ../noise 5 10    
  fi
if [ -d "../noise" ]; then
    python3 run.py seg ../noise 5 10    
fi
python3 run.py sig
python3 run.py compress gzip 