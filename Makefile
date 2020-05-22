ROOT=turmeric
FORTRAN=$(ROOT)/FORTRAN

all:
	$(MAKE) -C $(FORTRAN)

run:
	python -m turmeric --outfile tmp netlists/OP/diodemulti.net

requirements:
	pip install -r requirements.txt

test:
	python -m unittest discover

clean:
	$(MAKE) -C $(FORTRAN) clean

.PHONY: requirements test clean run

