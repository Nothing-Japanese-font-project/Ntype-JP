import defcon
import ufo2ft
import numpy as np
import time
import datetime
import tqdm

def getpoints(contour):
    points = []
    for point in contour:
        points.append(point)
    return points

def insertpoint(points, index, x, y, segmentType='curve'):
    points.insert(index, defcon.Point((x, y), segmentType=segmentType, smooth=True))

def bolderhorizon(contour, clockwise):
    points = getpoints(contour)
    adjust = 16
    limit = 32
    pos_x = []
    pos_y = []
    mod = [0] * len(points)
    index = 0
    count = 0
    if len(points) > 1:
        if clockwise==True:
            for i in range(len(points)):
                prev_index = (i - 1) % len(points)
                next_index = (i + 1) % len(points)
                if abs(points[i].y - points[prev_index].y) <= limit and mod[i] == 0:
                    mod[i] = -adjust if points[i].x >= points[prev_index].x else adjust
                if abs(points[i].y - points[next_index].y) <= limit and mod[i] == 0:
                    mod[i] = -adjust if points[i].x <= points[next_index].x else adjust
        else:
            for i in range(len(points)):
                prev_index = (i - 1) % len(points)
                next_index = (i + 1) % len(points)
                if abs(points[i].y - points[prev_index].y) <= limit and mod[i] == 0:
                    mod[i] = adjust if points[i].x <= points[prev_index].x else -adjust
                if abs(points[i].y - points[next_index].y) <= limit and mod[i] == 0:
                    mod[i] = adjust if points[i].x >= points[next_index].x else -adjust
    contour.clear()
    for i in range(len(points)):
        contour.appendPoint(defcon.Point((points[i].x, points[i].y + mod[i]), segmentType=points[i].segmentType, smooth=points[i].smooth))

def roundifycorner(points, index, p_prev, p, p_next, adjust, d_limit, r_limit):
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

    if d1 >= d_limit and d2 >= d_limit and p.segmentType == 'line':

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

    elif all([p.segmentType != 'curve', p.segmentType != None]):
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

first = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] UFOファイル読み込み開始")

font = defcon.Font(
    path="./NotoSerifJP-SemiBold.otf.ufo"
)

start = time.time()

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] UFOファイル読み込み終了")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] 経過時間: ",round(start - first),"秒")

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "]", font.info.familyName, font.info.styleName, "を読み込み")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] 合計", len(font), "字")
print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") , "] コンパイル前処理開始")

font.info.familyName = "NType JP Test"
font.info.styleName = "Bold"
font.info.postscriptFamilyName = "NType JP Test"
font.info.postscriptFullName = "NType JP Test Bold"
font.info.versionMajor = 1
font.info.versionMinor = 0



print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 横画編集開始")

for glyphs in tqdm.tqdm(font):
    for contour in glyphs:
        clockwise = contour.clockwise
        bolderhorizon(contour, clockwise)


print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 角丸処理開始")

size = 16
limit = 32

for glyphs in tqdm.tqdm(font):
    for contour in glyphs:
        points = []
        length = len(contour)
        for i in range(length):
            if i == 0:
                p_prev = contour[len(contour) - 1]
                p = contour[0]
                if length == 1:
                    p_next = contour[0]
                else:
                    p_next = contour[1]
                roundifycorner(points, 0, p_prev, p, p_next, size, limit, np.pi * 2 / 1)
            elif i == length - 1:
                p_prev = contour[i - 1]
                p = contour[i]
                p_next = contour[0]
                roundifycorner(points, i, p_prev, p, p_next, size, limit, np.pi * 2 / 1)
            else:
                p_prev = contour[i - 1]
                p = contour[i]
                p_next = contour[i + 1]
                roundifycorner(points, i, p_prev, p, p_next, size, limit, np.pi * 2 / 1)

        contour.clear()
        for point in points:
            contour.appendPoint(point)

print("[",datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") ,"] 正規化処理開始")

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

mid = time.time()

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
