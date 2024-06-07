DIR="../segment_of_music"

for FILE in "$DIR"/*; do
  if [ -f "$FILE" ]; then
    python3 run.py pred $FILE gzip
  fi
done