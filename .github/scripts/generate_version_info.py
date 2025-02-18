import os
from datetime import datetime

version = open("version.txt").read().strip()
version_tuple = tuple(map(int, version.split("-")[0].split("."))) + (0, )

year = datetime.today().year

content = f"""VSVersionInfo(
	ffi=FixedFileInfo(
		filevers={version_tuple},
		prodvers={version_tuple},
		mask=0x3f,
		flags=0x0,
		OS=0x40004,
		fileType=0x1,
		subtype=0x0,
		date=(0, 0)
	),
	kids=[
		StringFileInfo([
			StringTable(
				'040904B0',
				[
					StringStruct('CompanyName', 'Danijela Popović'),
					StringStruct('FileDescription', 'A smart notebook to manage your contacts and appointments'),
					StringStruct('FileVersion', '{version}'),
					StringStruct('InternalName', 'Tefter'),
					StringStruct('LegalCopyright', 'Copyright © {year} Danijela Popović'),
					StringStruct('OriginalFilename', 'Tefter.exe'),
					StringStruct('ProductName', 'Tefter'),
					StringStruct('ProductVersion', '{version}'),
				]
			)
		]),
		VarFileInfo([VarStruct('Translation', [1033, 1200])])
	]
)
"""

with open("version_info.txt", "w", encoding="utf-8") as version_info_file:
	version_info_file.write(content)
