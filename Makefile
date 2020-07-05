## Using Python 3.7 for this project
PYTHON_INTERPRETER = python3

## Serve the changeover labeller as a Bokeh app
.DEFAULT_GOAL := app
app:
	${PYTHON_INTERPRETER} -m bokeh serve real_estate_app/app.py --show

.venv/bin/activate: requirements.txt
	rm -rf .venv
	${PYTHON_INTERPRETER} -m pip install --upgrade pip
	${PYTHON_INTERPRETER} -m pip install --upgrade setuptools
	${PYTHON_INTERPRETER} -m pip install --upgrade virtualenv
	virtualenv --python ${PYTHON_INTERPRETER} .venv
	. .venv/bin/activate; \
		${PYTHON_INTERPRETER} -m pip install -r requirements.txt; \
		${PYTHON_INTERPRETER} -m pip install -e .; \
		ipython kernel install --user --name=real-estate-app; \

## Run tests.
.PHONY: tests 
tests: .venv/bin/activate
	. .venv/bin/activate; \
		${PYTHON_INTERPRETER} -m pytest tests --log-cli-level=DEBUG; \
