g++ -W -Wall -std=c++11 -o GetMaxFreqs GetMaxFreqs.cpp -lsndfile -lfftw3 -lm
path="../../wavs"
$i = 0
for file in $(ls $path)
do
    $i = $i + 1
    echo $i
    #./GetMaxFreqs -w "../../signaturesmusic1".freqs" "$path"/"$(basename "$file")"
done

#GetMaxFreqs -w test.freqs test.wav