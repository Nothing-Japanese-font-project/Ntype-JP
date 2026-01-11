import numpy as np
from matplotlib.path import Path
from typing import List, Dict, Any, Optional, Tuple

class GlyphEffect:
    """グリフ加工処理の基底クラス"""
    def apply(self, glyph_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """グリフデータに補正を適用する
        
        Args:
            glyph_data: グリフ情報の辞書
            **kwargs: 各エフェクト固有の追加引数
            
        Returns:
            Dict[str, Any]: 処理後のグリフ情報
        """
        raise NotImplementedError


class HorizontalBolder(GlyphEffect):
    """横画を太くする処理
    
    水平に近いセグメントを検出し、y座標をわずかに調整することで
    フォント全体の横画の太さをコントロールする。
    """
    def __init__(self, adjust: float = 9.0, limit: float = 4.0):
        """
        Args:
            adjust: 調整量（ピクセル単位）
            limit: 水平判定のためのy座標差の閾値
        """
        self.adjust = adjust
        self.limit = limit

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """グリフ内のすべての輪郭に対して横画の太さを調整する"""
        for contour in glyph_data['contours']:
            clockwise = contour['clockwise']
            points = contour['points']
            if len(points) <= 1:
                continue

            mod = [0.0] * len(points)
            for i in range(len(points)):
                p_c = points[i]
                p_p = points[(i - 1) % len(points)]
                p_n = points[(i + 1) % len(points)]
                
                v1 = np.array([p_p['x'] - p_c['x'], p_p['y'] - p_c['y']])
                v2 = np.array([p_n['x'] - p_c['x'], p_n['y'] - p_c['y']])
                d1 = np.linalg.norm(v1)
                d2 = np.linalg.norm(v2)

                # 水平判定
                # 1. 前後の点とのy座標差がlimit以内
                # 2. またはベクトルがほぼ水平で一定以上の長さがある
                cond1 = abs(p_c['y'] - p_p['y']) <= self.limit
                cond2 = abs(np.arctan2(v1[1], v1[0])) <= np.pi / 4 and d1 >= 300
                cond3 = abs(p_c['y'] - p_n['y']) <= self.limit
                cond4 = abs(np.arctan2(v2[1], v2[0])) <= np.pi / 4 and d2 >= 300

                if (cond1 or cond2):
                    tmp_adj = self.adjust if d1 > 20 else self.adjust * 1.5
                    if clockwise:
                        mod[i] = -tmp_adj if p_c['x'] >= p_p['x'] else tmp_adj
                    else:
                        mod[i] = tmp_adj if p_c['x'] <= p_p['x'] else -tmp_adj

                if mod[i] == 0 and (cond3 or cond4):
                    tmp_adj = self.adjust if d2 > 20 else self.adjust * 1.5
                    if clockwise:
                        mod[i] = -tmp_adj if p_c['x'] <= p_n['x'] else tmp_adj
                    else:
                        mod[i] = tmp_adj if p_c['x'] >= p_n['x'] else -tmp_adj

            for i, val in enumerate(mod):
                points[i]['y'] += val
        return glyph_data


class HorizontalStrokeLeftCut(GlyphEffect):
    """横画の左端を斜め（バックスラッシュ方向＼）に切り落とす処理
    
    明朝体の横画の開始部分に特徴的な斜めカットを追加する。
    上下両方のコーナーを調整して線幅を維持する。
    """
    def __init__(self, cut_size: float = 12.0, min_length: float = 100.0):
        """
        Args:
            cut_size: 切り落としの大きさ（ピクセル単位）
            min_length: 対象とする最小水平線分長
        """
        self.cut_size = cut_size
        self.min_length = min_length

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """横画の左端を検出し、斜めカットを適用する
        
        横画の左端の上下両方のコーナーを調整して、
        線幅を維持しながらバックスラッシュ状のカットを表現する。
        """
        for contour in glyph_data['contours']:
            clockwise = contour['clockwise']
            points = contour['points']
            n = len(points)
            if n < 4:
                continue
            
            # 横画の左端の上下コーナーを検出
            for i in range(n):
                p = points[i]
                p_next = points[(i + 1) % n]
                p_prev = points[(i - 1) % n]
                
                if p.get('segmentType') != 'line':
                    continue
                
                dx_next = p_next['x'] - p['x']
                dy_next = p_next['y'] - p['y']
                length_next = np.sqrt(dx_next**2 + dy_next**2)
                
                dx_prev = p['x'] - p_prev['x']
                dy_prev = p['y'] - p_prev['y']
                length_prev = np.sqrt(dx_prev**2 + dy_prev**2)
                
                # 水平で右向きの十分長い線分の始点を検出（外側輪郭の上辺）
                if length_next >= self.min_length and dx_next > 0 and abs(dy_next) < 5:
                    is_vertical_prev = length_prev > 30 and abs(dx_prev) < abs(dy_prev) * 0.3
                    if not clockwise and dy_prev < -30 and is_vertical_prev:
                        # 上コーナー: 右下に移動
                        p['x'] += self.cut_size * 0.8
                        p['y'] -= self.cut_size * 0.6
                
                # 水平で左向きの十分長い線分の終点を検出（外側輪郭の下辺）
                if length_prev >= self.min_length and dx_prev < 0 and abs(dy_prev) < 5:
                    is_vertical_next = length_next > 30 and abs(dx_next) < abs(dy_next) * 0.3
                    if not clockwise and dy_next > 30 and is_vertical_next:
                        # 下コーナー: 右上に移動
                        p['x'] += self.cut_size * 0.8
                        p['y'] += self.cut_size * 0.6
        
        return glyph_data



class InkTrap(GlyphEffect):
    """交差点に墨だまり（インクトラップ）を追加する処理
    
    画が交差する箇所の内角に小さな凹みを追加することで、
    印刷時のインクの滲みを軽減し、視認性を向上させる。
    """
    def __init__(self, trap_size: float = 8.0, min_angle: float = 30.0, max_angle: float = 150.0,
                 min_segment_length: float = 50.0):
        """
        Args:
            trap_size: 墨だまりの深さ（ピクセル単位）
            min_angle: 処理対象とする最小交差角度（度）
            max_angle: 処理対象とする最大交差角度（度）
            min_segment_length: 処理対象とする最小線分長（短すぎる線分や点を除外）
        """
        self.trap_size = trap_size
        self.min_angle = np.radians(min_angle)
        self.max_angle = np.radians(max_angle)
        self.min_segment_length = min_segment_length

    def _get_angle(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """2つのベクトル間の角度を計算（ラジアン）"""
        d1 = np.linalg.norm(v1)
        d2 = np.linalg.norm(v2)
        if d1 < 1e-6 or d2 < 1e-6:
            return np.pi  # 長さがほぼゼロの場合は180度を返す
        cos_theta = np.clip(np.dot(v1, v2) / (d1 * d2), -1.0, 1.0)
        return np.arccos(cos_theta)

    def _is_inner_corner(self, v1: np.ndarray, v2: np.ndarray, clockwise: bool) -> bool:
        """凹角（内側の角）かどうかを判定"""
        cross = np.cross(v1, v2)
        # PostScript形式: 外側輪郭はCCW、内側輪郭はCW
        # clockwise=Trueなら内側輪郭
        return (cross > 0) if clockwise else (cross < 0)

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """交差点を検出し、墨だまりを追加する"""
        # TODO: 一時的に無効化 - 後で修正予定
        return glyph_data


class SerifTrapezoid(GlyphEffect):
    """うろこ（セリフ）を三角形から台形に変換する処理
    
    Noto Serif JPのうろこはcurve（ベジェ曲線）で構成されているため、
    curveの頂点を2つのline点に分割して平らな上辺を作成する。
    """
    def __init__(self, flat_ratio: float = 0.15):
        """
        Args:
            flat_ratio: 上辺の幅を決める比率（大きいほど広い台形）
        """
        self.flat_ratio = flat_ratio

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """うろこの曲線頂点を検出し、2つのline点に分割して台形を作成
        
        一時的に無効化中
        """
        return glyph_data  # 一時的に無効化
        
        for contour in glyph_data['contours']:
            clockwise = contour['clockwise']
            points = contour['points']
            n = len(points)
            
            if n < 5 or clockwise:  # 外側輪郭のみ対象
                continue
            
            # うろこ頂点インデックスを検出
            serif_indices = set()
            for i in range(n):
                p = points[i]
                p_prev = points[(i - 1) % n]
                p_next = points[(i + 1) % n]
                
                if (p.get('segmentType') == 'curve' and 
                    p_next.get('segmentType') == 'line' and
                    p_prev.get('segmentType') is None):
                    
                    dx = p_next['x'] - p['x']
                    dy = p_next['y'] - p['y']
                    dist = np.sqrt(dx**2 + dy**2)
                    
                    # うろこの特徴: 適度な距離で左下方向
                    if 30 < dist < 200 and dx < 0 and dy < 0:
                        serif_indices.add(i)
            
            if not serif_indices:
                continue
            
            # 新しいポイントリストを構築
            new_points = []
            skip_next = 0
            
            for i in range(n):
                if skip_next > 0:
                    skip_next -= 1
                    continue
                
                p = points[i]
                
                if i in serif_indices:
                    # うろこ頂点: 2つのline点に分割
                    p_prev2 = points[(i - 2) % n]  # 前のcurve点（右側）
                    p_next = points[(i + 1) % n]   # 次のline点
                    
                    # 上辺の左端（現在の頂点を少し下げた位置）
                    flat_width = self.flat_ratio * 50  # 固定幅
                    left_x = p['x'] - flat_width * 0.3
                    left_y = p['y'] - flat_width * 0.5
                    
                    # 上辺の右端
                    right_x = p['x'] + flat_width * 0.3
                    right_y = p['y'] - flat_width * 0.5
                    
                    # 左側の点を追加（lineタイプ）
                    new_points.append({
                        'x': left_x, 'y': left_y,
                        'segmentType': 'line', 'smooth': False
                    })
                    # 右側の点を追加（lineタイプ）
                    new_points.append({
                        'x': right_x, 'y': right_y,
                        'segmentType': 'line', 'smooth': False
                    })
                    
                else:
                    # 通常の点はそのまま追加
                    new_points.append(p)
            
            contour['points'] = new_points
        
        return glyph_data




class CornerEnhancer(GlyphEffect):
    """角立ちを強調する処理
    
    微小な段差がある角に対して、点を追加してエッジを立たせる。
    """
    def __init__(self, v_limit: float = 50.0, h_limit: float = 30.0, adjust: float = 3.0):
        """
        Args:
            v_limit: 垂直方向の段差を検出する閾値
            h_limit: 水平方向の線分の最低長さ
            adjust: 強調のための座標ずらし量
        """
        self.v_limit = v_limit
        self.h_limit = h_limit
        self.adjust = adjust

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """グリフ内の特定の角に対して強調処理を適用する"""
        for contour in glyph_data['contours']:
            points = contour['points']
            if len(points) < 5:
                continue
            
            new_points = []
            i = 0
            while i < len(points):
                # 直前3点と現在の点をチェック
                p_m3 = points[(i - 3) % len(points)]
                p_m2 = points[(i - 2) % len(points)]
                p_m1 = points[(i - 1) % len(points)]
                p_0 = points[i % len(points)]
                
                # 線分かつ水平な並びであるかチェック
                if self._is_target_segment(p_m3, p_m2, p_m1, p_0):
                    diff_y = p_m2['y'] - p_m1['y']
                    
                    if 0 < diff_y <= self.v_limit: # Case 1: 下がり段差
                        new_points.extend(self._create_enhanced_points(p_m3, p_m2, p_m1, p_0, case=1))
                        i += 3
                        continue
                    elif 0 < -diff_y <= self.v_limit: # Case 2: 上がり段差
                        new_points.extend(self._create_enhanced_points(p_m3, p_m2, p_m1, p_0, case=2))
                        i += 3
                        continue
                
                new_points.append(p_m3)
                i += 1
            contour['points'] = new_points
        return glyph_data

    def _is_target_segment(self, p1, p2, p3, p4) -> bool:
        """加工対象のセグメント構成であるか判定する"""
        return all([
            p1['y'] == p2['y'], 
            p3['y'] == p4['y'], 
            p1.get('segmentType') == "line", 
            p2.get('segmentType') == "line", 
            p3.get('segmentType') == "line", 
            p4.get('segmentType') == "line",
            p1['x'] - p2['x'] >= self.h_limit, 
            p4['x'] - p3['x'] >= self.h_limit
        ])

    def _create_enhanced_points(self, p_m3, p_m2, p_m1, p_0, case: int) -> List[Dict[str, Any]]:
        """強調された点のリストを生成する"""
        pts = []
        pts.append({'x': p_m3['x'], 'y': p_m3['y'], 'segmentType': "line", 'smooth': True})
        
        if case == 1:
            pts.append({'x': (p_m3['x'] * 3 + p_m2['x']) / 4, 'y': p_m3['y'], 'segmentType': "line", 'smooth': True})
            pts.append({'x': p_m2['x'] - self.adjust * 3, 'y': p_m2['y'] + self.adjust, 'segmentType': "line", 'smooth': True})
            pts.append({'x': p_m1['x'] + self.adjust, 'y': p_m1['y'] - self.adjust * 3, 'segmentType': "line", 'smooth': True})
            pts.append({'x': (p_m1['x'] * 3 + p_0['x']) / 4, 'y': p_m1['y'], 'segmentType': "line", 'smooth': True})
        else:
            pts.append({'x': (p_m3['x'] * 2 + p_m2['x']) / 3, 'y': p_m3['y'], 'segmentType': "line", 'smooth': True})
            pts.append({'x': p_m2['x'] + self.adjust, 'y': p_m2['y'] - self.adjust * 3, 'segmentType': "line", 'smooth': True})
            pts.append({'x': p_m1['x'] - self.adjust * 3, 'y': p_m1['y'] + self.adjust, 'segmentType': "line", 'smooth': True})
            pts.append({'x': (p_m1['x'] * 2 + p_0['x']) / 3, 'y': p_m1['y'], 'segmentType': "line", 'smooth': True})
            
        pts.append({'x': p_0['x'], 'y': p_0['y'], 'segmentType': "line", 'smooth': True})
        return pts


class CornerRounder(GlyphEffect):
    """角丸処理
    
    直角に近い角を検出し、ベジェ曲線に置き換えることで角を丸める。
    """
    def __init__(self, size: float = 20.0, limit: float = 40.0):
        """
        Args:
            size: 角丸の大きさ（半径に相当する制御点のオフセット）
            limit: 角丸を適用するための最小線分長
        """
        self.size = size
        self.limit = limit

    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """グリフ内のすべての輪郭に対して角丸処理を適用する"""
        for contour in glyph_data['contours']:
            old_points = contour['points']
            new_points = []
            length = len(old_points)
            for i in range(length):
                p_p = old_points[(i - 1) % length]
                p = old_points[i]
                p_n = old_points[(i + 1) % length]
                self._roundify_corner(new_points, p_p, p, p_n)
            contour['points'] = new_points
        return glyph_data

    def _roundify_corner(self, points: List[Dict[str, Any]], p_p: Dict[str, Any], p: Dict[str, Any], p_n: Dict[str, Any]):
        """特定の点に対して角丸処理を行い、結果をpointsリストに追加する"""
        v1 = np.array([p_p['x'] - p['x'], p_p['y'] - p['y']])
        v2 = np.array([p_n['x'] - p['x'], p_n['y'] - p['y']])
        d1 = np.linalg.norm(v1)
        d2 = np.linalg.norm(v2)

        # マジックナンバーの定義
        WEIGHT_CORNER = 3.0
        WEIGHT_TOTAL = 5.0
        TIGHT_CURVE_FACTOR = 4.0

        is_large_enough = (d1 >= self.limit and d2 >= self.limit)
        
        if is_large_enough and p.get('segmentType') == "line":
            # 指定されたsizeに基づく角丸
            bx = (p['x'] * (d1 - self.size) + p_p['x'] * self.size) / d1
            by = (p['y'] * (d1 - self.size) + p_p['y'] * self.size) / d1
            ax = (p['x'] * (d2 - self.size) + p_n['x'] * self.size) / d2
            ay = (p['y'] * (d2 - self.size) + p_n['y'] * self.size) / d2
            
            # 中央の制御点を計算
            vx = (bx + p['x'] * WEIGHT_CORNER + ax) / WEIGHT_TOTAL
            vy = (by + p['y'] * WEIGHT_CORNER + ay) / WEIGHT_TOTAL
            
            points.append({'x': bx, 'y': by, 'segmentType': 'curve', 'smooth': True})
            points.append({'x': vx, 'y': vy, 'segmentType': None, 'smooth': True})
            points.append({'x': ax, 'y': ay, 'segmentType': 'curve', 'smooth': True})
            
        elif p.get('segmentType') is not None and p.get('segmentType') != "curve":
            # 線分だが短い場合、強制的に微小な角丸を適用
            f = TIGHT_CURVE_FACTOR
            bx = (p['x'] * f + p_p['x']) / (f + 1)
            by = (p['y'] * f + p_p['y']) / (f + 1)
            ax = (p['x'] * f + p_n['x']) / (f + 1)
            ay = (p['y'] * f + p_n['y']) / (f + 1)
            
            vx = (bx + p['x'] * WEIGHT_CORNER + ax) / WEIGHT_TOTAL
            vy = (by + p['y'] * WEIGHT_CORNER + ay) / WEIGHT_TOTAL
            
            points.append({'x': bx, 'y': by, 'segmentType': 'curve', 'smooth': True})
            points.append({'x': vx, 'y': vy, 'segmentType': None, 'smooth': True})
            points.append({'x': ax, 'y': ay, 'segmentType': 'curve', 'smooth': True})
        else:
            # すでに曲線であるか、加工対象外
            points.append(p)

class Normalizer(GlyphEffect):
    """グリフの正規化
    
    セグメントタイプの整合性を整える。
    """
    def apply(self, glyph_data: Dict[str, Any]) -> Dict[str, Any]:
        """オフカーブポイントの直後のポイントがcurve属性を持つように修正する"""
        for contour in glyph_data['contours']:
            pts = contour['points']
            for i in range(len(pts)):
                p = pts[i]
                p_next = pts[(i + 1) % len(pts)]
                # segmentTypeがNone（オフカーブ）の次がlineになっている場合、curveに修正
                if p.get('segmentType') is None and p_next.get('segmentType') == "line":
                    p_next['segmentType'] = "curve"
        return glyph_data
