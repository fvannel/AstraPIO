PYTHON ?= python3

.PHONY: check test
check:
	$(PYTHON) tools/check_project.py
	$(PYTHON) -m unittest discover -s test -p test_tools.py

test: check
	$(MAKE) -C test
	$(PYTHON) tools/check_results.py test/results.xml
