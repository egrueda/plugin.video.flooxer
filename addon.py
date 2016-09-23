# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Kodi Add-on para Flooxer (http://www.flooxer.com/)
# Version 1.1.0
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Changelog:
# 1.1.0
# - Optimizado funcionamiento
# - Ajustes para forzar miniaturas
# - Iconos y fondo
# 1.0.0
# - First release
#------------------------------------------------------------

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2, json
import urlparse
from urlparse import parse_qsl

my_addon = xbmcaddon.Addon()
my_path = my_addon.getAddonInfo('profile')

args = urlparse.parse_qs(sys.argv[2][1:])
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

# ID del addon
AddonName = xbmc.getInfoLabel('Container.PluginName')
my_addon_id = xbmcaddon.Addon(AddonName).getAddonInfo('id')

# Parametros Flooxer
flooxerApiUrl   = 'https://servicios.flooxer.com/api/'
videoApiURLBase = flooxerApiUrl + 'video/'

# Vista miniatura
force_thumb = my_addon.getSetting('force_thumb')
if force_thumb == "true":
    xbmc.log("force_thumb: " + force_thumb)
    skin_used = xbmc.getSkinDir()
    if skin_used == 'skin.confluence':
        xbmc.executebuiltin('Container.SetViewMode(500)')

def get_categories():
    categories = []
    categories.append({'title': 'Home',         'name': 'home',      'url': flooxerApiUrl + 'front/?page=0'})
    categories.append({'title': 'Original',     'name': 'original',  'url': flooxerApiUrl + 'video/original'})
    categories.append({'title': 'Primero Aquí', 'name': 'premiere',  'url': flooxerApiUrl + 'video/premiere'})
    categories.append({'title': 'Populares',    'name': 'populares', 'url': flooxerApiUrl + 'video/?orderBy=hits%20desc'})
    categories.append({'title': 'Ultimos',      'name': 'ultimos',   'url': flooxerApiUrl + 'video/?orderBy=publicationdate%20desc'})
    return categories

def list_categories():
    # Get video categories
    categories = get_categories()
    listing = []

    for category in categories:
        
        # Iconos para las categorias
        folder_image = "DefaultFolder.png"
        folder_image = "special://home/addons/" + my_addon_id + "/icon.png"

        # Imagen de fondo
        background_image = "special://home/addons/" + my_addon_id + "/fanart.jpg"

        list_item = xbmcgui.ListItem(label=category['title'], iconImage=folder_image)
        list_item.setArt({'fanart': background_image})
        url = '{0}?action=listing&category={1}'.format(_url, category['name'])
        is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def get_videos(category):
    #xbmc.log('get_videos: ' + category)

    # Categoria predeterminada
    if not category:
        category = 'home'

    # URL Predeterminada
    jsonUrl = flooxerApiUrl + 'front/?page=0'

    # Buscamos la URL de la categoria
    categories = get_categories()
    for cat in categories:
        if cat['name'] == category:
            jsonUrl = cat['url']

    #xbmc.log('jsonUrl: ' + jsonUrl)

    # Peticion del JSON
    jsonSrc = makeRequest(jsonUrl)
    #xbmc.log("Recibido jsonSrc: " + jsonSrc)

    # Comprobar formato respuesta
    if (is_json(jsonSrc) == False):
        errorTitle = 'Respuesta no JSON'
        errorMsg = "La respuesta recibida no tiene formato JSON"
        mostrar_errores(errorTitle, errorMsg, jsonSrc)
        return

    # Cargar respuesta en json
    datos = json.loads(jsonSrc)

    # Comprobar error en la respuesta
    if ('error' in datos):
        errorTitle = 'Error procesando vídeos'
        errorMsg = datos['msg']
        mostrar_errores(errorTitle, errorMsg)
        return

    # Devolvemos listado de videos
    videos = datos['content']
    #xbmc.log("Videos:\n" + str(videos))
    return(videos)

