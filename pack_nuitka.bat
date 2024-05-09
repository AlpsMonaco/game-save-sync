call venv\Scripts\activate.bat
python -m nuitka --onefile mainwindow.py --enable-plugin=pyside6 --noinclude-dlls=qt6pdf.dll --noinclude-dlls=qt6network.dll --noinclude-dlls=qt6svg.dll
pause