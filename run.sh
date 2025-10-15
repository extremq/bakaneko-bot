docker build . -t bakaneko
docker run -d --rm --restart unless-stopped bakaneko > ./log.txt 2> ./err.txt &