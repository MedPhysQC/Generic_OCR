# Generic_OCR

See [Wiki](../../wiki) for documentation.

## Dependencies
This module makes use of pyocr, which uses tesseract.

Installation instruction for tesseract can be found on many pages, e.g.  
http://grimhacker.com/2014/11/23/installing-pytesseract-practically-painless/

### macOS:
For homebrew:

```
brew install tessaract
```

### Windows:
Follow the instructions on e.g.
* https://github.com/UB-Mannheim/tesseract/wiki
* http://digi.bib.uni-mannheim.de/tesseract/
* http://3.onj.me/tesseract/
```
wget http://3.onj.me/tesseract/how\ to\ install.txt
wget http://3.onj.me/tesseract/tesseract-core-20160524.exe
wget http://3.onj.me/tesseract/tesseract-langs-20160524.exe
```

### Linux:
apt install -y tesseract-ocr tesseract-ocr-eng
