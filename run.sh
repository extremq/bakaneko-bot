docker build . -t bakaneko
nohup docker run --rm bakaneko > ./log.txt 2> ./err.txt &