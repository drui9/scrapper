env:=venv
requires:=requirements.txt

run: $(env)
	$</bin/python src/browser.py

$(env): $(requires)
	python -m venv venv;$@/bin/pip install -r $<
