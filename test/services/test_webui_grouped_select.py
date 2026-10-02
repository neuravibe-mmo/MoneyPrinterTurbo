from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app.config import config
from app.services import voice


ROOT_DIR = Path(__file__).parent.parent.parent
WEBUI_MAIN = ROOT_DIR / "webui" / "Main.py"


@contextmanager
def _running_app(*args, saved_video_source="pexels"):
    """在整个用例期间保持配置和外部音色查询隔离。"""
    test_app_config = dict(config.app, video_source=saved_video_source)
    test_ui_config = dict(config.ui, language="en")
    with (
        patch.object(config, "app", test_app_config),
        patch.object(config, "ui", test_ui_config),
        patch.object(config, "try_save_config", return_value=True),
        patch.object(
            voice,
            "get_all_azure_voices",
            return_value=["en-US-JennyNeural-Female"],
        ),
    ):
        app = AppTest.from_file(str(WEBUI_MAIN), default_timeout=60)
        app.session_state["ui_language"] = "en"
        app.run()
        assert [str(item.value) for item in app.exception] == []
        yield app


def test_grouped_video_source_applies_first_change_and_allows_switching_back():
    """一次选择操作就应更新业务状态，并允许切换回原选项。"""
    with _running_app() as app:
        source_box = next(
            item for item in app.selectbox if item.key == "video_source_select_en"
        )
        assert app.session_state["video_source_select_en"] == "pexels"
        assert source_box.value == "pexels"

        source_box.set_value("pixabay").run()
        assert [str(item.value) for item in app.exception] == []
        assert app.session_state["video_source_select_en"] == "pixabay"

        source_box = next(
            item for item in app.selectbox if item.key == "video_source_select_en"
        )
        source_box.set_value("pexels").run()
        assert [str(item.value) for item in app.exception] == []
        assert app.session_state["video_source_select_en"] == "pexels"


def test_grouped_video_source_ignores_unknown_event_and_repairs_saved_value():
    """过期配置不能让页面进入未知素材来源状态。"""
    with _running_app(saved_video_source="removed-provider") as app:
        assert app.session_state["video_source_select_en"] == "pexels"
        source_box = next(
            item for item in app.selectbox if item.key == "video_source_select_en"
        )
        assert source_box.value == "pexels"


def test_grouped_video_source_keeps_groups_and_accessible_label_binding():
    """下拉框应包含全部预设素材来源选项。"""
    with _running_app() as app:
        source_box = next(
            item for item in app.selectbox if item.key == "video_source_select_en"
        )
        assert list(source_box.options) == [
            "[Stock Video] Pexels",
            "[Stock Video] Pixabay",
            "[Stock Video] Coverr",
            "[AI Video] Metaso · MiniMax H3",
            "[AI Video] OFox AI Video",
            "[AI Video] Shengsuan Cloud AI Video",
            "[AI Video] Volcano Engine Ark · Seedance",
            "[AI Video] WaveSpeed AI Video",
            "[AI Video] MuAPI AI Video",
            "[AI Image] OpenAI Compatible Text-to-Image",
            "[Local Files] Local file",
        ]


def test_stock_concurrency_only_appears_for_stock_sources():
    """库存并发仅对三家库存素材显示，切换来源时保留显式设置。"""
    with _running_app() as app:
        stock = next(
            item for item in app.selectbox
            if item.key.startswith("material_concurrency_select_")
        )
        clip = next(
            item for item in app.selectbox
            if item.key.startswith("clip_rendering_concurrency_select_")
        )
        assert stock.value == 1
        assert clip.value == 1

        stock.set_value(4).run()
        clip = next(
            item for item in app.selectbox
            if item.key.startswith("clip_rendering_concurrency_select_")
        )
        clip.set_value(2).run()
        assert config.app["material_concurrency"] == 4
        assert config.app["video_clip_concurrency"] == 2

        for source, show_stock in (
            ("pixabay", True),
            ("coverr", True),
            ("wavespeed", False),
            ("local", False),
            ("pexels", True),
        ):
            source_box = next(
                item for item in app.selectbox if item.key == "video_source_select_en"
            )
            source_box.set_value(source).run()
            assert [str(item.value) for item in app.exception] == []
            stock_widgets = [
                item for item in app.selectbox
                if item.key.startswith("material_concurrency_select_")
            ]
            assert bool(stock_widgets) is show_stock
            if show_stock:
                assert stock_widgets[0].value == 4
            assert next(
                item for item in app.selectbox
                if item.key.startswith("clip_rendering_concurrency_select_")
            ).value == 2
            assert config.app["material_concurrency"] == 4

