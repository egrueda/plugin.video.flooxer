# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Kodi Add-on para Flooxer (http://www.flooxer.com/)
# Version 1.2.0
#------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
#------------------------------------------------------------
# Changelog:
# 1.2.0
# - Navegacion por categorias
# - Opcion para habilitar debug
# - Nuevo icono
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
my_path = my_addon.getAddonInfo('path').decode('utf-8')
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

# Categorias y tipo de cada una
def get_categories():
    categories = []
    categories.append({'title': 'Original',     'name': 'original',  'tipo': 1, 'url': flooxerApiUrl + 'video/original?page=0&size=500'})
    categories.append({'title': 'Primero Aquí', 'name': 'premiere',  'tipo': 1, 'url': flooxerApiUrl + 'video/premiere?page=0&size=500'})
    categories.append({'title': 'Populares',    'name': 'populares', 'tipo': 1, 'url': flooxerApiUrl + 'video/?orderBy=hits%20desc&page=0&size=500'})
    categories.append({'title': 'Ultimos',      'name': 'ultimos',   'tipo': 1, 'url': flooxerApiUrl + 'video/?orderBy=publicationdate%20desc&page=0&size=500'})
    categories.append({'title': 'Creadores',    'name': 'creadores', 'tipo': 2, 'url': 'prescriber'})
    categories.append({'title': 'Formatos',     'name': 'formatos',  'tipo': 2, 'url': 'format'})
    categories.append({'title': 'Canales',      'name': 'canales',   'tipo': 2, 'url': 'channel'})
    categories.append({'title': 'Géneros',      'name': 'generos',   'tipo': 2, 'url': 'genre'})
    return categories

# Obtener listado de categorias
def list_categories():
    # Get video categories
    categories = get_categories()
    listing = []

    for category in categories:
        
        # Iconos para las categorias
        folder_image = "DefaultFolder.png"
        folder_image = "special://home/addons/" + my_addon_id + "/icon.png"
        icon = '%s/icon.png' %my_path

        # Imagen de fondo
        background_image = "special://home/addons/" + my_addon_id + "/fanart.jpg"

        list_item = xbmcgui.ListItem(label=category['title'], iconImage=icon)
        if category['tipo'] == 1:
            url = '{0}?action=listing&category={1}'.format(_url, category['name'])
        else:
            url = '{0}?action=items&category={1}'.format(_url, category['name'])

        is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

# Leer videos de categoria tipo 1
def get_videos(category):
    #save_debug('get_videos: ' + category)
    save_debug('get_videos: ' + category)

    # Buscamos la URL de la categoria
    categories = get_categories()
    for cat in categories:
        if cat['name'] == category:
            jsonUrl = cat['url']

    if jsonUrl[:4] != 'http':
        jsonUrl = '{0}{1}/?orderBy=name%20asc&page=0&size=500'.format(flooxerApiUrl,jsonUrl)

    # Peticion del JSON
    save_debug("Peticion jsonUrl: " + jsonUrl)
    jsonSrc = makeRequest(jsonUrl)
    #save_debug("Recibido jsonSrc: " + jsonSrc)

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
        errorTitle = 'Error procesando ví­deos'
        errorMsg = datos['msg']
        mostrar_errores(errorTitle, errorMsg)
        return

    # Devolvemos listado de videos
    videos = datos['content']
    #save_debug("Videos:\n" + str(videos))
    return(videos)

# Leer videos de categoria tipo 2
def get_videos2(category,item_id):
    save_debug('get_videos2: ' + category)

    # Buscamos la URL de la categoria
    categories = get_categories()
    for cat in categories:
        if cat['name'] == category:
            jsonUrl = cat['url']

    jsonUrl = '{0}{1}/{2}/videos/?&orderBy=publicationdate%20desc&page=0&size=500'.format(flooxerApiUrl,jsonUrl,item_id)

    #save_debug('jsonUrl: ' + jsonUrl)

    # Peticion del JSON
    jsonSrc = makeRequest(jsonUrl)
    #save_debug("Recibido jsonSrc: " + jsonSrc)

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
    #save_debug("Videos:\n" + str(videos))
    return(videos)

