all:
	make convert
	make render

convert:
	for FILE in *.pov; do \
		python replace_on_file.py $$FILE ; \
	done

render:
	for FILE in *_re.pov; do \
	   	povray $${FILE} +H2000 +W2000 +A0.05 +Q10 -J -D; \
	done;
