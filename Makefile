PYTHON ?= python3

.PHONY: check test unit host-test
check:
	$(PYTHON) tools/check_project.py
	$(PYTHON) -m unittest discover -s test -p test_tools.py
	$(PYTHON) -m unittest discover -s test -p test_provisional_precheck.py
	$(PYTHON) -m unittest discover -s test -p test_release_policy.py
	$(PYTHON) -m unittest discover -s test -p test_sram_diagnostic.py

unit:
	$(MAKE) -C test/units
	$(PYTHON) tools/check_results.py test/units/results.xml

host-test:
	mkdir -p work/host-test
	$(CC) -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined firmware/pio_host.c test/test_host.c -o work/host-test/test_host
	./work/host-test/test_host

test: check unit host-test
	$(MAKE) -C test
	$(PYTHON) tools/check_results.py test/results.xml