def list_videos(category,item_id=''):
    if item_id == '':
        videos = get_videos(category)
    else:
        videos = get_videos2(category,item_id)

    listing = []
    for video in videos:

        # ID del contenido
        video_id = video['id']
        #save_debug('video_id: ' + video_id)

        # Comprobar el tipo de json
        if ('datos' in video):
            # Portada
            json_type = 1
        else:
            # Resto de categorias
            json_type = 2
        save_debug('JSON Tipo: ' + str(json_type))

        # Leemos los datos en funcion del tipo de json
        if json_type == 1:
            imgPoster = video['datos']['imgPoster']
            titulo = video['datos']['titulo']
        elif json_type == 2:
            imgPoster = video['imgPoster']
            titulo = video['titulo']

        # Informacion del video
        #videoJsonData = get_video_info(video_id)
        #videoUrl      = videoJsonData['sources'][2]['src']
        #videoTitle    = videoJsonData['titulo']
        #videoDate     = videoJsonData['publishDate']
        #videoDesc     = videoJsonData['descriptionSeo']
        #videoDuration = videoJsonData['duration']

        # Imagenes del video
        videoThumb  = imgPoster + '52.jpg'
        videoIcon   = imgPoster + '54.jpg'
        videoFanart = imgPoster + '54.jpg'

        # Generar item
        list_item = xbmcgui.ListItem(label=titulo)
        list_item.setInfo('video', {
            'title': titulo, 
            'genre': 'Sin especificar', 
            #	'Plot': videoDesc
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

def list_items(category):
    save_debug('Ejecutando list_items (' + category + ')')
    videos = get_videos(category)

    listing = []
    for video in videos:

        # ID del contenido
        itemId = video['id']
        save_debug('Leyendo itemId: ' + itemId)

        # Comprobar el tipo de json
        if ('datos' in video):
            # Portada
            json_type = 1
        else:
            # Resto de categorias
            json_type = 2
        save_debug('JSON Tipo: ' + str(json_type))

        # Leemos los datos en funcion del tipo de json
        if json_type == 1:
            imgPoster = video['datos']['imghead']
            titulo = video['datos']['name']
        elif json_type == 2:
            imgPoster = video['imghead']
            titulo = video['name']

        # Informacion del video
        #videoJsonData = get_video_info(video_id)
        #videoUrl      = videoJsonData['sources'][2]['src']
        #videoTitle    = videoJsonData['titulo']
        #videoDate     = videoJsonData['publishDate']
        #videoDesc     = videoJsonData['descriptionSeo']
        #videoDuration = videoJsonData['duration']

        # Imagenes del video
        videoThumb  = imgPoster + '52.jpg'
        videoIcon   = imgPoster + '54.jpg'
        videoFanart = imgPoster + '54.jpg'

        # Generar item
        list_item = xbmcgui.ListItem(label=titulo)
        list_item.setInfo('video', {'title': titulo, 'genre': 'Sin especificar'})
        list_item.setArt({'thumb': videoThumb, 'icon': videoIcon, 'fanart': videoFanart})
        #list_item.setProperty('IsPlayable', 'true')
        url = '{0}?action=listing2&item={1}&category={2}'.format(_url, itemId, category)
        is_folder = True
        listing.append((url, list_item, is_folder))

    # Generar listado
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)

def play_video(video_id):

    # URL del video
    videoApiURL   = videoApiURLBase + video_id
    save_debug("video_id: " + video_id)
    save_debug("videoApiURL: " + videoApiURL)
    videoJsonSrc  = urllib2.urlopen(videoApiURL)
    videoJsonData = json.load(videoJsonSrc)
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

def get_video_info(video_id):
    save_debug('Obteniendo informacion del video ID: ' + video_id)
    # URL del video
    videoApiURL   = videoApiURLBase + video_id
    videoJsonSrc  = urllib2.urlopen(videoApiURL)
    videoJsonData = json.load(videoJsonSrc)
    return videoJsonData

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
            list_videos(params['category'],'')
        elif params['action'] == 'items':
            # Play a video from a provided URL.
            list_items(params['category'])
        if params['action'] == 'listing2':
            # Display the list of videos in a provided category.
            list_videos(params['category'],params['item'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()

# Realizar peticion HTTP
def makeRequest(url):
    save_debug("makeRequest: " + url)

    try:
        req      = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data     = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        errorMsg = str(e)
        save_debug(errorMsg);
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
    save_debug("ERROR: " + titulo)

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

def save_debug(log_string):
    debug_enabled = my_addon.getSetting('debug_enabled')
    if debug_enabled == "true":
        xbmc.log("FLOXER [debug]: " + log_string)
    else:
        return True

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])