for /f "delims=" %%F in ('dir /b *.py') do @echo %%F >> filelist.txt
xgettext -o locale\\Tefter.pot -d Tefter --from-code=UTF-8 --language=Python --no-wrap --package-name="Pametni tefter" --package-version="2.0" --copyright-holder="Danijela Popovic <eternal.romania@gmail.com>" --files-from=filelist.txt
del filelist.txt