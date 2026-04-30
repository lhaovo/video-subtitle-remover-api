import configparser
import json
import os
from pathlib import Path
from typing import Any

from backend.tools.constant import InpaintMode, SubtitleDetectMode

# 项目版本号
VERSION = "1.4.0"
PROJECT_HOME_URL = "https://github.com/YaoFANGUK/video-subtitle-remover"
PROJECT_ISSUES_URL = PROJECT_HOME_URL + "/issues"
PROJECT_RELEASES_URL = PROJECT_HOME_URL + "/releases"
PROJECT_UPDATE_URLS = [
    "https://api.github.com/repos/YaoFANGUK/video-subtitle-remover/releases/latest",
    "https://accelerate.xdow.net/api/repos/YaoFANGUK/video-subtitle-remover/releases/latest",
]

# 项目的base目录
BASE_DIR = str(Path(os.path.abspath(__file__)).parent)
CONFIG_FILE = os.environ.get("VSR_CONFIG_FILE", "config/config.json")
HARDWARD_ACCELERATION_OPTION = True


class HeadlessConfigItem:
    def __init__(self, value: Any):
        self.value = value


class HeadlessConfig:
    intefaceTexts = {
        "简体中文": "ch",
        "繁體中文": "chinese_cht",
        "English": "en",
        "한국어": "ko",
        "日本語": "japan",
        "Tiếng Việt": "vi",
        "Español": "es",
    }

    def __init__(self):
        self.interface = HeadlessConfigItem("en")
        self.windowX = HeadlessConfigItem(None)
        self.windowY = HeadlessConfigItem(None)
        self.windowW = HeadlessConfigItem(1200)
        self.windowH = HeadlessConfigItem(1200)
        self.subtitleSelectionAreas = HeadlessConfigItem("0.88,0.99,0.15,0.85")
        self.inpaintMode = HeadlessConfigItem(InpaintMode.STTN_AUTO)
        self.subtitleDetectMode = HeadlessConfigItem(SubtitleDetectMode.PP_OCRv5_SERVER)
        self.subtitleYXAxisDifferencePixel = HeadlessConfigItem(10)
        self.subtitleAreaDeviationPixel = HeadlessConfigItem(10)
        self.subtitleAreaYAxisDifferencePixel = HeadlessConfigItem(20)
        self.subtitleAreaPixelToleranceYPixel = HeadlessConfigItem(20)
        self.subtitleAreaPixelToleranceXPixel = HeadlessConfigItem(20)
        self.subtitleTimelineBackwardFrameCount = HeadlessConfigItem(3)
        self.subtitleTimelineForwardFrameCount = HeadlessConfigItem(3)
        self.sttnNeighborStride = HeadlessConfigItem(5)
        self.sttnReferenceLength = HeadlessConfigItem(10)
        self.sttnMaxLoadNum = HeadlessConfigItem(50)
        self.propainterMaxLoadNum = HeadlessConfigItem(70)
        self.hardwareAcceleration = HeadlessConfigItem(HARDWARD_ACCELERATION_OPTION)
        self.checkUpdateOnStartup = HeadlessConfigItem(True)
        self.saveDirectory = HeadlessConfigItem("")

    def getSttnMaxLoadNum(self):
        return max(self.sttnMaxLoadNum.value, self.sttnNeighborStride.value * self.sttnReferenceLength.value)

    def set(self, item: HeadlessConfigItem, value: Any) -> None:
        item.value = value


def _enum_from_value(enum_type, value):
    if isinstance(value, enum_type):
        return value
    for member in enum_type:
        if value in (member.value, member.name):
            return member
    return value


def _load_headless_config() -> HeadlessConfig:
    loaded = HeadlessConfig()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError:
        return loaded

    main = raw.get("Main", {})
    window = raw.get("Window", {})
    propainter = raw.get("ProPainter", {})
    sttn = raw.get("Sttn", {})
    loaded.interface.value = window.get("Interface", loaded.interface.value)
    loaded.windowX.value = window.get("X", loaded.windowX.value)
    loaded.windowY.value = window.get("Y", loaded.windowY.value)
    loaded.windowW.value = window.get("Width", loaded.windowW.value)
    loaded.windowH.value = window.get("Height", loaded.windowH.value)
    loaded.subtitleSelectionAreas.value = main.get("SubtitleSelectionAreas", loaded.subtitleSelectionAreas.value)
    loaded.inpaintMode.value = _enum_from_value(InpaintMode, main.get("InpaintMode", loaded.inpaintMode.value))
    loaded.subtitleDetectMode.value = _enum_from_value(
        SubtitleDetectMode,
        main.get("SubtitleDetectMode", loaded.subtitleDetectMode.value),
    )
    loaded.subtitleYXAxisDifferencePixel.value = main.get(
        "SubtitleYXAxisDifferencePixel",
        loaded.subtitleYXAxisDifferencePixel.value,
    )
    loaded.subtitleAreaDeviationPixel.value = main.get(
        "SubtitleAreaDeviationPixel",
        loaded.subtitleAreaDeviationPixel.value,
    )
    loaded.subtitleAreaYAxisDifferencePixel.value = main.get(
        "SubtitleAreaYAxisDifferencePixel",
        loaded.subtitleAreaYAxisDifferencePixel.value,
    )
    loaded.subtitleAreaPixelToleranceYPixel.value = main.get(
        "SubtitleAreaPixelToleranceYPixel",
        loaded.subtitleAreaPixelToleranceYPixel.value,
    )
    loaded.subtitleAreaPixelToleranceXPixel.value = main.get(
        "SubtitleAreaPixelToleranceXPixel",
        loaded.subtitleAreaPixelToleranceXPixel.value,
    )
    loaded.subtitleTimelineBackwardFrameCount.value = main.get(
        "SubtitleTimelineBackwardFrameCount",
        loaded.subtitleTimelineBackwardFrameCount.value,
    )
    loaded.subtitleTimelineForwardFrameCount.value = main.get(
        "subtitleTimelineForwardFrameCount",
        loaded.subtitleTimelineForwardFrameCount.value,
    )
    loaded.hardwareAcceleration.value = main.get("HardwareAcceleration", loaded.hardwareAcceleration.value)
    loaded.checkUpdateOnStartup.value = main.get("CheckUpdateOnStartup", loaded.checkUpdateOnStartup.value)
    loaded.saveDirectory.value = main.get("SaveDirectory", loaded.saveDirectory.value)
    loaded.sttnNeighborStride.value = sttn.get("NeighborStride", loaded.sttnNeighborStride.value)
    loaded.sttnReferenceLength.value = sttn.get("ReferenceLength", loaded.sttnReferenceLength.value)
    loaded.sttnMaxLoadNum.value = sttn.get("MaxLoadNum", loaded.sttnMaxLoadNum.value)
    loaded.propainterMaxLoadNum.value = propainter.get("MaxLoadNum", loaded.propainterMaxLoadNum.value)
    return loaded


