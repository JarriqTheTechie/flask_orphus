rmdir /s /q dist
rmdir /s /q build
python setup.py sdist bdist_wheel
pip install twine
twine upload dist/*
rmdir /s /q dist
rmdir /s /q build