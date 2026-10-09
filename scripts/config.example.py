"""路径配置。所有路径都可以用环境变量覆盖，或直接修改本文件。

使用前请确认以下路径指向你自己的文件：
  LC_GAME_DIR   Limbus Company 游戏根目录
  LC_KR_DIR     韩文剧情目录（游戏内 Resources_moved/.../Localize/kr/StoryData）
  LC_ZH_DIR     中文汉化剧情目录（LLC 汉化包 .../LLC_zh-CN/StoryData）
  LC_BANK_DIR   语音 bank 目录（.../StreamingAssets/Assets/Sound/FMODBuilds/Desktop）
  LC_MDX        Naver 韩汉词典 .mdx（可选，用于逐词释义）
"""
import os

ROOT = os.environ.get("LC_ANKI_ROOT", os.path.dirname(os.path.abspath(__file__)))
GAME = os.environ.get("LC_GAME_DIR", r"E:\Steam\steamapps\common\Limbus Company")

KRD = os.environ.get("LC_KR_DIR", os.path.join(
    GAME, r"LimbusCompany_Data\Assets\Resources_moved\Localize\kr\StoryData"))
ZHD = os.environ.get("LC_ZH_DIR", r"D:\powershellfild\LimbusLocalize_2026100501\LimbusCompany_Data\Lang\LLC_zh-CN\StoryData")
BANKDIR = os.environ.get("LC_BANK_DIR", os.path.join(
    GAME, r"LimbusCompany_Data\StreamingAssets\Assets\Sound\FMODBuilds\Desktop"))
MDX = os.environ.get("LC_MDX", "")

MEDIA = os.path.join(ROOT, "media")
