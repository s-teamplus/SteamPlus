import Millennium
import PluginUtils
import json
import os
from api_manager import APIManager
from steamplus import steamplusManager
from steam_utils import has_lua_for_app, list_lua_apps
from config import VERSION
from restart_steam import restart_steam
from installdlc import install_dlc

__all__ = [
    'Logger',
    'hasluaForApp', 
    'addViasteamplus',
    'GetStatus',
    'GetLocalLibrary',
    'removeViasteamplus',
    'restartSteam',
    'installDLC'
]

logger = PluginUtils.Logger()

def json_response(data: dict) -> str:
    return json.dumps(data)

def success_response(**kwargs) -> str:
    return json_response({'success': True, **kwargs})

def error_response(error: str, **kwargs) -> str:
    return json_response({'success': False, 'error': error, **kwargs})

def GetPluginDir():
    current_file = os.path.realpath(__file__)
    if current_file.endswith('/main.py/main.py') or current_file.endswith('\\main.py\\main.py'):
        current_file = current_file[:-8]
    elif current_file.endswith('/main.py') or current_file.endswith('\\main.py'):
        current_file = current_file[:-8]

    if current_file.endswith('main.py'):
        backend_dir = os.path.dirname(current_file)
    else:
        backend_dir = current_file

    plugin_dir = os.path.dirname(backend_dir)
    return plugin_dir

class Plugin:
    def __init__(self):
        # Initialize instance variables
        self.plugin_dir = None
        self.backend_path = None
        self.api_manager = None
        self.steamplus_manager = None
        self._injected = False

    def _inject_webkit_files(self):
        if self._injected:
            return

        try:
            js_file_path = os.path.join(self.plugin_dir, '.millennium', 'Dist', 'index.js')

            if os.path.exists(js_file_path):
                Millennium.add_browser_js(js_file_path)
                self._injected = True
            else:
                logger.error(f"steamplus: Bundle not found")
        except Exception as e:
            logger.error(f'steamplus: Failed to inject: {e}')

    def _front_end_loaded(self):
        logger.log("steamplus: v0.1.0 ready - GitHub Version")

    def _load(self):
        global plugin
        plugin = self  # Store instance for module-level functions

        logger.log(f"steamplus: backend loading (v{VERSION})")

        # Initialize plugin components
        self.plugin_dir = GetPluginDir()
        self.backend_path = os.path.join(self.plugin_dir, 'backend')
        self.api_manager = APIManager(self.backend_path)
        self.steamplus_manager = steamplusManager(self.backend_path, self.api_manager)

        self._inject_webkit_files()
        Millennium.ready()
        logger.log("steamplus: backend ready")

    def _unload(self):
        logger.log("Unloading steamplus plugin")

# Global plugin instance - will be set in _load() when Millennium calls it
plugin = None

def get_plugin():
    """Get the plugin instance. Millennium will have already instantiated it."""
    return plugin

class Logger:
    @staticmethod
    def log(message: str) -> str:
        logger.log(f"[Frontend] {message}")
        return success_response()

def hasluaForApp(appid: int) -> str:
    try:
        exists = has_lua_for_app(appid)
        return success_response(exists=exists)
    except Exception as e:
        logger.error(f'hasluaForApp failed for {appid}: {e}')
        return error_response(str(e))

def addViasteamplus(appid: int) -> str:
    try:
        endpoints = plugin.api_manager.get_download_endpoints()
        result = plugin.steamplus_manager.add_via_lua(appid, endpoints)
        return json_response(result)
    except Exception as e:
        logger.error(f'addViasteamplus failed for {appid}: {e}')
        return error_response(str(e))

def GetStatus(appid: int) -> str:
    try:
        result = plugin.steamplus_manager.get_download_status(appid)
        return json_response(result)
    except Exception as e:
        logger.error(f'GetStatus failed for {appid}: {e}')
        return error_response(str(e))

def GetLocalLibrary() -> str:
    try:
        apps = list_lua_apps()
        return success_response(apps=apps)
    except Exception as e:
        logger.error(f'GetLocalLibrary failed: {e}')
        return error_response(str(e))

def removeViasteamplus(appid: int) -> str:
    try:
        result = plugin.steamplus_manager.remove_via_lua(appid)
        return json_response(result)
    except Exception as e:
        logger.error(f'removeViasteamplus failed for {appid}: {e}')
        return error_response(str(e))

def restartSteam() -> str:
    try:
        success = restart_steam()
        if success:
            return success_response(message="Steam reiniciado com sucesso")
        else:
            return error_response("Falha ao reiniciar o Steam")
    except Exception as e:
        logger.error(f'restartSteam failed: {e}')
        return error_response(str(e))
        
def installDLC(appid: int = None) -> str:
    try:
        # Log do AppID recebido
        if appid:
            logger.log(f"steamplus: Instalando DLC's para AppID {appid}")
        else:
            logger.log("steamplus: Instalando DLC's (AppID não especificado)")
        
        # Chama a função de instalação passando o AppID
        success = install_dlc(appid)
        
        if success:
            message = f"Instalação de DLC's iniciada"
            if appid:
                message += f" para AppID {appid}"
            return success_response(message=message)
        else:
            error_msg = "Falha ao iniciar a instalação de DLC's"
            if appid:
                error_msg += f" para AppID {appid}"
            return error_response(error_msg)
    except Exception as e:
        logger.error(f'installDLC failed: {e}')
        return error_response(str(e))

