import site

# Determine path to site-packages
PACKAGES_PATH = site.getsitepackages()[0]

cv2_path = f"{PACKAGES_PATH}/cv2"
mediapipe_path = f"{PACKAGES_PATH}/mediapipe"
pyautogui_path = f"{PACKAGES_PATH}/pyautogui"

block_cipher = None

# Add paths to the Analysis object
a = Analysis(['main.py'],
             pathex=[cv2_path, mediapipe_path, pyautogui_path],
             binaries=[],
             datas=[(f"{mediapipe_path}", "mediapipe"),
                    (f"{cv2_path}/data", "cv2/data")],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='handroller.exe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='assets/handroller.ico')
