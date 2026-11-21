from flask import Blueprint ,request ,jsonify ,current_app ,render_template ,send_file
import os
from datetime import datetime
main_bp =Blueprint ("main",__name__ )
@main_bp .route ('/')
def main_page ():
    device_config =current_app .config ['DEVICE_CONFIG']
    return render_template ('inky.html',config =device_config .get_config (),plugins =device_config .get_plugins ())
@main_bp .route ('/api/current_image')
def get_current_image ():
    image_path =os .path .join (os .path .dirname (os .path .dirname (__file__ )),'static','images','current_image.png')
    if not os .path .exists (image_path ):
        return jsonify ({"error":"Изображение не найдено"}),404
    file_mtime =int (os .path .getmtime (image_path ))
    last_modified =datetime .fromtimestamp (file_mtime )
    if_modified_since =request .headers .get ('If-Modified-Since')
    if if_modified_since :
        try :
            client_mtime =datetime .strptime (if_modified_since ,'%a, %d %b %Y %H:%M:%S %Z')
            client_mtime_seconds =int (client_mtime .timestamp ())
            if file_mtime <=client_mtime_seconds :
                return '',304
        except (ValueError ,AttributeError ):
            pass
    response =send_file (image_path ,mimetype ='image/png')
    response .headers ['Last-Modified']=last_modified .strftime ('%a, %d %b %Y %H:%M:%S по Гринвичу')
    response .headers ['Cache-Control']='no-cache'
    return response