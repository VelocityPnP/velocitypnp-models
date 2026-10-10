# Contributing

Open an issue before you change a package schema or model approval policy.
Include the model or dataset ID, expected behavior, and validation evidence.

Run these checks before you submit a pull request:

```sh
python3 -m unittest discover -s tests
python3 tools/verify_repository.py
```

Published packages are immutable. Do not replace, rename, or delete a release
asset. Fix package content with a new version and update the applicable card
and catalog entry. Do not commit files from the ignored `dist/` directory.

Remove secrets, user names, host names, absolute paths, and unrelated machine
metadata from new package content before publication.
