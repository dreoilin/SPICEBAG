# compile command
FC = f2py

# compile flags
FCFLAGS = -c

# source files
SRCS = $(wildcard *.f90)

# target names
PROGS = $(patsubst %.f90,%,$(SRCS))

all: $(PROGS)

%: %.f90
	@echo "Compiling $<"
	@$(FC) $(FCFLAGS) -m $@ $<
