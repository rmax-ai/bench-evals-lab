# Agent instructions

- Never commit secrets. Read credentials only from environment variables.
- Keep every eval folder self-contained. Add dependencies to that eval's own `pyproject.toml` or `package.json`, never to a root dependency manifest or lockfile.
- Provide a one-command run path for every eval, such as a Makefile target or `npm` script, and document it in that eval's README.
- Treat results as artifacts. Commit them under `results/<YYYY-MM-DD>-<slug>/` within the eval folder.
- After changing an eval, run its documented command and verify it before committing.
- When adding an eval, update the index table in the root README.
