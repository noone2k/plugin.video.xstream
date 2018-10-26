# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'movie2k_ag'
SITE_NAME = 'Movie2k AG'
SITE_ICON = 'movie2k_ag.png'

URL_MAIN = 'https://movie2k.ag/'
URL_MOVIE = URL_MAIN + '%s'
URL_SEARCH = URL_MAIN + '?c=movie&m=filter&keyword=%s'
URL_HOSTER = 'https://api.vodlocker.to/embed/movieStreams/?id=%s&lang=2&cat=movie'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIE % 'releases')
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'featured')
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'views')
    oGui.addFolder(cGuiElement('Beliebte Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'updates')
    oGui.addFolder(cGuiElement('Updates', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'rating')
    oGui.addFolder(cGuiElement('Top IMDB', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = '">Genre</a>.*?</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    isMatch, aResult = cParser.parse(sHtmlContainer, "href='([^']+)'>([^<]+)")

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Cookie', 'approve_search=yes')
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]id="post-([\d]+)".*?<a[^>]*class="clip-link".*?title="([^"]+).*?<img src="([^"]+).*?<span>(.*?)</p>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sID, sName, sThumbnail, sDesc in aResult:
        isYear, sYear = cParser().parse(sName, '(.*?)\((\d*)\)')
        for name, year in sYear:
            sName = name
            sYear = year
            break
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setDescription(sDesc.replace('	', ' '))
        oGuiElement.setYear(sYear)
        params.setParam('sID', sID)
        params.setParam('sName', sName)
        params.setParam('sYear', sYear)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<a[^>]*href="([^"]+)">&gt')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl.replace('amp;',''))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    params = ParameterHandler()
    sID = params.getValue('sID')
    sName = params.getValue('sName')
    sYear = params.getValue('sYear')
    sHtmlContent = cRequestHandler('https://api.vodlocker.to/embed?id=' + sID + '&t=' + sName + '&y=' + sYear + '&referrer=link&server=1').request()
    pattern = "<source[^>]src='([^']+).*?data-res='([\d]+)'"
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if isMatch:
        for sUrl, sName in aResult:
            hoster = {'link': sUrl, 'name': 'CDN ' + sName}
            hosters.append(hoster)
    sHtmlContent = cRequestHandler(URL_HOSTER % sID).request()
    pattern = "<a[^>]*href='([^']+)'(?:[^>]*player.*?, \"([^\"]+)\")?.*?<span[^>]*class='?url'?[^>]*>(.*?)</span>"
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sHref, sEmbeded, sName in aResult:
            hoster = {'link': (sEmbeded if sEmbeded else sHref), 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': True if 'vodlocker' in sUrl else False}]

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
