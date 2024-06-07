python3 run.py seg ../complete_musics 5 10
python3 run.py sig
python3 run.py compress gzip

DIR="../segment_of_music"

for FILE in "$DIR"/*; do
  if [ -f "$FILE" ]; then
    echo "$FILE"
    python3 run.py pred $FILE gzip
  fi
done

python3 run.py clean