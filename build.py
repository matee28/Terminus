import PyInstaller.__main__

PyInstaller.__main__.run([
    'src/terminus_test.py',
    '--name=Terminus',
    '--add-data=src/assets;assets',
    '--windowed',
])