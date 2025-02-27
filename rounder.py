import defcon
import ufo2ft
import numpy as np
import time
import datetime
import tqdm


def update_font_info(
    font,
    name,
    weight,
    designer,
    id,
    license_text=(
        "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
        'This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS '
        "OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, "
        "permissions and limitations governing your use of this Font Software."
    ),
    license_url="http://scripts.sil.org/OFL",
    wws_subfamily=None,
):
    if wws_subfamily is None:
        wws_subfamily = weight

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
    font.info.openTypeNameLicense = license_text
    font.info.openTypeNameLicenseURL = license_url
    font.info.openTypeNameDescription = name + " " + weight
    font.info.openTypeNameSampleText = name + " " + weight
    font.info.openTypeNameWWSFamilyName = name
    font.info.openTypeNameWWSSubfamilyName = wws_subfamily
    font.info.styleMapFamilyName = name

    # Designer information
    font.info.openTypeNameDesigner = "Ryoko NISHIZUKA 西塚涼子 (kana & ideographs); Frank Grießhammer (Latin, Greek & Cyrillic); Wenlong ZHANG 张文龙 (bopomofo); Sandoll Communications 산돌커뮤니케이션, Soohyun PARK 박수현, Yejin WE 위예진 & Donghoon HAN 한동훈 (hangul elements, letters & syllables)' Nothing Japanese Font Project Team'"
    font.info.openTypeNameDesignerURL = "http://www.adobe.com/type/"
    font.info.openTypeNameManufacturer = "Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI 服部正貴 (production & ideograph elements); Zachary Quinn Scheuren (variable font & overall production) Nothing Japanese Font Project Team"

    # License information
    font.info.openTypeNameLicense = 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.'
    font.info.openTypeNameLicenseURL = "http://scripts.sil.org/OFL"


def getpoints(contour):
    points = []
    for point in contour:
        points.append(point)
    return points


def insertpoint(points, index, x, y, segmentType="curve"):
    points.insert(index, defcon.Point((x, y), segmentType=segmentType, smooth=True))


def bolderhorizon(contour):
    points = getpoints(contour)
    adjust = 9
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
                condition1 = all(
                    [abs(points[i].y - points[prev_index].y) <= limit, mod[i] == 0]
                )
                condition2 = all(
                    [abs(np.arctan2(v1[1], v1[0])) <= np.pi / 4, d1 >= 300, mod[i] == 0]
                )
                condition3 = all(
                    [abs(points[i].y - points[next_index].y) <= limit, mod[i] == 0]
                )
                condition4 = all(
                    [abs(np.arctan2(v2[1], v2[0])) <= np.pi / 4, d2 >= 300, mod[i] == 0]
                )
                if any([condition1, condition2]):
                    tmp_adjust = (
                        adjust if np.linalg.norm(v - v_prev) > 20 else adjust * 3 / 2
                    )
                    mod[i] = (
                        -tmp_adjust
                        if points[i].x >= points[prev_index].x
                        else tmp_adjust
                    )
                if any([condition3, condition4]):
                    tmp_adjust = (
                        adjust if np.linalg.norm(v - v_next) > 20 else adjust * 3 / 2
                    )
                    mod[i] = (
                        -tmp_adjust
                        if points[i].x <= points[next_index].x
                        else tmp_adjust
                    )
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
                condition1 = all(
                    [abs(points[i].y - points[prev_index].y) <= limit, mod[i] == 0]
                )
                condition2 = all(
                    [abs(np.arctan2(v1[1], v1[0])) <= np.pi / 4, d1 >= 300, mod[i] == 0]
                )
                condition3 = all(
                    [abs(points[i].y - points[next_index].y) <= limit, mod[i] == 0]
                )
                condition4 = all(
                    [abs(np.arctan2(v2[1], v2[0])) <= np.pi / 4, d2 >= 300, mod[i] == 0]
                )
                if any([condition1, condition2]):
                    tmp_adjust = (
                        adjust if np.linalg.norm(v - v_prev) > 20 else adjust * 3 / 2
                    )
                    mod[i] = (
                        tmp_adjust
                        if points[i].x <= points[prev_index].x
                        else -tmp_adjust
                    )
                if any([condition3, condition4]):
                    tmp_adjust = (
                        adjust if np.linalg.norm(v - v_next) > 20 else adjust * 3 / 2
                    )
                    mod[i] = (
                        tmp_adjust
                        if points[i].x >= points[next_index].x
                        else -tmp_adjust
                    )
        contour.clear()
        for i in range(len(points)):
            contour.appendPoint(
                defcon.Point(
                    (points[i].x, points[i].y + mod[i]),
                    segmentType=points[i].segmentType,
                    smooth=points[i].smooth,
                )
            )


