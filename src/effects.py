import numpy as np
from typing import List, Dict, Any, Optional

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
