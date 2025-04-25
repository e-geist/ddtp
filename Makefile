presentation:
	pandoc -t revealjs -i --include-in-header doc/presentation/slides.css --slide-level 2 --embed-resource -s doc/presentation/presentation.md -o doc/presentation/presentation.html -V revealjs-url=https://cdn.jsdelivr.net/npm/reveal.js@5.2.1 -V theme=white

start-kafka:
	docker compose -f docker/docker-compose.yml up -d

stop-kafka:
	docker compose -f docker/docker-compose.yml down