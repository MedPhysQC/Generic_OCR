Installation of tessaract for pyocr


http://grimhacker.com/2014/11/23/installing-pytesseract-practically-painless/

Mac:
brew install tessaract

Windows:
https://github.com/UB-Mannheim/tesseract/wiki
http://digi.bib.uni-mannheim.de/tesseract/
http://3.onj.me/tesseract/
wget http://3.onj.me/tesseract/how\ to\ install.txt
wget http://3.onj.me/tesseract/tesseract-core-20160524.exe
wget http://3.onj.me/tesseract/tesseract-langs-20160524.exe

Linux:
apt install -y tesseract-ocr tesseract-ocr-eng

Training data:
https://github.com/tesseract-ocr/tessdata

pip install pytesseract
or
pip install pyocr
https://github.com/jflesch/pyocr
see pyWAD ocr.py plugin (config example?)

https://saxenarajat99.wordpress.com/2014/10/04/optical-character-recognition-in-python/