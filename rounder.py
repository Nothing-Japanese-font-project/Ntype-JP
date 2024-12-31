import defcon
import ufo2ft
import numpy as np
import time
import datetime
import tqdm

def update_font_info(font, name, weight, designer, id):
    font.info.familyName = name
    font.info.styleName = weight
    font.info.postscriptFamilyName = name
    font.info.postscriptFullName = name + " " + weight
    font.info.versionMajor = 1
    font.info.versionMinor = 0
    font.info.openTypeNamePreferredFamilyName = name
    font.info.openTypeNamePreferredSubfamilyName = weight
    font.info.openTypeNameFamilyName = name
    font.info.openTypeNameSubfamilyName = weight
    font.info.openTypeNameCompatibleFullName = name + " " + weight
    font.info.openTypeNameUniqueID = id + "-" + weight
    font.info.openTypeOS2VendorID = id
    font.info.openTypeNameManufacturer = designer
    font.info.openTypeNameDesigner = designer
    font.info.openTypeNameLicense = "SIL Open Font License"
    font.info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"
    font.info.openTypeNameDescription = name + " " + weight
    font.info.openTypeNameSampleText = name + " " + weight
    font.info.openTypeNameWWSFamilyName = name

def getpoints(contour):
    points = []
    for point in contour:
        points.append(point)
    return points

def insertpoint(points, index, x, y, segmentType='curve'):
    points.insert(index, defcon.Point((x, y), segmentType=segmentType, smooth=True))

def bolderhorizon(contour):
    points = getpoints(contour)
    adjust = 15
    limit = 4
    mod = [0] * len(points)
    if len(points) > 1:
        if contour.clockwise:
            for i in range(len(points)):
                prev_index = (i - 1) % len(points)
                next_index = (i + 1) % len(points)
                v_prev = np.array([points[prev_index].x, points[prev_index].y])
                v = np.array([points[i].x, points[i].y])
                v_next = np.array([points[next_index].x, points[next_index].y])
                v1 = np.array(v_prev - v)
                v2 = np.array(v_next - v)
                d1 = np.linalg.norm(v_prev - v)
                d2 = np.linalg.norm(v_next - v)
                condition1 = all([abs(points[i].y - points[prev_index].y) <= limit, mod[i] == 0])
                condition2 = all([abs(np.arctan2(v1[1], v1[0])) <= np.pi / 4, d1 >= 300, mod[i] == 0])
                condition3 = all([abs(points[i].y - points[next_index].y) <= limit, mod[i] == 0])
                condition4 = all([abs(np.arctan2(v2[1], v2[0])) <= np.pi / 4, d2 >= 300, mod[i] == 0])
                if any([condition1, condition2]):
                    tmp_adjust = adjust if np.linalg.norm(v - v_prev) > 20 else adjust * 3 / 2
                    mod[i] = -tmp_adjust if points[i].x >= points[prev_index].x else tmp_adjust
                if any([condition3, condition4]):
                    tmp_adjust = adjust if np.linalg.norm(v - v_next) > 20 else adjust * 3 / 2
                    mod[i] = -tmp_adjust if points[i].x <= points[next_index].x else tmp_adjust
        else:
            for i in range(len(points)):
                prev_index = (i - 1) % len(points)
                next_index = (i + 1) % len(points)
                v_prev = np.array([points[prev_index].x, points[prev_index].y])
                v = np.array([points[i].x, points[i].y])
                v_next = np.array([points[next_index].x, points[next_index].y])
                v1 = np.array(v_prev - v)
                v2 = np.array(v_next - v)
                d1 = np.linalg.norm(v_prev - v)
                d2 = np.linalg.norm(v_next - v)
                condition1 = all([abs(points[i].y - points[prev_index].y) <= limit, mod[i] == 0])
                condition2 = all([abs(np.arctan2(v1[1], v1[0])) <= np.pi / 4, d1 >= 300, mod[i] == 0])
                condition3 = all([abs(points[i].y - points[next_index].y) <= limit, mod[i] == 0])
                condition4 = all([abs(np.arctan2(v2[1], v2[0])) <= np.pi / 4, d2 >= 300, mod[i] == 0])
                if any([condition1, condition2]):
                    tmp_adjust = adjust if np.linalg.norm(v - v_prev) > 20 else adjust * 3 / 2
                    mod[i] = tmp_adjust if points[i].x <= points[prev_index].x else -tmp_adjust
                if any([condition3, condition4]):
                    tmp_adjust = adjust if np.linalg.norm(v - v_next) > 20 else adjust * 3 / 2
                    mod[i] = tmp_adjust if points[i].x >= points[next_index].x else -tmp_adjust
        contour.clear()
        for i in range(len(points)):
            contour.appendPoint(defcon.Point((points[i].x, points[i].y + mod[i]), segmentType=points[i].segmentType, smooth=points[i].smooth))

