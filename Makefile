.PHONY: clean ruff

clean:
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '.coverage' -delete
	@find . -type f -name 'Thumbs.db' -delete
	@find . -type d -name '__pycache__' -delete
	@find . -type d -name '.pytest_cache' -delete
	@find . -type d -name '.ruff_cache' -delete
	@find . -type d -name '.venv' -delete
	@find . -type d -name '.cache' -delete

ruff:
	@ruff format
	@ruff check
