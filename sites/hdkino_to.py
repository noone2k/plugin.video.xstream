# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'hdkino_to'
SITE_NAME = 'HDKino.to'
SITE_ICON = 'hdkino_to.png'
SITE_GLOBAL_SEARCH = False
URL_MAIN = 'https://hdkino.to'
URL_FILME = URL_MAIN + '/filme?page=%s'
URL_TOP_FILME = URL_MAIN + '/top?page=%s'
URL_SEARCH = URL_MAIN + '/search/%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('page', 1)
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TOP_FILME)
    oGui.addFolder(cGuiElement('Top Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler('https://hdkino.to/genre').request()
    pattern = '>Genres</div>.*?</div>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]+)".*?>([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContainer, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('//'):
            sUrl = 'https:' + sUrl
        params.setParam('sUrl', sUrl + '?page=%s')
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=None):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    page = params.getValue('page')
    if sSearchText is not None:
        oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    else:
        oRequest = cRequestHandler(entryUrl % page)
    sHtmlContent = oRequest.request()
    pattern = 'search_frame".*?<a[^>]href="([^"]+)"><img[^>]src="([^"]+).*?<strong>([^<]+).*?year/([\d]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName, sYear in aResult:
        sThumbnail = cParser().replace('\d+x\d+', '', sThumbnail)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        if sSearchText is None:
            isMatchNextPage, sNextUrl = cParser().parse(sHtmlContent, "page[^>]([\d]+)")
            if isMatchNextPage:
                if max(sNextUrl) > page:
                    params.setParam('page', int(page) + 1)
                    oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = 'data-video-id="(.*?)"\sdata-provider="(.*?)"'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if isMatch:
        for sID, sName in aResult:
            sHtmlContent = cRequestHandler('https://hdkino.to/embed.php?video_id=' + sID + '&provider=' + sName).request()
            isMatch, aResult = cParser().parse(sHtmlContent, 'src="([^"]+)"')
            for sUrl in aResult:
                hoster = {'link': sUrl, 'name': sName}
                hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText, oGui, sSearchText)