def enhancedline(contour, points, p1, p2, p3, p4):
    v_limit = 50
    h_limit = 100
    adjust = 9
    if contour.clockwise:
        p1x = p1.x
        p1y = p1.y
        p2x = p2.x
        p2y = p2.y
        p3x = p3.x
        p3y = p3.y
        p4x = p4.x
        p4y = p4.y
        if all([
            abs(p2y - p3y) <= v_limit,
            abs(p2x - p1x) >= h_limit,
            abs(p3x - p4x) >= h_limit,
            p2y <= p3y,
        ]):
            p0x = (p1x - 75) if p2x - p1x >= 100 else (p1x + p2x * 3) / 4
            points.append(defcon.Point((p0x, p1y), segmentType='curve', smooth=True))
            points.append(defcon.Point((p1x, p1y + adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p2x, p2y + adjust), segmentType='line', smooth=True))
            points.append(defcon.Point((p3x - adjust, p3y - adjust / 2), segmentType='line', smooth=True))
            points.append(defcon.Point((p4x, p4y - adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p4x, p4y), segmentType='curve', smooth=True))
        elif all([
            abs(p2y - p3y) <= v_limit,
            abs(p2x - p1x) >= h_limit,
            abs(p3x - p4x) >= h_limit,
            p2y >= p3y,
        ]):
            p0x = (p1x - 75) if p2x - p1x >= 100 else (p1x + p2x * 3) / 4
            points.append(defcon.Point((p0x, p1y), segmentType='curve', smooth=True))
            points.append(defcon.Point((p1x, p1y - adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p2x, p2y - adjust), segmentType='line', smooth=True))
            points.append(defcon.Point((p3x - adjust, p3y + adjust / 2), segmentType='line', smooth=True))
            points.append(defcon.Point((p4x, p4y + adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p4x, p4y), segmentType='curve', smooth=True))
        else:
            points.append(p1)
    else:
        p1x = p1.x
        p1y = p1.y
        p2x = p2.x
        p2y = p2.y
        p3x = p3.x
        p3y = p3.y
        p4x = p4.x
        p4y = p4.y
        if all([
            abs(p3y - p2y) <= v_limit,
            abs(p2x - p1x) >= h_limit,
            abs(p3x - p4x) >= h_limit,
            p2y >= p3y,
        ]):
            p0x = (p1x - 75) if p2x - p1x >= 100 else (p1x + p2x * 3) / 4
            points.append(defcon.Point((p0x, p1y), segmentType='curve', smooth=True))
            points.append(defcon.Point((p1x, p1y - adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p2x, p2y - adjust), segmentType='line', smooth=True))
            points.append(defcon.Point((p3x - adjust, p3y + adjust / 2), segmentType='line', smooth=True))
            points.append(defcon.Point((p4x, p4y + adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p4x, p4y), segmentType='curve', smooth=True))
        elif all([
            abs(p3y - p2y) <= v_limit,
            abs(p2x - p1x) >= h_limit,
            abs(p3x - p4x) >= h_limit,
            p2y <= p3y,
        ]):
            p0x = (p1x - 75) if p2x - p1x >= 100 else (p1x + p2x * 3) / 4
            points.append(defcon.Point((p0x, p1y), segmentType='curve', smooth=True))
            points.append(defcon.Point((p1x, p1y + adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p2x, p2y + adjust), segmentType='line', smooth=True))
            points.append(defcon.Point((p3x - adjust, p3y - adjust / 2), segmentType='line', smooth=True))
            points.append(defcon.Point((p4x, p4y - adjust / 3), segmentType='curve', smooth=True))
            points.append(defcon.Point((p4x, p4y), segmentType='curve', smooth=True))
        else:
            points.append(p1)

