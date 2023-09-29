env:=venv
requires:=requirements.txt

run: $(env)
	$</bin/python browser.py

$(env): $(requires)
	python -m venv venv;$@/bin/pip install -r $<
