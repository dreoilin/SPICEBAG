ROOT=turmeric
FORTRAN=$(ROOT)/FORTRAN

all:
	$(MAKE) -C $(FORTRAN)

requirements:
	pip install -r requirements.txt

test:
	python -m unittest discover

clean:
	$(MAKE) -C $(FORTRAN) clean

.PHONY: requirements test clean