def roundifycorner(points, p_prev, p, p_next, adjust, d_limit):
    ppx = p_prev.x
    ppy = p_prev.y
    px = p.x
    py = p.y
    pnx = p_next.x
    pny = p_next.y
    v1 = np.array([ppx - px, ppy - py])
    v2 = np.array([pnx - px, pny - py])
    d1 = np.linalg.norm(v1)
    d2 = np.linalg.norm(v2)
    arg1 = np.arctan2(v1[1], v1[0])
    arg2 = np.arctan2(v2[1], v2[0])
    arg12 = arg2 - arg1

    if all([any([d1 >= d_limit, d2 >= d_limit]), p.segmentType == 'line']):

        bx = np.divide((px * (d1 - adjust) + ppx * adjust), d1, out=np.zeros_like(px, dtype=np.float64), where=d1!=0)
        by = np.divide((py * (d1 - adjust) + ppy * adjust), d1, out=np.zeros_like(py, dtype=np.float64), where=d1!=0)
        ax = np.divide((px * (d2 - adjust) + pnx * adjust), d2, out=np.zeros_like(px, dtype=np.float64), where=d2!=0)
        ay = np.divide((py * (d2 - adjust) + pny * adjust), d2, out=np.zeros_like(py, dtype=np.float64), where=d2!=0)
        m = np.array([px + v1[0] + v2[0], py + v1[1] + v2[1]])
        radius = -1 * v1
        ronated = np.array([radius[0] * np.cos(arg12 / 2) - radius[1] * np.sin(arg12 / 2), radius[0] * np.sin(arg12 / 2) + radius[1] * np.cos(arg12 / 2)])
        v = np.array([(bx + px * 3 + ax) / 5, (by + py * 3 + ay) / 5])

        points.append(defcon.Point((bx, by), segmentType = 'curve', smooth = True))
        #points.append(defcon.Point((m[0] - ronated[0], m[1] - ronated[1]), segmentType = None, smooth = True))
        #points.append(defcon.Point((((bx + ax) / 2 + px) / 2, ((by + ay) / 2 + py) / 2), segmentType = None, smooth = True))
        points.append(defcon.Point((v[0], v[1]), segmentType = None, smooth = True))
        points.append(defcon.Point((ax, ay), segmentType = 'curve', smooth = True))

    elif all([p.segmentType != None, p.segmentType != 'curve']):
        tmp = 4
        bx = (px * tmp + ppx) / (tmp + 1)
        by = (py * tmp + ppy) / (tmp + 1)
        ax = (px * tmp + pnx) / (tmp + 1)
        ay = (py * tmp + pny) / (tmp + 1)
        v = np.array([(bx + px * 3 + ax) / 5, (by + py * 3 + ay) / 5])
        points.append(defcon.Point((bx, by), segmentType = 'curve', smooth = True))
        points.append(defcon.Point((v[0], v[1]), segmentType = None, smooth = True))
        points.append(defcon.Point((ax, ay), segmentType = 'curve', smooth = True))

    else:
        points.append(p)

