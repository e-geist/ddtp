presentation-standalone:
	pandoc -t revealjs --include-in-header doc/presentation/slides.css --slide-level 2 --embed-resources -s doc/presentation/presentation.md -o doc/presentation/presentation-standalone.html

presentation:
	pandoc -t revealjs --include-in-header doc/presentation/slides.css --slide-level 2 -s doc/presentation/presentation.md -o doc/presentation/presentation.html