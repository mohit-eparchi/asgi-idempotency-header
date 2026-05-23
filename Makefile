.PHONY: clean ruff

clean:
	@find . -type f -name '*.pyc' -exec rm -rf {} +
	@find . -type f -name '.coverage' -exec rm -rf {} +
	@find . -type f -name 'Thumbs.db' -exec rm -rf {} \;
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '.pytest_cache' -exec rm -rf {} +
	@find . -type d -name '.ruff_cache' -exec rm -rf {} +
	@find . -type d -name '.venv' -exec rm -rf {} +
	rm -rf .cache

ruff:
	ruff format
	ruff check