try:
    from qfluentwidgets import (
        BoolValidator,
        ConfigItem,
        ConfigValidator,
        EnumSerializer,
        OptionsConfigItem,
        OptionsValidator,
        QConfig,
        RangeConfigItem,
        RangeValidator,
        qconfig,
    )

    class Config(QConfig):
        intefaceTexts = HeadlessConfig.intefaceTexts
        interface = OptionsConfigItem("Window", "Interface", "ChineseSimplified", OptionsValidator(intefaceTexts.values()), restart=True)
        windowX = ConfigItem("Window", "X", None)
        windowY = ConfigItem("Window", "Y", None)
        windowW = ConfigItem("Window", "Width", 1200)
        windowH = ConfigItem("Window", "Height", 1200)
        subtitleSelectionAreas = ConfigItem("Main", "SubtitleSelectionAreas", "0.88,0.99,0.15,0.85")
        inpaintMode = OptionsConfigItem("Main", "InpaintMode", InpaintMode.STTN_AUTO, OptionsValidator(InpaintMode), EnumSerializer(InpaintMode))
        subtitleDetectMode = OptionsConfigItem("Main", "SubtitleDetectMode", SubtitleDetectMode.PP_OCRv5_SERVER, OptionsValidator(SubtitleDetectMode), EnumSerializer(SubtitleDetectMode))
        subtitleYXAxisDifferencePixel = RangeConfigItem("Main", "SubtitleYXAxisDifferencePixel", 10, RangeValidator(0, 300))
        subtitleAreaDeviationPixel = RangeConfigItem("Main", "SubtitleAreaDeviationPixel", 10, RangeValidator(1, 300))
        subtitleAreaYAxisDifferencePixel = RangeConfigItem("Main", "SubtitleAreaYAxisDifferencePixel", 20, RangeValidator(0, 300))
        subtitleAreaPixelToleranceYPixel = RangeConfigItem("Main", "SubtitleAreaPixelToleranceYPixel", 20, RangeValidator(0, 300))
        subtitleAreaPixelToleranceXPixel = RangeConfigItem("Main", "SubtitleAreaPixelToleranceXPixel", 20, RangeValidator(0, 300))
        subtitleTimelineBackwardFrameCount = RangeConfigItem("Main", "SubtitleTimelineBackwardFrameCount", 3, RangeValidator(0, 300))
        subtitleTimelineForwardFrameCount = RangeConfigItem("Main", "subtitleTimelineForwardFrameCount", 3, RangeValidator(0, 300))
        sttnNeighborStride = RangeConfigItem("Sttn", "NeighborStride", 5, RangeValidator(1, 100))
        sttnReferenceLength = RangeConfigItem("Sttn", "ReferenceLength", 10, RangeValidator(1, 100))
        sttnMaxLoadNum = RangeConfigItem("Sttn", "MaxLoadNum", 50, RangeValidator(1, 300))
        getSttnMaxLoadNum = lambda self: max(self.sttnMaxLoadNum.value, self.sttnNeighborStride.value * self.sttnReferenceLength.value)
        propainterMaxLoadNum = RangeConfigItem("ProPainter", "MaxLoadNum", 70, RangeValidator(1, 300))
        hardwareAcceleration = ConfigItem("Main", "HardwareAcceleration", HARDWARD_ACCELERATION_OPTION, BoolValidator())
        checkUpdateOnStartup = ConfigItem("Main", "CheckUpdateOnStartup", True, BoolValidator())
        saveDirectory = ConfigItem("Main", "SaveDirectory", "", ConfigValidator())

    config = Config()
    qconfig.load(CONFIG_FILE, config)
except ImportError:
    config = _load_headless_config()

# 向后兼容：旧的 SubtitleDetectMode 枚举值为中文，迁移为新值
_detect_mode_value = config.subtitleDetectMode.value
if isinstance(_detect_mode_value, str) and _detect_mode_value in ("快速", "Fast"):
    config.set(config.subtitleDetectMode, SubtitleDetectMode.PP_OCRv5_MOBILE)
elif isinstance(_detect_mode_value, str) and _detect_mode_value in ("精准", "Precise"):
    config.set(config.subtitleDetectMode, SubtitleDetectMode.PP_OCRv5_SERVER)

tr = configparser.ConfigParser()
TRANSLATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interface", f"{config.interface.value}.ini")
tr.read(TRANSLATION_FILE, encoding="utf-8")

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
