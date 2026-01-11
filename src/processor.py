import defcon
import ufo2ft
import datetime
import tqdm
import re
import os
from concurrent.futures import ProcessPoolExecutor
from effects import HorizontalBolder, HorizontalStrokeLeftCut, InkTrap, SerifTrapezoid, CornerEnhancer, CornerRounder, Normalizer

def process_glyph_worker(glyph_data):
    """並列処理用ワーカー（インスタンスを再利用して高速化）"""
    # init_workerで事前に生成されたインスタンスを取得
    bolder = getattr(process_glyph_worker, 'bolder', HorizontalBolder(adjust=9))
    left_cut = getattr(process_glyph_worker, 'left_cut', HorizontalStrokeLeftCut())
    ink_trap = getattr(process_glyph_worker, 'ink_trap', InkTrap())
    serif_trap = getattr(process_glyph_worker, 'serif_trap', SerifTrapezoid())
    enhancer = getattr(process_glyph_worker, 'enhancer', CornerEnhancer())
    rounder = getattr(process_glyph_worker, 'rounder', CornerRounder(size=12))
    normalizer = getattr(process_glyph_worker, 'normalizer', Normalizer())
    
    bolder.apply(glyph_data)
    left_cut.apply(glyph_data)
    ink_trap.apply(glyph_data)
    serif_trap.apply(glyph_data)
    enhancer.apply(glyph_data)
    # rounder.apply(glyph_data)  # 一時的に無効化
    normalizer.apply(glyph_data)
    
    # 座標を整数に丸める（浮動小数点を排除してファイルサイズを削減）
    for contour in glyph_data['contours']:
        for p in contour['points']:
            p['x'] = int(round(p['x']))
            p['y'] = int(round(p['y']))
                
    return glyph_data

def init_worker(rs):
    """ワーカープロセスの初期化（エフェクトを一度だけ生成）"""
    process_glyph_worker.bolder = HorizontalBolder(adjust=9)
    process_glyph_worker.left_cut = HorizontalStrokeLeftCut()
    process_glyph_worker.ink_trap = InkTrap()
    process_glyph_worker.serif_trap = SerifTrapezoid()
    process_glyph_worker.enhancer = CornerEnhancer()
    process_glyph_worker.rounder = CornerRounder(size=rs if rs != 20 else 12)
    process_glyph_worker.normalizer = Normalizer()