def roundify(glyph):
    size = 20
    limit = 40
    for contour in glyph:
        points = []
        length = len(contour)
        for i in range(length):
            p_prev = contour[(i - 1) % length]
            p = contour[i]
            p_next = contour[(i + 1) % length]
            roundifycorner(points, p_prev, p, p_next, size, limit)
        contour.clear()
        for point in points:
            contour.appendPoint(point)

def enhansedglyph(glyph):
    for contour in glyph:
        points = []
        for i in range(len(contour)):
            p1 = contour[i]
            p2 = contour[(i + 1) % len(contour)]
            p3 = contour[(i + 2) % len(contour)]
            p4 = contour[(i + 3) % len(contour)]
            enhancedline(contour, points, p1, p2, p3, p4)
        contour.clear()
        for i in range(len(points)):
            contour.appendPoint(defcon.Point((points[i].x, points[i].y), segmentType=points[i].segmentType, smooth=points[i].smooth))









first = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] UFOファイル読み込み開始")

path = "./NotoSerifJP-Bold.otf.ufo"
font = defcon.Font(path=path)

start = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] UFOファイル読み込み終了")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] 経過時間: ",round(start - first),"秒")

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "]", font.info.familyName, font.info.styleName, "を読み込み")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] 合計", len(font), "字")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] コンパイル前処理開始")

name = "NType JP alpha"
weight = "Bold"
designer = "Nothing Japanese Font Project"
id = "NTYP"
update_font_info(font, name, weight, designer, id)

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 横画編集開始")

for glyphs in tqdm.tqdm(font):
    unicode = int(str(glyphs.unicode)) if glyphs.unicode != None else 0
    if any([0x2e80 <= unicode <= 0x2fdf, 0x3400 <= unicode <= 0x4dbf, 0x4e00 <= unicode <= 0x9fff, 0xf900 <= unicode <= 0xfaff, 0x20000 <= unicode <= 0x3fffff, unicode == 0x3005, unicode == 0x303b]):
        for contour in glyphs:
            bolderhorizon(contour)
'''
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 角立て処理開始")

for glyphs in tqdm.tqdm(font):
    unicode = int(str(glyphs.unicode)) if glyphs.unicode != None else 0
    if any([0x2e80 <= unicode <= 0x2fdf, 0x3400 <= unicode <= 0x4dbf, 0x4e00 <= unicode <= 0x9fff, 0xf900 <= unicode <= 0xfaff, 0x20000 <= unicode <= 0x3fffff, unicode == 0x3005, unicode == 0x303b]):
        enhansedglyph(glyphs)
'''
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 角丸処理開始")

for glyph in tqdm.tqdm(font):
    unicode = int(str(glyph.unicode)) if glyph.unicode != None else 0
    if any([0x2e80 <= unicode <= 0x4dbf, 0x4e00 <= unicode <= 0x9fff, 0xf900 <= unicode <= 0xfaff, 0x20000 <= unicode <= 0x3fffff, unicode == 0x3005, unicode == 0x303b]):
        roundify(glyph)

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 正規化処理開始")

irregular = 0
for glyphs in tqdm.tqdm(font):
    for contour in glyphs:
        points = getpoints(contour)
        for i in range (len(points)):
            if i == 0:
                p = points[0]
                if len(points) == 1:
                    p_next = points[0]
                else:
                    p_next = points[1]
            elif i == len(points) - 1:
                p = points[i]
                p_next = points[0]
            else:
                p = points[i]
                p_next = points[i + 1]
            if p.segmentType == None and p_next.segmentType == 'line':
                p.segmentType = 'curve'
                irregular += 1

mid = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 修正した制御点: ", irregular, "個")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] コンパイル前処理終了")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 経過時間: ",round(mid - start),"秒")

otf = ufo2ft.compileOTF(font)
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
otf.save("./"+now+".otf")

end = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] コンパイル終了")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 経過時間: ",round(end - mid),"秒")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 合計時間: ",round(end - first),"秒")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 合計", len(font), "字")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 処理速度: ",round(len(font) / (end - mid)),"字/秒")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 出力ファイル: ",now+".otf")