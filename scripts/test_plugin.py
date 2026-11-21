import json
from src .plugins .plugin_registry import load_plugins ,get_plugin_instance
from src .utils .image_utils import resize_image ,change_orientation
from unittest .mock import patch ,MagicMock
from PIL import Image
PLUGIN_CONFIG_FILE ="install/config_base/plugins.json"
RESOLUTIONS =[
[400 ,300 ],
[640 ,400 ],
[600 ,448 ],
[800 ,480 ],
]
ORIENTATIONS =["horizontal","vertical"]
plugin_id ="ai_text"
plugin_settings ={
"title":"Сегодня в истории",
"textModel":"gpt-4o",
"textPrompt":"idk",
"selectedFrame":"Rectangle"
}
mock_device_config =MagicMock ()
with open (PLUGIN_CONFIG_FILE )as f :
    plugins =json .load (f )
plugin_config =[config for config in plugins if config .get ('id')==plugin_id ]
if not plugin_config :
    exit (f"Plugin {plugin_id } not found in plugin config file: {PLUGIN_CONFIG_FILE }")
load_plugins (plugin_config )
plugin_config =plugin_config [0 ]
plugin_instance =get_plugin_instance (plugin_config )
total_height =sum ([max (resolution )for resolution in RESOLUTIONS ])
total_width =max ([max (resolution )for resolution in RESOLUTIONS ])*2
composite =Image .new ('RGB',(total_width ,total_height ),color ='gray')
y =0
for resolution in RESOLUTIONS :
    x =0
    width ,height =resolution
    for orientation in ORIENTATIONS :
        mock_device_config .get_resolution .return_value =resolution
        mock_device_config .get_config .return_value =orientation
        img =plugin_instance .generate_image (plugin_settings ,mock_device_config )
        img =change_orientation (img ,orientation )
        img =resize_image (img ,resolution ,plugin_config .get ('image_settings',[]))
        if orientation =="vertical":
            img =img .rotate (-90 ,expand =1 )
        composite .paste (img ,(x ,y ))
        x =int (total_width /2 )
    y +=max (width ,height )
composite .show ()