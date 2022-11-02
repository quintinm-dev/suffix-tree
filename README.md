## Lint
```bash
black -l 80 **/*.py
pylint --rcfile=pylintrc **/*.py
```

## Tests
```bash
python3 -m unittest tests.suffix_tree_test
```
