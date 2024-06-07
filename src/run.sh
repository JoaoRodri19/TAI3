python3 run_seg.py seg ../complete_musics 5 10
python3 run_seg.py sig
python3 run_seg.py compress gzip

DIR="../segment_of_music"

for FILE in "$DIR"/*; do
  if [ -f "$FILE" ]; then
    python3 run_seg.py pred $FILE gzip
  fi
done

python3 run_seg.py clean