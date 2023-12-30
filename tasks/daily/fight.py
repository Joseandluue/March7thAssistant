from managers.screen_manager import screen
from managers.config_manager import config
from managers.logger_manager import logger
from managers.translate_manager import _
from tasks.base.base import Base
from tasks.base.pythonchecker import PythonChecker
from tasks.base.command import subprocess_with_timeout, subprocess_with_timeout1
import subprocess
import shutil
import os


class Fight:

    @staticmethod
    def update():
        if os.path.exists(os.path.join(config.fight_exe_path, "map")):
            shutil.rmtree(os.path.join(config.fight_exe_path, "map"))
        from module.update.update_handler import UpdateHandler
        from tasks.base.fastest_mirror import FastestMirror
        if config.fight_operation_mode == "exe":
            import requests
            import json
            response = requests.get(FastestMirror.get_github_api_mirror("moesnow", "Fhoe-Rail", "fight-latest.json", 1), timeout=3)
            if response.status_code == 200:
                data = json.loads(response.text)
                for asset in data["assets"]:
                    url = FastestMirror.get_github_mirror(asset["browser_download_url"])
                    break
                update_handler = UpdateHandler(url, config.fight_exe_path, "Fhoe-Rail")
                update_handler.run()
        elif config.fight_operation_mode == "source":
            config.set_value("fight_requirements", False)
            url = FastestMirror.get_github_mirror("https://github.com/Starry-Wind/StarRailAssistant/archive/main.zip")
            update_handler = UpdateHandler(url, config.fight_source_path, "StarRailAssistant-main")
            update_handler.run()

    @staticmethod
    def check_path():
        status = False
        path_to_check = ""
        if config.fight_operation_mode == "exe":
            path_to_check = os.path.join(config.fight_exe_path, "Fhoe-Rail.exe")
            if not os.path.exists(path_to_check):
                status = True
        elif config.fight_operation_mode == "source":
            path_to_check = os.path.join(config.fight_source_path, "Honkai_Star_Rail.py")
            if not os.path.exists(path_to_check):
                status = True 
        if status:
            logger.warning(_("锄大地路径不存在: {path}").format(path=path_to_check))
            Fight.update()

    @staticmethod
    def check_requirements():
        if not config.fight_requirements:
            logger.info(_("开始安装依赖"))
            from tasks.base.fastest_mirror import FastestMirror
            subprocess.run([config.python_exe_path, "-m", "pip", "install", "-i", FastestMirror.get_pypi_mirror(), "pip", "--upgrade"])
            while not subprocess.run([config.python_exe_path, "-m", "pip", "install", "-i", FastestMirror.get_pypi_mirror(), "-r", "requirements.txt"], check=True, cwd=config.fight_source_path):
                logger.error(_("依赖安装失败"))
                input(_("按回车键重试. . ."))
            logger.info(_("依赖安装成功"))
            config.set_value("fight_requirements", True)

    @staticmethod
    def before_start():
        Fight.check_path()
        if config.fight_operation_mode == "source":
            PythonChecker.run()
            Fight.check_requirements()
        return True

    @staticmethod
    def start():
        logger.hr(_("准备锄大地"), 2)
        if Fight.before_start():
            # 切换队伍
            if config.fight_team_enable:
                Base.change_team(config.fight_team_number)

            logger.info(_("开始锄大地"))
            screen.change_to('universe_main')
            screen.change_to('main')

            status = False
            if config.fight_operation_mode == "exe":
                if subprocess_with_timeout([os.path.join(config.fight_exe_path, "Fhoe-Rail.exe")], config.fight_timeout * 3600, config.fight_exe_path):
                    status = True
            elif config.fight_operation_mode == "source":
                if subprocess_with_timeout1([config.python_exe_path, "Honkai_Star_Rail.py"], config.fight_timeout * 3600, config.fight_source_path, config.env):
                    status = True
            if status:
                config.save_timestamp("fight_timestamp")
                Base.send_notification_with_screenshot(_("🎉锄大地已完成🎉"))
                return True

        logger.error(_("锄大地失败"))
        Base.send_notification_with_screenshot(_("⚠️锄大地未完成⚠️"))
        return False

    @staticmethod
    def gui():
        if Fight.before_start():
            if config.fight_operation_mode == "exe":
                if subprocess.run(["start", "Fhoe-Rail.exe", "--debug"], shell=True, check=True, cwd=config.fight_exe_path):
                    return True
            elif config.fight_operation_mode == "source":
                if subprocess.run([config.python_exe_path, "Honkai_Star_Rail.py"], shell=True, check=True, cwd=config.fight_source_path, env=config.env):
                    return True
        return False
