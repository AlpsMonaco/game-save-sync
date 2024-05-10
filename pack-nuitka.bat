call venv\Scripts\activate.bat
python -m nuitka mainwindow.py --standalone --enable-plugin=pyside6 --disable-console --lto=yes