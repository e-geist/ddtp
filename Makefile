presentation-standalone:
	pandoc -t revealjs --embed-resources -s doc/presentation/presentation.md -o doc/presentation/presentation-standalone.html

presentation:
	pandoc -t revealjs --slide-level 2 -s doc/presentation/presentation.md -o doc/presentation/presentation.html