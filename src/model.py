import os
import json
import logging
from datetime import datetime ,timedelta
logger =logging .getLogger (__name__ )
class RefreshInfo :
    def __init__ (self ,refresh_type ,plugin_id ,refresh_time ,image_hash ,playlist =None ,plugin_instance =None ):
        self .refresh_time =refresh_time
        self .image_hash =image_hash
        self .refresh_type =refresh_type
        self .plugin_id =plugin_id
        self .playlist =playlist
        self .plugin_instance =plugin_instance
    def get_refresh_datetime (self ):
        latest_refresh =None
        if self .refresh_time :
            latest_refresh =datetime .fromisoformat (self .refresh_time )
        return latest_refresh
    def to_dict (self ):
        refresh_dict ={
        "refresh_time":self .refresh_time ,
        "image_hash":self .image_hash ,
        "refresh_type":self .refresh_type ,
        "plugin_id":self .plugin_id ,
        }
        if self .playlist :
            refresh_dict ["playlist"]=self .playlist
        if self .plugin_instance :
            refresh_dict ["plugin_instance"]=self .plugin_instance
        return refresh_dict
    @classmethod
    def from_dict (cls ,data ):
        return cls (
        refresh_time =data .get ("refresh_time"),
        image_hash =data .get ("image_hash"),
        refresh_type =data .get ("refresh_type"),
        plugin_id =data .get ("plugin_id"),
        playlist =data .get ("playlist"),
        plugin_instance =data .get ("plugin_instance")
        )
class PlaylistManager :
    DEFAULT_PLAYLIST_START ="00:00"
    DEFAULT_PLAYLIST_END ="24:00"
    def __init__ (self ,playlists =[],active_playlist =None ):
        self .playlists =playlists
        self .active_playlist =active_playlist
    def get_playlist_names (self ):
        return [p .name for p in self .playlists ]
    def add_default_playlist (self ):
        return self .playlists .append (
        Playlist ("Default",PlaylistManager .DEFAULT_PLAYLIST_START ,PlaylistManager .DEFAULT_PLAYLIST_END ,[]))
    def find_plugin (self ,plugin_id ,instance ):
        for playlist in self .playlists :
            plugin =playlist .find_plugin (plugin_id ,instance )
            if plugin :
                return plugin
        return None
    def determine_active_playlist (self ,current_datetime ):
        current_time =current_datetime .strftime ("%H:%M")
        active_playlists =[p for p in self .playlists if p .is_active (current_time )]
        if not active_playlists :
            return None
        active_playlists .sort (key =lambda p :p .get_priority ())
        playlist =active_playlists [0 ]
        return playlist
    def get_playlist (self ,playlist_name ):
        return next ((p for p in self .playlists if p .name ==playlist_name ),None )
    def add_plugin_to_playlist (self ,playlist_name ,plugin_data ):
        playlist =self .get_playlist (playlist_name )
        if playlist :
            if playlist .add_plugin (plugin_data ):
                return True
        else :
            logger .warning (f"Playlist '{playlist_name }' not found.")
        return False
    def add_playlist (self ,name ,start_time =None ,end_time =None ):
        if not start_time :
            start_time =PlaylistManager .DEFAULT_PLAYLIST_START
        if not end_time :
            end_time =PlaylistManager .DEFAULT_PLAYLIST_END
        self .playlists .append (Playlist (name ,start_time ,end_time ))
        return True
    def update_playlist (self ,old_name ,new_name ,start_time ,end_time ):
        playlist =self .get_playlist (old_name )
        if playlist :
            playlist .name =new_name
            playlist .start_time =start_time
            playlist .end_time =end_time
            return True
        logger .warning (f"Playlist '{old_name }' not found.")
        return False
    def delete_playlist (self ,name ):
        self .playlists =[p for p in self .playlists if p .name !=name ]
    def to_dict (self ):
        return {
        "playlists":[p .to_dict ()for p in self .playlists ],
        "active_playlist":self .active_playlist
        }
    @classmethod
    def from_dict (cls ,data ):
        return cls (
        playlists =[Playlist .from_dict (p )for p in data .get ("playlists",[])],
        active_playlist =data .get ("active_playlist")
        )
    @staticmethod
    def should_refresh (latest_refresh ,interval_seconds ,current_time ):
        if not latest_refresh :
            return True
        return (current_time -latest_refresh )>=timedelta (seconds =interval_seconds )
