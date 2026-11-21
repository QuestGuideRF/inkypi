import threading
import time
import os
import logging
import psutil
import pytz
from datetime import datetime ,timezone
from plugins .plugin_registry import get_plugin_instance
from utils .image_utils import compute_image_hash
from model import RefreshInfo ,PlaylistManager
from PIL import Image
logger =logging .getLogger (__name__ )
class RefreshTask :
    def __init__ (self ,device_config ,display_manager ):
        self .device_config =device_config
        self .display_manager =display_manager
        self .thread =None
        self .lock =threading .Lock ()
        self .condition =threading .Condition (self .lock )
        self .running =False
        self .manual_update_request =()
        self .refresh_event =threading .Event ()
        self .refresh_event .set ()
        self .refresh_result ={}
    def start (self ):
        if not self .thread or not self .thread .is_alive ():
            logger .info ("Запуск задачи обновления")
            self .thread =threading .Thread (target =self ._run ,daemon =True )
            self .running =True
            self .thread .start ()
    def stop (self ):
        with self .condition :
            self .running =False
            self .condition .notify_all ()
        if self .thread :
            logger .info ("Остановка задачи обновления")
            self .thread .join ()
    def _run (self ):
        while True :
            try :
                with self .condition :
                    sleep_time =self .device_config .get_config ("plugin_cycle_interval_seconds",default =60 *60 )
                    self .condition .wait (timeout =sleep_time )
                    self .refresh_result ={}
                    self .refresh_event .clear ()
                    if not self .running :
                        break
                    playlist_manager =self .device_config .get_playlist_manager ()
                    latest_refresh =self .device_config .get_refresh_info ()
                    current_dt =self ._get_current_datetime ()
                    refresh_action =None
                    if self .manual_update_request :
                        logger .info ("Запрошено обновление вручную")
                        refresh_action =self .manual_update_request
                        self .manual_update_request =()
                    else :
                        if self .device_config .get_config ("log_system_stats"):
                            self .log_system_stats ()
                        logger .info (f"Running interval refresh check. | current_time: {current_dt .strftime ('%Y-%m-%d %H:%M:%S')}")
                        playlist ,plugin_instance =self ._determine_next_plugin (playlist_manager ,latest_refresh ,current_dt )
                        if plugin_instance :
                            refresh_action =PlaylistRefresh (playlist ,plugin_instance )
                    if refresh_action :
                        plugin_config =self .device_config .get_plugin (refresh_action .get_plugin_id ())
                        if plugin_config is None :
                            logger .error (f"Plugin config not found for '{refresh_action .get_plugin_id ()}'.")
                            continue
                        plugin =get_plugin_instance (plugin_config )
                        image =refresh_action .execute (plugin ,self .device_config ,current_dt )
                        image_hash =compute_image_hash (image )
                        refresh_info =refresh_action .get_refresh_info ()
                        refresh_info .update ({"refresh_time":current_dt .isoformat (),"image_hash":image_hash })
                        if image_hash !=latest_refresh .image_hash :
                            logger .info (f"Updating display. | refresh_info: {refresh_info }")
                            self .display_manager .display_image (image ,image_settings =plugin .config .get ("image_settings",[]))
                        else :
                            logger .info (f"Image already displayed, skipping refresh. | refresh_info: {refresh_info }")
                        self .device_config .refresh_info =RefreshInfo (**refresh_info )
                        self .device_config .write_config ()
            except Exception as e :
                logger .exception ('Исключение во время обновления')
                self .refresh_result ["exception"]=e
            finally :
                self .refresh_event .set ()
    def manual_update (self ,refresh_action ):
        if self .running :
            with self .condition :
                self .manual_update_request =refresh_action
                self .refresh_result ={}
                self .refresh_event .clear ()
                self .condition .notify_all ()
            self .refresh_event .wait ()
            if self .refresh_result .get ("exception"):
                raise self .refresh_result .get ("exception")
        else :
            logger .warn ("Задача фонового обновления не запущена, невозможно выполнить обновление вручную.")
    def signal_config_change (self ):
        if self .running :
            with self .condition :
                self .condition .notify_all ()
    def _get_current_datetime (self ):
        tz_str =self .device_config .get_config ("timezone",default ="UTC")
        return datetime .now (pytz .timezone (tz_str ))
    def _determine_next_plugin (self ,playlist_manager ,latest_refresh_info ,current_dt ):
        playlist =playlist_manager .determine_active_playlist (current_dt )
        if not playlist :
            playlist_manager .active_playlist =None
            logger .info (f"No active playlist determined.")
            return None ,None
        playlist_manager .active_playlist =playlist .name
        if not playlist .plugins :
            logger .info (f"Active playlist '{playlist .name }' has no plugins.")
            return None ,None
        latest_refresh_dt =latest_refresh_info .get_refresh_datetime ()
        plugin_cycle_interval =self .device_config .get_config ("plugin_cycle_interval_seconds",default =3600 )
        should_refresh =PlaylistManager .should_refresh (latest_refresh_dt ,plugin_cycle_interval ,current_dt )
        if not should_refresh :
            latest_refresh_str =latest_refresh_dt .strftime ('%Y-%m-%d %H:%M:%S')if latest_refresh_dt else "None"
            logger .info (f"Not time to update display. | latest_update: {latest_refresh_str } | plugin_cycle_interval: {plugin_cycle_interval }")
            return None ,None
        plugin =playlist .get_next_plugin ()
        logger .info (f"Determined next plugin. | active_playlist: {playlist .name } | plugin_instance: {plugin .name }")
        return playlist ,plugin
    def log_system_stats (self ):
        metrics ={
        'cpu_percent':psutil .cpu_percent (interval =1 ),
        'memory_percent':psutil .virtual_memory ().percent ,
        'disk_percent':psutil .disk_usage ('/').percent ,
        'load_avg_1_5_15':os .getloadavg (),
        'swap_percent':psutil .swap_memory ().percent ,
        'net_io':{
        'bytes_sent':psutil .net_io_counters ().bytes_sent ,
        'bytes_recv':psutil .net_io_counters ().bytes_recv
        }
        }
        logger .info (f"System Stats: {metrics }")
