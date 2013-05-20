.PHONY: all clean continuous
all: style.css

SCSS=scss-1.9
SCSS_FLAGS=--unix-newlines

%.css: %.scss
	$(SCSS) $(SCSS_FLAGS) $< $@

clean:
	$(RM) style.css

continuous:
	$(SCSS) $(SCSS_FLAGS) --watch style.scss:style.css
