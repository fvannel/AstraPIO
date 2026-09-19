PYTHON ?= python3

.PHONY: check test unit host-test differential
check:
	$(PYTHON) tools/check_project.py
	$(PYTHON) -m unittest discover -s test -p test_tools.py
	$(PYTHON) -m unittest discover -s test -p test_micro_tools.py
	$(PYTHON) -m unittest discover -s test -p test_provisional_precheck.py
	$(PYTHON) -m unittest discover -s test -p test_release_policy.py
	$(PYTHON) -m unittest discover -s test -p test_sram_diagnostic.py

unit:
	$(MAKE) -C test/units
	$(PYTHON) tools/check_results.py test/units/results.xml
	$(MAKE) -C test/program
	$(PYTHON) tools/check_results.py test/program/results.xml
	$(MAKE) -C test/program PROGRAM_WIDTH=16 COCOTB_RESULTS_FILE=results16.xml
	$(PYTHON) tools/check_results.py test/program/results16.xml

host-test:
	mkdir -p work/host-test
	$(CC) -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined firmware/pio_host.c test/test_host.c -o work/host-test/test_host
	./work/host-test/test_host
	$(CC) -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined firmware/pio_host.c firmware/pio_timed.c test/test_host_timed.c -o work/host-test/test_host_timed
	./work/host-test/test_host_timed

differential:
	$(MAKE) -C test/differential
	$(PYTHON) tools/check_results.py test/differential/results.xml

test: check unit host-test differential
	$(MAKE) -C test
	$(PYTHON) tools/check_results.py test/results.xml
