# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.cCFScrape import cCFScrape
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'filmpalast_to'
SITE_NAME = 'FilmPalast'
SITE_ICON = 'filmpalast.png'

URL_MAIN = 'https://filmpalast.to'
URL_MOVIES = URL_MAIN + '/movies/new'
URL_SHOWS = URL_MAIN + '/serien/view'
URL_TOP = URL_MAIN + '/movies/top'
URL_ENGLISH = URL_MAIN + '/search/genre/Englisch'
URL_SEARCH = URL_MAIN + '/search/title/%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    oGui = cGui()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Neues', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMovieMenu'))
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showSeriesMenu'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showMovieMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TOP)
    oGui.addFolder(cGuiElement('Top Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_ENGLISH)
    oGui.addFolder(cGuiElement('Englisch', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES)
    params.setParam('value', 'genre')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('sUrl', URL_MOVIES)
    params.setParam('value', 'movietitle')
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showValue'), params)
    oGui.setEndOfDirectory()


def showSeriesMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_SHOWS)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('value', 'movietitle')
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showValue'), params)
    oGui.setEndOfDirectory()


def showValue():
    oGui = cGui()
    params = ParameterHandler()
    value = params.getValue("value")
    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    pattern = '<section[^>]id="%s">(.*?)</section>' % value
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    pattern = 'href="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sContainer, pattern)

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
    sHtmlContent = oRequest.request()
    pattern = '"><a[^>]href="([^"]+)"[^>]title="([^"]+)"><img[^>]src="([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        pattern = '</div><a[^>]href="([^"]+)"[^>]title="([^"]+)">.*?img[^>]src="([^"]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        isTvshow, aResult = cParser.parse(sName, 'S\d\dE\d\d')
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = '<a[^>]class="pageing.*?href=([^>]+)>[^>]v'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            if sNextUrl.startswith('/'):
                sNextUrl = URL_MAIN + sNextUrl
            params.setParam('sUrl', sNextUrl.replace("'", "").replace('"', ''))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshow' if isTvshow else 'movie')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("sThumbnail")
    sName = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<a[^>]*class="staffTab"[^>]*data-sid="(\d+)"[^>]*>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    isMatchDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description">([^<]+)')
    total = len(aResult)
    for iSeason in aResult:
        oGuiElement = cGuiElement("Staffel " + str(iSeason), SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(iSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        if isMatchDesc:
            oGuiElement.setDescription(sDesc)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("sThumbnail")
    sSeason = params.getValue('season')
    sShowName = params.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]*class="staffelWrapperLoop[^"]*"[^>]*data-sid="%s">(.*?)</div></li></ul></div>' % sSeason
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]*)"[^>]*class="getStaffelStream"[^>]*>.*?<small>([^>]*?)</small>'
    isMatch, aResult = cParser.parse(sContainer, pattern)
    isMatchDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description">([^<]+)')

    total = len(aResult)
    for sEpisodeUrl, sTitle in aResult:
        oGuiElement = cGuiElement(sTitle, SITE_IDENTIFIER, "showHosters")
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setTVShowTitle(sShowName)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sEpisodeUrl)
        if isMatchDesc:
            oGuiElement.setDescription(sDesc)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'hostName">([^<]+).*?href="([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if isMatch:
        for sName, sUrl in aResult:
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
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
