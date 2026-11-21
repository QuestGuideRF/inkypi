import os ,logging .config
from pi_heif import register_heif_opener
logging .config .fileConfig (os .path .join (os .path .dirname (__file__ ),'config','logging.conf'))
import warnings
warnings .filterwarnings ("ignore",message =".*Ожидание занято: держится на высоком уровне.*")
import os
import random
import time
import sys
import json
import logging
import threading
import argparse
from utils .app_utils import generate_startup_image
from flask import Flask ,request
from werkzeug .serving import is_running_from_reloader
from config import Config
from display .display_manager import DisplayManager
from refresh_task import RefreshTask
from blueprints .main import main_bp
from blueprints .settings import settings_bp
from blueprints .plugin import plugin_bp
from blueprints .playlist import playlist_bp
from jinja2 import ChoiceLoader ,FileSystemLoader
from plugins .plugin_registry import load_plugins
from waitress import serve
logger =logging .getLogger (__name__ )
parser =argparse .ArgumentParser (description ='Сервер отображения InkyPi')
parser .add_argument ('--dev',action ='store_true',help ='Запустить в режиме разработки')
args =parser .parse_args ()
if args .dev :
    Config .config_file =os .path .join (Config .BASE_DIR ,"config","device_dev.json")
    DEV_MODE =True
    PORT =8080
    logger .info ("Запуск InkyPi в режиме РАЗРАБОТКИ на порту 8080.")
else :
    DEV_MODE =False
    PORT =80
    logger .info ("Запуск InkyPi в ПРОИЗВОДСТВЕННОМ режиме на порту 80")
logging .getLogger ('waitress.queue').setLevel (logging .ERROR )
app =Flask (__name__ )
template_dirs =[
os .path .join (os .path .dirname (__file__ ),"templates"),
os .path .join (os .path .dirname (__file__ ),"plugins"),
]
app .jinja_loader =ChoiceLoader ([FileSystemLoader (directory )for directory in template_dirs ])
device_config =Config ()
display_manager =DisplayManager (device_config )
refresh_task =RefreshTask (device_config ,display_manager )
load_plugins (device_config .get_plugins ())
app .config ['DEVICE_CONFIG']=device_config
app .config ['DISPLAY_MANAGER']=display_manager
app .config ['REFRESH_TASK']=refresh_task
app .config ['MAX_FORM_PARTS']=10_000
app .register_blueprint (main_bp )
app .register_blueprint (settings_bp )
app .register_blueprint (plugin_bp )
app .register_blueprint (playlist_bp )
register_heif_opener ()
if __name__ =='__main__':
    refresh_task .start ()
    if device_config .get_config ("startup")is True :
        logger .info ("Флаг запуска установлен, отображается заставка.")
        img =generate_startup_image (device_config .get_resolution ())
        display_manager .display_image (img )
        device_config .update_value ("startup",False ,write =True )
    try :
        app .secret_key =str (random .randint (100000 ,999999 ))
        if DEV_MODE :
            import socket
            try :
                s =socket .socket (socket .AF_INET ,socket .SOCK_DGRAM )
                s .connect (("8.8.8.8",80 ))
                local_ip =s .getsockname ()[0 ]
                s .close ()
                logger .info (f"Serving on http://{local_ip }:{PORT }")
            except :
                pass
        serve (app ,host ="0.0.0.0",port =PORT ,threads =1 )
    finally :
        refresh_task .stop ()