class FontProcessor:
    """フォント全体の処理を統括するクラス"""
    def __init__(self, input_path, round_size=20):
        self.input_path = input_path
        self.round_size = round_size
        self.font = None

    def load(self):
        print(f"[{datetime.datetime.now()}] Loading UFO: {self.input_path}")
        self.font = defcon.Font(path=self.input_path)
        print(f"[{datetime.datetime.now()}] Loaded {len(self.font)} glyphs.")

    def _extract_glyph_data(self, glyph):
        contours = []
        for contour in glyph:
            points = []
            for p in contour:
                points.append({'x': p.x, 'y': p.y, 'segmentType': p.segmentType, 'smooth': p.smooth})
            contours.append({'clockwise': contour.clockwise, 'points': points})
        return {'name': glyph.name, 'contours': contours}

    def _apply_glyph_data(self, glyph, data):
        glyph.clear()
        for c_data in data['contours']:
            contour = defcon.Contour()
            for p in c_data['points']:
                contour.appendPoint(defcon.Point((p['x'], p['y']), segmentType=p['segmentType'], smooth=p['smooth']))
            glyph.appendContour(contour)

    def is_target_glyph(self, unicode_val):
        """漢字や特定の記号を対象とする判定"""
        if unicode_val is None: return False
        # 範囲チェックを最適化
        return (0x4E00 <= unicode_val <= 0x9FFF or   # CJK Unified Ideographs
                0x3400 <= unicode_val <= 0x4DBF or   # CJK Unified Ideographs Extension A
                0x20000 <= unicode_val <= 0x3FFFF or # CJK Extensions (BMP outside)
                0xF900 <= unicode_val <= 0xFAFF or   # CJK Compatibility Ideographs
                0x2E80 <= unicode_val <= 0x2FDF or   # CJK Radicals Supplement
                unicode_val in (0x3005, 0x303B))     # 々, 〻
    def process(self, use_parallel=True, max_workers=None, subset_glyphs=None):
        if subset_glyphs:
            target_names = subset_glyphs
            print(f"[{datetime.datetime.now()}] Subset mode: Processing {len(target_names)} specified glyphs.")
        else:
            print(f"[{datetime.datetime.now()}] Target identification...")
            # unicodeDataを直接走査して対象グリフ名を一気に取得
            target_names = []
            for uni, names in self.font.unicodeData.items():
                if self.is_target_glyph(uni):
                    target_names.extend(names)
            
            target_names = sorted(list(set(target_names)))
            print(f"[{datetime.datetime.now()}] Processing {len(target_names)} target glyphs.")
        
        total_targets = len(target_names)

        def data_generator():
            for name in target_names:
                yield self._extract_glyph_data(self.font[name])

        if use_parallel:
            print(f"[{datetime.datetime.now()}] Starting parallel conversion (high-throughput)...")
            chunk_size = 100
            with ProcessPoolExecutor(
                max_workers=max_workers, 
                initializer=init_worker, 
                initargs=(self.round_size,)
            ) as executor:
                # 通信効率の良い map(chunksize) を使用
                results_iter = executor.map(process_glyph_worker, data_generator(), chunksize=chunk_size)
                
                # 通知を一括で止めて反映を高速化
                self.font.holdNotifications()
                try:
                    for res in tqdm.tqdm(results_iter, total=total_targets, desc="Processing"):
                        self._apply_glyph_data(self.font[res['name']], res)
                finally:
                    self.font.releaseHeldNotifications()
        else:
            print(f"[{datetime.datetime.now()}] Starting sequential conversion...")
            init_worker(self.round_size)
            self.font.holdNotifications()
            try:
                for name in tqdm.tqdm(target_names, desc="Processing"):
                    data = self._extract_glyph_data(self.font[name])
                    res = process_glyph_worker(data)
                    self._apply_glyph_data(self.font[name], res)
            finally:
                self.font.releaseHeldNotifications()

    def save_otf(self, output_path, optimize_cff=True, subset_glyphs=None):
        font_to_compile = self.font
        
        if subset_glyphs:
            print(f"[{datetime.datetime.now()}] Creating subset font for fast preview...")
            # 最小限のフォントを作成
            subset_font = defcon.Font()
            # メタデータのコピー
            for attr in ['familyName', 'styleName', 'unitsPerEm', 'ascender', 'descender', 'xHeight', 'capHeight']:
                val = getattr(self.font.info, attr)
                if val is not None:
                    setattr(subset_font.info, attr, val)
            
            # 必要なグリフのコピー (.notdef は必須、サブセット時はフィーチャーは無視)
            needed = set(subset_glyphs) | {".notdef", "space"}
            for name in needed:
                if name in self.font:
                    subset_font.insertGlyph(self.font[name], name=name)
            
            font_to_compile = subset_font

        if font_to_compile.features.text:
            print(f"[{datetime.datetime.now()}] Sanitizing features.fea (fixing aalt script errors)...")
            def sanitize_aalt(match):
                block = match.group(0)
                sub_block = re.sub(r'^\s*(script|language)\s+[^;]+;\s*$', '', block, flags=re.MULTILINE)
                return sub_block
            
            new_text = re.sub(r'feature aalt\s*\{.*?\}\s*aalt\s*;', sanitize_aalt, font_to_compile.features.text, flags=re.DOTALL)
            font_to_compile.features.text = new_text

        print(f"[{datetime.datetime.now()}] Compiling OTF (CFFVersion: 2, Optimize: {optimize_cff})...")
        # ufo2ftの内部でcffsubrが走る前にpost形式を3.0にする必要があるため、一旦最適化オフでコンパイル
        otf = ufo2ft.compileOTF(font_to_compile, optimizeCFF=False, cffVersion=2)
        
        # post形式 2.0 (デフォルト) はインデックス溢れで保存できないため 3.0 (名前なし) に変更
        otf["post"].formatType = 3.0

        if optimize_cff:
            import cffsubr
            print(f"[{datetime.datetime.now()}] Subroutinizing CFF2 (this will take a few minutes for 65k glyphs)...")
            # 手動でサブルーチン化を実行（このとき内部でotf.saveが走るが、post=3.0なら通る）
            cffsubr.subroutinize(otf, cff_version=2)
        
        otf.save(output_path)
        print(f"[{datetime.datetime.now()}] Saved to {output_path}")
