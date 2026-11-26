.PHONY: all data train eval app test clean

PYTHON = python

all: data train eval

data:
	$(PYTHON) -m src.data

train:
	$(PYTHON) -m src.train

eval:
	$(PYTHON) -m src.evaluate

app:
	streamlit run app.py

test:
	pytest -v tests/

clean:
	rm -rf data/processed/* results/* __pycache__ src/__pycache__ tests/__pycache__
