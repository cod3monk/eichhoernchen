.PHONY: all clean continuous
all: style.css

%.css: %.scss
	sass $< $@

clean:
	$(RM) style.css

continuous:
	sass --watch style.scss:style.css
