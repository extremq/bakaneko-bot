docker build . -t bakaneko
docker run -d --restart unless-stopped -v $(pwd)/baka.db:/app/baka.db bakaneko