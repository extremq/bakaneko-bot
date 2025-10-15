docker build . -t bakaneko
nohup docker run -d --rm --restart unless-stopped bakaneko > ./log.txt 2> ./err.txt & -d --rm --restart unless-stopped