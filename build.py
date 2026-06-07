import PyInstaller.__main__

PyInstaller.__main__.run([
    'src/terminus.py',
    '--name=Terminus',
    '--add-data=src/assets;assets',
    '--windowed',
])