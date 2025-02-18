# Pametni tefter – SmartNotebook 

A simple app to manage your contacts and appointments 


## Features 

This is a work-in-progress app, and here are some of the planned and implemented features. 

- [x] Export of contacts 
- [ ] Import of contacts 
- [ ] Send email to selected contacts 
- [x] Export of appointments 
- [ ] Import of appointments 
- [ ] Export and import customizable templates 
- [x] Customizable app interface sounds 
- [ ] Better customization/choice of appointment importance sounds 
- [ ] ... :blush: 


## Some notes 

Run `extract_translatables.bat` with gettext installed on your machine to update the translation template (locale/Tefter.pot) 


## Build 

You can build an executable file like those in the releases, it's pretty simple. 

First of all, install **pyinstaller** (I'm not going to tell you to always work in virtual environments, you shall know it by now :grin:):  

```shell
pip install pyinstaller
```

Then run the command:  

```shell
pyinstaller --onefile --windowed --name Tefter --icon=icon.png --add-data "locale;locale" --add-data "sounds;sounds" --version-file version_info.txt --noconsole Tefter.py
```
