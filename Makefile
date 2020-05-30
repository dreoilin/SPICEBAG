ROOT=turmeric
FORTRAN=$(ROOT)/FORTRAN
FORTRANBASE=$(patsubst %.f90,%,$(wildcard $(FORTRAN)/*.f90))
FORTRANOBJS=$(wildcard $(FORTRANBASE)*.so)

all:
	$(MAKE) -C $(FORTRAN)

run: $(if $(FORTRANOBJS),$(FORTRANOBJS), $(FORTRANBASE))
	python -m turmeric.gui

$(FORTRANBASE): 
	$(MAKE) -C $(FORTRAN) 

requirements:
	pip install -r requirements.txt

test:
	python -m unittest discover

clean:
	$(MAKE) -C $(FORTRAN) clean

deepclean: clean
	find . -name __pycache__ -exec rm -rf {} +

.PHONY: requirements test clean deepclean run

