import defcon
import ufo2ft
import datetime
import tqdm
import re
import os
from concurrent.futures import ProcessPoolExecutor
from effects import HorizontalBolder, CornerEnhancer, CornerRounder, Normalizer

def process_glyph_worker(glyph_data):
    """並列処理用ワーカー（インスタンスを再利用して高速化）"""
    # init_workerで事前に生成されたインスタンスを取得
    bolder = getattr(process_glyph_worker, 'bolder', HorizontalBolder(adjust=9))
    enhancer = getattr(process_glyph_worker, 'enhancer', CornerEnhancer())
    rounder = getattr(process_glyph_worker, 'rounder', CornerRounder(size=20))
    normalizer = getattr(process_glyph_worker, 'normalizer', Normalizer())
    
    bolder.apply(glyph_data)
    enhancer.apply(glyph_data)
    rounder.apply(glyph_data)
    normalizer.apply(glyph_data)
                
    return glyph_data

def init_worker(rs):
    """ワーカープロセスの初期化（エフェクトを一度だけ生成）"""
    process_glyph_worker.bolder = HorizontalBolder(adjust=9)
    process_glyph_worker.enhancer = CornerEnhancer()
    process_glyph_worker.rounder = CornerRounder(size=rs)
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

    def process(self, use_parallel=True, max_workers=None):
        print(f"[{datetime.datetime.now()}] Target identification...")
        # unicodeDataを直接走査して対象グリフ名を一気に取得 (20秒程度かかるが最も確実)
        target_names = []
        for uni, names in self.font.unicodeData.items():
            if self.is_target_glyph(uni):
                target_names.extend(names)
        
        target_names = sorted(list(set(target_names)))
        total_targets = len(target_names)
        print(f"[{datetime.datetime.now()}] Processing {total_targets} target glyphs.")

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

    def save_otf(self, output_path, optimize_cff=False):
        if self.font.features.text:
            print(f"[{datetime.datetime.now()}] Sanitizing features.fea (fixing aalt script errors)...")
            def sanitize_aalt(match):
                block = match.group(0)
                sub_block = re.sub(r'^\s*(script|language)\s+[^;]+;\s*$', '', block, flags=re.MULTILINE)
                return sub_block
            
            new_text = re.sub(r'feature aalt\s*\{.*?\}\s*aalt\s*;', sanitize_aalt, self.font.features.text, flags=re.DOTALL)
            self.font.features.text = new_text

        print(f"[{datetime.datetime.now()}] Compiling OTF (Optimization/Compression: {optimize_cff})...")
        print(f"[{datetime.datetime.now()}] This may take a few minutes if optimization is enabled.")
        
        otf = ufo2ft.compileOTF(self.font, optimizeCFF=False, cffVersion=2)
        
        otf["post"].formatType = 3.0

        if optimize_cff:
            import cffsubr
            print(f"[{datetime.datetime.now()}] Subroutinizing CFF2 (this will take some time)...")
            cffsubr.subroutinize(otf, cff_version=2)
        
        otf.save(output_path)
        print(f"[{datetime.datetime.now()}] Saved to {output_path}")
