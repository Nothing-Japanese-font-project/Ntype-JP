import datetime

class MetadataManager:
    """フォントのメタデータ更新を担当するクラス"""

    @staticmethod
    def update(font, name, weight, designer, vendor_id,
               license_text=None, license_url="http://scripts.sil.org/OFL"):
        if license_text is None:
            license_text = (
                "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                'This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS '
                "OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, "
                "permissions and limitations governing your use of this Font Software."
            )

        font.info.familyName = name
        font.info.styleName = weight
        font.info.postscriptFamilyName = name
        font.info.postscriptFullName = f"{name} {weight}"
        font.info.versionMajor = 1
        font.info.versionMinor = 0
        font.info.openTypeNamePreferredFamilyName = name
        font.info.openTypeNamePreferredSubfamilyName = weight
        font.info.openTypeNameFamilyName = name
        font.info.openTypeNameSubfamilyName = weight
        font.info.openTypeNameCompatibleFullName = f"{name} {weight}"
        font.info.openTypeNameUniqueID = f"{vendor_id}-{weight}"
        font.info.openTypeOS2VendorID = vendor_id
        font.info.openTypeNameManufacturer = designer
        font.info.openTypeNameDesigner = designer
        font.info.openTypeNameLicense = license_text
        font.info.openTypeNameLicenseURL = license_url
        font.info.openTypeNameDescription = f"{name} {weight}"
        font.info.openTypeNameSampleText = f"{name} {weight}"
        font.info.openTypeNameWWSFamilyName = name
        font.info.openTypeNameWWSSubfamilyName = weight
        font.info.styleMapFamilyName = name

        font.info.postscriptROS = "Adobe-Identity-0"

        font.info.openTypeNameDesigner = (
            "Ryoko NISHIZUKA 西塚涼子 (kana & ideographs); "
            "Frank Grießhammer (Latin, Greek & Cyrillic); "
            "Wenlong ZHANG 张文龙 (bopomofo); "
            "Sandoll Communications 산돌커뮤니케이션, Soohyun PARK 박수현, Yejin WE 위예진 & Donghoon HAN 한동훈 "
            "(hangul elements, letters & syllables) 'Nothing Japanese Font Project Team'"
        )
        font.info.openTypeNameDesignerURL = "http://www.adobe.com/type/"
        font.info.openTypeNameManufacturer = (
            "Dr. Ken Lunde (project architect, glyph set definition & overall production); "
            "Masataka HATTORI 服部正貴 (production & ideograph elements); "
            "Zachary Quinn Scheuren (variable font & overall production) Nothing Japanese Font Project Team"
        )
