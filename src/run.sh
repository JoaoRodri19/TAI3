g++ -W -Wall -std=c++11 -o GetMaxFreqs GetMaxFreqs.cpp -lsndfile -lfftw3 -lm

directory="../signaturesmusic"
if [ ! -d "$directory" ]; then
  # Create the directory if it doesn't exist
  mkdir -p "$directory"
  echo "Directory created: $directory"
else
  echo "Directory already exists: $directory"
fi

path="../wavs"
i=0
for file in $(ls $path)
do
    let i+=1
    #echo $i
    ./GetMaxFreqs -w "../signaturesmusic/signature$i.freqs" "$path"/"$(basename "$file")"
done

#GetMaxFreqs -w test.freqs test.wav