class Playlist :
    def __init__ (self ,name ,start_time ,end_time ,plugins =None ,current_plugin_index =None ):
        self .name =name
        self .start_time =start_time
        self .end_time =end_time
        self .plugins =[PluginInstance .from_dict (p )for p in (plugins or [])]
        self .current_plugin_index =current_plugin_index
    def is_active (self ,current_time ):
        if self .start_time <=self .end_time :
            return self .start_time <=current_time <self .end_time
        else :
            return current_time >=self .start_time or current_time <self .end_time
    def add_plugin (self ,plugin_data ):
        if self .find_plugin (plugin_data ["plugin_id"],plugin_data ["name"]):
            logger .warning (f"Plugin '{plugin_data ['plugin_id']}' with instance '{plugin_data ['name']}' already exists.")
            return False
        self .plugins .append (PluginInstance .from_dict (plugin_data ))
        return True
    def update_plugin (self ,plugin_id ,instance_name ,updated_data ):
        plugin =self .find_plugin (plugin_id ,instance_name )
        if plugin :
            plugin .update (updated_data )
            return True
        logger .warning (f"Plugin '{plugin_id }' with name '{instance_name }' not found.")
        return False
    def delete_plugin (self ,plugin_id ,name ):
        initial_count =len (self .plugins )
        self .plugins =[p for p in self .plugins if not (p .plugin_id ==plugin_id and p .name ==name )]
        if len (self .plugins )==initial_count :
            logger .warning (f"Plugin '{plugin_id }' with instance '{name }' not found.")
            return False
        return True
    def find_plugin (self ,plugin_id ,name ):
        return next ((p for p in self .plugins if p .plugin_id ==plugin_id and p .name ==name ),None )
    def get_next_plugin (self ):
        if self .current_plugin_index is None :
            self .current_plugin_index =0
        else :
            self .current_plugin_index =(self .current_plugin_index +1 )%len (self .plugins )
        return self .plugins [self .current_plugin_index ]
    def get_priority (self ):
        return self .get_time_range_minutes ()
    def get_time_range_minutes (self ):
        start =datetime .strptime (self .start_time ,"%H:%M")
        if self .end_time !="24:00":
            end =datetime .strptime (self .end_time ,"%H:%M")
        else :
            end =datetime .strptime ("00:00","%H:%M")
            end +=timedelta (days =1 )
        if end <start :
            end +=timedelta (days =1 )
        return int ((end -start ).total_seconds ()//60 )
    def to_dict (self ):
        return {
        "name":self .name ,
        "start_time":self .start_time ,
        "end_time":self .end_time ,
        "plugins":[p .to_dict ()for p in self .plugins ],
        "current_plugin_index":self .current_plugin_index
        }
    @classmethod
    def from_dict (cls ,data ):
        return cls (
        name =data ["name"],
        start_time =data ["start_time"],
        end_time =data ["end_time"],
        plugins =data ["plugins"],
        current_plugin_index =data .get ("current_plugin_index",None )
        )
class PluginInstance :
    def __init__ (self ,plugin_id ,name ,settings ,refresh ,latest_refresh_time =None ):
        self .plugin_id =plugin_id
        self .name =name
        self .settings =settings
        self .refresh =refresh
        self .latest_refresh_time =latest_refresh_time
    def update (self ,updated_data ):
        for key ,value in updated_data .items ():
            setattr (self ,key ,value )
    def should_refresh (self ,current_time ):
        latest_refresh_dt =self .get_latest_refresh_dt ()
        if not latest_refresh_dt :
            return True
        if "interval"in self .refresh :
            interval =self .refresh .get ("interval")
            if interval and (current_time -latest_refresh_dt )>=timedelta (seconds =interval ):
                return True
        if "scheduled"in self .refresh :
            scheduled_time_str =self .refresh .get ("scheduled")
            latest_refresh_str =latest_refresh_dt .strftime ("%H:%M")
            if latest_refresh_str <scheduled_time_str :
                return True
        if "scheduled"in self .refresh :
            scheduled_time_str =self .refresh .get ("scheduled")
            scheduled_time =datetime .strptime (scheduled_time_str ,"%H:%M").time ()
            latest_refresh_date =latest_refresh_dt .date ()
            current_date =current_time .date ()
            if (latest_refresh_date <current_date and current_time .time ()>=scheduled_time )or (latest_refresh_date ==current_date and latest_refresh_dt .time ()<scheduled_time <=current_time .time ()):
                return True
        return False
    def get_image_path (self ):
        return f"{self .plugin_id }_{self .name .replace (' ','_')}.png"
    def get_latest_refresh_dt (self ):
        latest_refresh =None
        if self .latest_refresh_time :
            latest_refresh =datetime .fromisoformat (self .latest_refresh_time )
        return latest_refresh
    def to_dict (self ):
        return {
        "plugin_id":self .plugin_id ,
        "name":self .name ,
        "plugin_settings":self .settings ,
        "refresh":self .refresh ,
        "latest_refresh_time":self .latest_refresh_time ,
        }
    @classmethod
    def from_dict (cls ,data ):
        return cls (
        plugin_id =data ["plugin_id"],
        name =data ["name"],
        settings =data ["plugin_settings"],
        refresh =data ["refresh"],
        latest_refresh_time =data .get ("latest_refresh_time"),
        )