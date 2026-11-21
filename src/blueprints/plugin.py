from flask import Blueprint ,request ,jsonify ,current_app ,render_template ,send_from_directory
from plugins .plugin_registry import get_plugin_instance
from utils .app_utils import resolve_path ,handle_request_files ,parse_form
from refresh_task import ManualRefresh ,PlaylistRefresh
import json
import os
import logging
logger =logging .getLogger (__name__ )
plugin_bp =Blueprint ("plugin",__name__ )
def _delete_plugin_instance_images (device_config ,plugin_instance_obj ):
    plugin_image_path =os .path .join (device_config .plugin_image_dir ,plugin_instance_obj .get_image_path ())
    if os .path .exists (plugin_image_path ):
        try :
            os .remove (plugin_image_path )
            logger .info (f"Deleted plugin instance image: {plugin_image_path }")
        except Exception as e :
            logger .warning (f"Failed to delete plugin instance image {plugin_image_path }: {e }")
    try :
        plugin_config =device_config .get_plugin (plugin_instance_obj .plugin_id )
        if plugin_config :
            plugin =get_plugin_instance (plugin_config )
            plugin .cleanup (plugin_instance_obj .settings )
    except Exception as e :
        logger .warning (f"Error during plugin cleanup for {plugin_instance_obj .plugin_id }: {e }")
@plugin_bp .route ('/plugin/<идентификатор_плагина>')
def plugin_page (plugin_id ):
    device_config =current_app .config ['DEVICE_CONFIG']
    playlist_manager =device_config .get_playlist_manager ()
    plugin_config =device_config .get_plugin (plugin_id )
    if plugin_config :
        try :
            plugin =get_plugin_instance (plugin_config )
            template_params =plugin .generate_settings_template ()
            plugin_instance_name =request .args .get ('instance')
            if plugin_instance_name :
                plugin_instance =playlist_manager .find_plugin (plugin_id ,plugin_instance_name )
                if not plugin_instance :
                    return jsonify ({"error":f"Plugin instance: {plugin_instance_name } does not exist"}),500
                template_params ["plugin_settings"]=plugin_instance .settings
                template_params ["plugin_instance"]=plugin_instance_name
            template_params ["playlists"]=playlist_manager .get_playlist_names ()
        except Exception as e :
            logger .exception ("ИСКЛЮЧЕНИЕ: "+str (e ))
            return jsonify ({"error":f"An error occurred: {str (e )}"}),500
        return render_template ('plugin.html',plugin =plugin_config ,**template_params )
    else :
        return "Плагин не найден",404
@plugin_bp .route ('/images/<plugin_id>/<path:filename>')
def image (plugin_id ,filename ):
    plugins_dir =resolve_path ("plugins")
    plugin_dir =os .path .join (plugins_dir ,plugin_id )
    safe_path =os .path .abspath (os .path .join (plugin_dir ,filename ))
    if not safe_path .startswith (os .path .abspath (plugin_dir )):
        return "Неверный путь",403
    abs_plugin_dir =os .path .abspath (plugin_dir )
    if not os .path .isdir (abs_plugin_dir ):
        logger .error (f"Plugin directory not found: {abs_plugin_dir }")
        return "Каталог плагина не найден",404
    if not os .path .isfile (safe_path ):
        logger .error (f"File not found: {safe_path }")
        return "Файл не найден",404
    return send_from_directory (abs_plugin_dir ,filename )
@plugin_bp .route ('/plugin_instance_image/<path:playlist_name>/<path:plugin_id>/<path:instance_name>')
def plugin_instance_image (playlist_name ,plugin_id ,instance_name ):
    device_config =current_app .config ['DEVICE_CONFIG']
    playlist_manager =device_config .get_playlist_manager ()
    playlist =playlist_manager .get_playlist (playlist_name )
    if not playlist :
        return "Плейлист не найден",404
    plugin_instance =playlist .find_plugin (plugin_id ,instance_name )
    if not plugin_instance :
        return "Экземпляр плагина не найден",404
    image_filename =plugin_instance .get_image_path ()
    image_path =os .path .join (device_config .plugin_image_dir ,image_filename )
    if not os .path .exists (image_path ):
        return "Изображение еще не создано",404
    return send_from_directory (device_config .plugin_image_dir ,image_filename )
