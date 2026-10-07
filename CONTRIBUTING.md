# Contributing to QuickBite

Thanks for your interest in improving this project. Contributions of any size are welcome.

## Ways to help

- Report a bug or suggest an idea by opening an issue
- Improve the docs or README
- Add a new SQL KPI query or dashboard chart
- Improve the cancellation model (new features, better metrics)
- Add more test questions for the text-to-SQL assistant

## Set up on your computer

1. Fork the repo and clone your fork
2. Install the libraries: `pip install -r requirements.txt`
3. Generate the data: `python generator/generate_data.py`
4. Build the warehouse and run the tests: `python pipeline/run_all.py`

## Make a change

1. Create a branch: `git checkout -b my-change`
2. Make your change
3. Run the tests: `python -m pytest tests/test_pipeline.py -q`
4. Commit with a short clear message
5. Push your branch and open a pull request. Say what you changed and why.

## Rules

- Never commit API keys, `.env` files, `quickbite.duckdb` or `data/raw/`
- The assistant must stay read-only. Do not remove `read_only=True` or the `is_safe()` check.
- Keep the pipeline tests passing

## Questions

Open an issue and I will reply as soon as I can.
'@ | Set-Content -Path CONTRIBUTING.md -Encoding utf8