def list_videos(category):
    videos = get_videos(category)

    listing = []
    for video in videos:

        # ID del contenido
        video_id = video['id']
        #xbmc.log('video_id: ' + video_id)

        # Comprobar el tipo de json
        if ('datos' in video):
            # Portada
            json_type = 1
        else:
            # Resto de categorias
            json_type = 2
        xbmc.log('JSON Tipo: ' + str(json_type))

        # Leemos los datos en funcion del tipo de json
        if json_type == 1:
            imgPoster = video['datos']['imgPoster']
            titulo = video['datos']['titulo']
        elif json_type == 2:
            imgPoster = video['imgPoster']
            titulo = video['titulo']

        # Informacion del video
        videoJsonData = get_video_info(video_id)
        videoUrl      = videoJsonData['sources'][2]['src']
        videoTitle    = videoJsonData['titulo']
        videoDate     = videoJsonData['publishDate']
        videoDesc     = videoJsonData['descriptionSeo']
        videoDuration = videoJsonData['duration']

        # Imagenes del video
        videoThumb  = imgPoster + '52.jpg'
        videoIcon   = imgPoster + '54.jpg'
        videoFanart = imgPoster + '54.jpg'

        # Generar item
        list_item = xbmcgui.ListItem(label=titulo)
        list_item.setInfo('video', {
            'title': titulo, 
            'genre': 'Sin especificar', 
            'Plot': videoDesc
        })
        list_item.setArt({'thumb': videoThumb, 'icon': videoIcon, 'fanart': videoFanart})
        list_item.setProperty('IsPlayable', 'true')
        url = '{0}?action=play&video={1}'.format(_url, video_id)
        is_folder = False
        listing.append((url, list_item, is_folder))

    # Generar listado
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

# Devolver informacion de un video especifico
def get_video_info(video_id):
    # URL del video
    videoApiURL   = videoApiURLBase + video_id
    videoJsonSrc  = urllib2.urlopen(videoApiURL)
    videoJsonData = json.load(videoJsonSrc)
    return videoJsonData

def play_video(video_id):

    # Informacion del video
    videoJsonData = get_video_info(video_id)

    videoUrl      = videoJsonData['sources'][2]['src']
    videoTitle    = videoJsonData['titulo']
    videoDesc     = videoJsonData['descripcion']
    videoDuration = videoJsonData['duration']

    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=videoUrl)
    play_item.setInfo( type="Video", infoLabels={ 
        "Title": videoTitle, 
        "Duration": videoDuration,
        "Plot": videoDesc
    } )

    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()

# Realizar peticion HTTP
def makeRequest(url):
    xbmc.log("makeRequest: " + url)

    try:
        req      = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data     = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        errorMsg = str(e)
        xbmc.log(errorMsg);
        xbmc.executebuiltin("Notification(Flooxer,"+errorMsg+")")
        data_err = []
        data_err.append(['error', True])
        data_err.append(['msg', errorMsg])
        data_err = json.dumps(data_err)
        data_err = "{\"error\":\"true\", \"msg\":\""+errorMsg+"\"}"
        return data_err

# Comprobar si la cadena es json
def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True

# Mostrar errores
def mostrar_errores(titulo, mensaje, debug=""):
    xbmc.log("ERROR: " + titulo)

    listing = []
    errTitle = "[COLOR red][UPPERCASE]" + titulo + "[/UPPERCASE][/COLOR]"
    errMsg = mensaje + "[CR]Para mas informacion, por favor, consulta el registro."

    list_item = xbmcgui.ListItem(label=errTitle, iconImage='DefaultFolder.png')
    url = '{0}'.format(_url)
    is_folder = True
    listing.append((url, list_item, is_folder))

    list_item = xbmcgui.ListItem(label=errMsg, iconImage='DefaultFolder.png')
    url = '{0}'.format(_url)
    is_folder = True
    listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

    return

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])