@plugin_bp .route ('/delete_plugin_instance',methods =['POST'])
def delete_plugin_instance ():
    device_config =current_app .config ['DEVICE_CONFIG']
    playlist_manager =device_config .get_playlist_manager ()
    data =request .json
    playlist_name =data .get ("playlist_name")
    plugin_id =data .get ("plugin_id")
    plugin_instance =data .get ("plugin_instance")
    try :
        playlist =playlist_manager .get_playlist (playlist_name )
        if not playlist :
            return jsonify ({"success":False ,"message":"Плейлист не найден"}),400
        plugin_instance_obj =playlist .find_plugin (plugin_id ,plugin_instance )
        if not plugin_instance_obj :
            return jsonify ({"success":False ,"message":"Экземпляр плагина не найден"}),400
        _delete_plugin_instance_images (device_config ,plugin_instance_obj )
        result =playlist .delete_plugin (plugin_id ,plugin_instance )
        if not result :
            return jsonify ({"success":False ,"message":"Экземпляр плагина не найден"}),400
        device_config .write_config ()
    except Exception as e :
        logger .exception ("ИСКЛЮЧЕНИЕ: "+str (e ))
        return jsonify ({"error":f"An error occurred: {str (e )}"}),500
    return jsonify ({"success":True ,"message":"Удален экземпляр плагина."})
@plugin_bp .route ('/update_plugin_instance/<строка:имя_экземпляра>',methods =['PUT'])
def update_plugin_instance (instance_name ):
    device_config =current_app .config ['DEVICE_CONFIG']
    playlist_manager =device_config .get_playlist_manager ()
    try :
        form_data =parse_form (request .form )
        if not instance_name :
            raise RuntimeError ("Укажите название экземпляра.")
        plugin_settings =form_data
        plugin_settings .update (handle_request_files (request .files ,request .form ))
        plugin_id =plugin_settings .pop ("plugin_id")
        plugin_instance =playlist_manager .find_plugin (plugin_id ,instance_name )
        if not plugin_instance :
            return jsonify ({"error":f"Plugin instance: {instance_name } does not exist"}),500
        plugin_instance .settings =plugin_settings
        device_config .write_config ()
    except Exception as e :
        return jsonify ({"error":f"An error occurred: {str (e )}"}),500
    return jsonify ({"success":True ,"message":f"Updated plugin instance {instance_name }."})
@plugin_bp .route ('/display_plugin_instance',methods =['POST'])
def display_plugin_instance ():
    device_config =current_app .config ['DEVICE_CONFIG']
    refresh_task =current_app .config ['REFRESH_TASK']
    playlist_manager =device_config .get_playlist_manager ()
    data =request .json
    playlist_name =data .get ("playlist_name")
    plugin_id =data .get ("plugin_id")
    plugin_instance_name =data .get ("plugin_instance")
    try :
        playlist =playlist_manager .get_playlist (playlist_name )
        if not playlist :
            return jsonify ({"success":False ,"message":f"Playlist {playlist_name } not found"}),400
        plugin_instance =playlist .find_plugin (plugin_id ,plugin_instance_name )
        if not plugin_instance :
            return jsonify ({"success":False ,"message":f"Plugin instance '{plugin_instance_name }' not found"}),400
        refresh_task .manual_update (PlaylistRefresh (playlist ,plugin_instance ,force =True ))
    except Exception as e :
        return jsonify ({"error":f"An error occurred: {str (e )}"}),500
    return jsonify ({"success":True ,"message":"Дисплей обновлен"}),200
@plugin_bp .route ('/update_now',methods =['POST'])
def update_now ():
    device_config =current_app .config ['DEVICE_CONFIG']
    refresh_task =current_app .config ['REFRESH_TASK']
    display_manager =current_app .config ['DISPLAY_MANAGER']
    try :
        plugin_settings =parse_form (request .form )
        plugin_settings .update (handle_request_files (request .files ))
        plugin_id =plugin_settings .pop ("plugin_id")
        if refresh_task .running :
            refresh_task .manual_update (ManualRefresh (plugin_id ,plugin_settings ))
        else :
            logger .info ("Задача обновления не выполняется, обновление дисплея напрямую")
            plugin_config =device_config .get_plugin (plugin_id )
            if not plugin_config :
                return jsonify ({"error":f"Plugin '{plugin_id }' not found"}),404
            plugin =get_plugin_instance (plugin_config )
            image =plugin .generate_image (plugin_settings ,device_config )
            display_manager .display_image (image ,image_settings =plugin_config .get ("image_settings",[]))
    except Exception as e :
        logger .exception (f"Error in update_now: {str (e )}")
        return jsonify ({"error":f"An error occurred: {str (e )}"}),500
    return jsonify ({"success":True ,"message":"Дисплей обновлен"}),200