class RefreshAction :
    def refresh (self ,plugin ,device_config ,current_dt ):
        raise NotImplementedError ("Подклассы должны реализовывать метод обновления.")
    def get_refresh_info (self ):
        raise NotImplementedError ("Подклассы должны реализовывать метод get_refresh_info.")
    def get_plugin_id (self ):
        raise NotImplementedError ("Подклассы должны реализовывать метод get_plugin_id.")
class ManualRefresh (RefreshAction ):
    def __init__ (self ,plugin_id :str ,plugin_settings :dict ):
        self .plugin_id =plugin_id
        self .plugin_settings =plugin_settings
    def execute (self ,plugin ,device_config ,current_dt :datetime ):
        return plugin .generate_image (self .plugin_settings ,device_config )
    def get_refresh_info (self ):
        return {"refresh_type":"Обновление вручную","plugin_id":self .plugin_id }
    def get_plugin_id (self ):
        return self .plugin_id
class PlaylistRefresh (RefreshAction ):
    def __init__ (self ,playlist ,plugin_instance ,force =False ):
        self .playlist =playlist
        self .plugin_instance =plugin_instance
        self .force =force
    def get_refresh_info (self ):
        return {
        "refresh_type":"Playlist",
        "playlist":self .playlist .name ,
        "plugin_id":self .plugin_instance .plugin_id ,
        "plugin_instance":self .plugin_instance .name
        }
    def get_plugin_id (self ):
        return self .plugin_instance .plugin_id
    def execute (self ,plugin ,device_config ,current_dt :datetime ):
        plugin_image_path =os .path .join (device_config .plugin_image_dir ,self .plugin_instance .get_image_path ())
        if self .plugin_instance .should_refresh (current_dt )or self .force :
            logger .info (f"Refreshing plugin instance. | plugin_instance: '{self .plugin_instance .name }'")
            image =plugin .generate_image (self .plugin_instance .settings ,device_config )
            image .save (plugin_image_path )
            self .plugin_instance .latest_refresh_time =current_dt .isoformat ()
        else :
            logger .info (f"Not time to refresh plugin instance, using latest image. | plugin_instance: {self .plugin_instance .name }.")
            with Image .open (plugin_image_path )as img :
                image =img .copy ()
        return image