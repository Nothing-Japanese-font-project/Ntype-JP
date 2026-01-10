import defcon
import ufo2ft
import os
from pathlib import Path

UFO_PATH = "static/NotoSerifJP-Regular.otf.ufo"

def investigate():
    print(f"Loading UFO: {UFO_PATH}")
    font = defcon.Font(UFO_PATH)
    print(f"Total glyphs in UFO: {len(font)}")
    
    # aalt 機能を一時的に除去して試す
    if font.features.text:
        print("Features found. Content length:", len(font.features.text))
        # aalt ブロックを無効化してみる（テスト用）
        import re
        font.features.text = re.sub(r'feature aalt\s*\{.*?\}\s*aalt\s*;', '', font.features.text, flags=re.DOTALL)
        print("Removed aalt feature for testing.")

    try:
        print("Compiling OTF with optimizeCFF=False, cffVersion=2...")
        otf = ufo2ft.compileOTF(font, optimizeCFF=False, cffVersion=2)
        print(f"Compilation success! Total glyphs in output OTF: {len(otf.getGlyphOrder())}")
        
        # もし成功したら、手動でcffsubrを試みる
        import cffsubr
        print("Attempting manual subroutinization...")
        cffsubr.subroutinize(otf, cff_version=2)
        print("Subroutinization success!")
        
    except Exception as e:
        print(f"Compilation/Optimization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate()