def enhancedline(points, p1, p2, p3, p4):
    global count
    v_limit = 50
    h_limit = 30
    adjust = 3
    if all(
        [
            p1.y == p2.y,
            p3.y == p4.y,
            0 < (p2.y - p3.y) <= v_limit,
            p1.segmentType == "line",
            p2.segmentType == "line",
            p3.segmentType == "line",
            p4.segmentType == "line",
            p1.x - p2.x >= h_limit,
            p4.x - p3.x >= h_limit,
        ]
    ):
        points.append(defcon.Point((p1.x, p1.y), segmentType="line", smooth=True))
        points.append(
            defcon.Point(
                ((p1.x * 3 + p2.x) / 4, p1.y),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                (p2.x - adjust * 3, p2.y + adjust),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                (p3.x + adjust, p3.y - adjust * 3),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                ((p3.x * 3 + p4.x) / 4, p3.y),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(defcon.Point((p4.x, p4.y), segmentType="line", smooth=True))
        count += 3
    elif all(
        [
            p1.y == p2.y,
            p3.y == p4.y,
            0 < (p3.y - p2.y) <= v_limit,
            p1.segmentType == "line",
            p2.segmentType == "line",
            p3.segmentType == "line",
            p4.segmentType == "line",
            p1.x - p2.x >= h_limit,
            p4.x - p3.x >= h_limit,
        ]
    ):
        points.append(defcon.Point((p1.x, p1.y), segmentType="line", smooth=True))
        points.append(
            defcon.Point(
                ((p1.x * 2 + p2.x) / 3, p1.y),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                (p2.x + adjust, p2.y - adjust * 3),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                (p3.x - adjust * 3, p3.y + adjust),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(
            defcon.Point(
                ((p3.x * 2 + p4.x) / 3, p3.y),
                segmentType="line",
                smooth=True,
            )
        )
        points.append(defcon.Point((p4.x, p4.y), segmentType="line", smooth=True))
        count += 3
    else:
        points.append(p1)


def enhansedglyph(glyph):
    global count
    for contour in glyph:
        if len(contour) < 5:
            continue
        points = []
        count = 0
        while count <= len(contour):
            p1 = contour[(count - 3) % len(contour)]
            p2 = contour[(count - 2) % len(contour)]
            p3 = contour[(count - 1) % len(contour)]
            p4 = contour[count % len(contour)]
            enhancedline(points, p1, p2, p3, p4)
            count += 1
        contour.clear()
        for j in range(len(points)):
            contour.appendPoint(
                defcon.Point(
                    (points[j].x, points[j].y),
                    segmentType=points[j].segmentType,
                    smooth=points[j].smooth,
                )
            )


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

    if all([d1 >= d_limit, d2 >= d_limit, p.segmentType == "line"]):

        bx = np.divide(
            (px * (d1 - adjust) + ppx * adjust),
            d1,
            out=np.zeros_like(px, dtype=np.float64),
            where=d1 != 0,
        )
        by = np.divide(
            (py * (d1 - adjust) + ppy * adjust),
            d1,
            out=np.zeros_like(py, dtype=np.float64),
            where=d1 != 0,
        )
        ax = np.divide(
            (px * (d2 - adjust) + pnx * adjust),
            d2,
            out=np.zeros_like(px, dtype=np.float64),
            where=d2 != 0,
        )
        ay = np.divide(
            (py * (d2 - adjust) + pny * adjust),
            d2,
            out=np.zeros_like(py, dtype=np.float64),
            where=d2 != 0,
        )
        m = np.array([px + v1[0] + v2[0], py + v1[1] + v2[1]])
        radius = -1 * v1
        ronated = np.array(
            [
                radius[0] * np.cos(arg12 / 2) - radius[1] * np.sin(arg12 / 2),
                radius[0] * np.sin(arg12 / 2) + radius[1] * np.cos(arg12 / 2),
            ]
        )
        v = np.array([(bx + px * 3 + ax) / 5, (by + py * 3 + ay) / 5])

        points.append(defcon.Point((bx, by), segmentType="curve", smooth=True))
        # points.append(defcon.Point((m[0] - ronated[0], m[1] - ronated[1]), segmentType = None, smooth = True))
        # points.append(defcon.Point((((bx + ax) / 2 + px) / 2, ((by + ay) / 2 + py) / 2), segmentType = None, smooth = True))
        points.append(defcon.Point((v[0], v[1]), segmentType=None, smooth=True))
        points.append(defcon.Point((ax, ay), segmentType="curve", smooth=True))

    elif all([p.segmentType != None, p.segmentType != "curve"]):
        tmp = 4
        bx = (px * tmp + ppx) / (tmp + 1)
        by = (py * tmp + ppy) / (tmp + 1)
        ax = (px * tmp + pnx) / (tmp + 1)
        ay = (py * tmp + pny) / (tmp + 1)
        v = np.array([(bx + px * 3 + ax) / 5, (by + py * 3 + ay) / 5])
        points.append(defcon.Point((bx, by), segmentType="curve", smooth=True))
        points.append(defcon.Point((v[0], v[1]), segmentType=None, smooth=True))
        points.append(defcon.Point((ax, ay), segmentType="curve", smooth=True))

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


first = time.time()

print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] UFOファイル読み込み開始",
)

path = "./NotoSerifJP-SemiBold.otf.ufo"
font = defcon.Font(path=path)

start = time.time()

print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] UFOファイル読み込み終了",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 経過時間: ",
    round(start - first),
    "秒",
)

