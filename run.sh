docker build . -t bakaneko
docker run -d --restart unless-stopped bakaneko > ./log.txt 2> ./err.txt &