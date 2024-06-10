if [ ! -d "complete_musics" ]; then
    wget -O complete_musics.zip "https://uapt33090-my.sharepoint.com/:u:/g/personal/jmourao_ua_pt/EYryuw1rZhNLvTH2cmW-c0QBzikYRuEfdXnAH0bfZpbIkw?e=Ynl7ei&download=1"
    unzip complete_musics.zip
    rm complete_musics.zip
else
    echo "Folder already exists. Skipping download and extraction."
fi