print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "]",
    font.info.familyName,
    font.info.styleName,
    "を読み込み",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 合計",
    len(font),
    "字",
)
print(
    "[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] コンパイル前処理開始"
)

name = "NType JP alpha"
weight = "SemiBold"
designer = "Nothing Japanese Font Project"
id = "NTYP"
update_font_info(font, name, weight, designer, id)


print("[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] 横画編集開始")

for glyphs in tqdm.tqdm(font):
    unicode = int(str(glyphs.unicode)) if glyphs.unicode != None else 0
    if any(
        [
            0x2E80 <= unicode <= 0x2FDF,
            0x3400 <= unicode <= 0x4DBF,
            0x4E00 <= unicode <= 0x9FFF,
            0xF900 <= unicode <= 0xFAFF,
            0x20000 <= unicode <= 0x3FFFFF,
            unicode == 0x3005,
            unicode == 0x303B,
        ]
    ):
        for contour in glyphs:
            bolderhorizon(contour)


print("[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] 角立て処理開始")


for glyphs in tqdm.tqdm(font):
    unicode = int(str(glyphs.unicode)) if glyphs.unicode != None else 0
    if any(
        [
            0x2E80 <= unicode <= 0x2FDF,
            0x3400 <= unicode <= 0x4DBF,
            0x4E00 <= unicode <= 0x9FFF,
            0xF900 <= unicode <= 0xFAFF,
            0x20000 <= unicode <= 0x3FFFFF,
            unicode == 0x3005,
            unicode == 0x303B,
        ]
    ):
        enhansedglyph(glyphs)


print("[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] 角丸処理開始")

for glyph in tqdm.tqdm(font):
    unicode = int(str(glyph.unicode)) if glyph.unicode != None else 0
    if any(
        [
            0x2E80 <= unicode <= 0x4DBF,
            0x4E00 <= unicode <= 0x9FFF,
            0xF900 <= unicode <= 0xFAFF,
            0x20000 <= unicode <= 0x3FFFFF,
            unicode == 0x3005,
            unicode == 0x303B,
        ]
    ):
        roundify(glyph)


print("[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] 正規化処理開始")

irregular = 0
for glyphs in tqdm.tqdm(font):
    for contour in glyphs:
        points = getpoints(contour)
        for i in range(len(points)):
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
            if p.segmentType == None and p_next.segmentType == "line":
                p.segmentType = "curve"
                irregular += 1

mid = time.time()

print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 修正した制御点: ",
    irregular,
    "個",
)
print(
    "[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] コンパイル前処理終了"
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 経過時間: ",
    round(mid - start),
    "秒",
)

otf = ufo2ft.compileOTF(font)
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
otf.save("./" + now + ".otf")

end = time.time()

print("[", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "] コンパイル終了")
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 経過時間: ",
    round(end - mid),
    "秒",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 合計時間: ",
    round(end - first),
    "秒",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 合計",
    len(font),
    "字",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 処理速度: ",
    round(len(font) / (end - mid)),
    "字/秒",
)
print(
    "[",
    datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    "] 出力ファイル: ",
    now + ".otf",
)
