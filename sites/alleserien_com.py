# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.cCFScrape import cCFScrape
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'alleserien_com'
SITE_NAME = 'Alleserien.com'
SITE_ICON = 'alleserien_com.png'
SITE_GLOBAL_SEARCH = False
URL_MAIN = 'http://www.alleserien.com'
URL_POPULAR_FILME = URL_MAIN + '/popular-filme'
URL_POPULAR_SERIE = URL_MAIN + '/popular'
URL_GENRE_FILM = URL_MAIN + '/filme'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_POPULAR_FILME)
    oGui.addFolder(cGuiElement('Popular Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRE_FILM)
    oGui.addFolder(cGuiElement('Film Genres', SITE_IDENTIFIER, 'showGenres'), params)
    params.setParam('sUrl', URL_POPULAR_SERIE)
    oGui.addFolder(cGuiElement('Popular Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Serien Genres', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'homeContentGenresList">.*?</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+)">([^<]+)')

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
    request = cRequestHandler(entryUrl)
    sHtmlContent = request.request()
    pattern = '6">.*?<a href="([^"]+)" title="([^"]+).*?<img src="([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        isTvshow = True if 'folge' in sUrl else False
        sThumbnail = cCFScrape.createUrl(sThumbnail, request)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        oGui.setView('tvshows' if 'folge' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]class="hosterSiteDirectNav".*?<div[^>]class="cf">'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    pattern = 'href="([^"]+)"[^>]title="([^"]+)">([\d]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sSeasonNr in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        params.setParam('sUrl', sUrl)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<li>[^>]<a[^>]href="([^"]+)".*?">([\d]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sLink, sEpisodeNr in aResult:
        oGuiElement = cGuiElement('Folge ' + str(sEpisodeNr), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setEpisode(sEpisodeNr)
        params.setParam('entryUrl', sLink)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'class="PartChange"[^>]data-id="([\d]+).*?data-controlid="([\d]+)">.*?alt="([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    result, sHoster = cParser().parseSingleResult(sHtmlContent, '".PartChange".*?url:[^>]"([^"]+)')
    result, token = cParser().parseSingleResult(sHtmlContent, "_token':'([^']+)")

    hosters = []
    if isMatch:
        for ID, controlid, sName in aResult:
            request = cRequestHandler(sHoster)
            request.addParameters('_token', token)
            request.addParameters('PartID', ID)
            request.addParameters('ControlID', controlid)
            request.setRequestType(1)
            sHtmlContent = request.request()
            result, link = cParser().parseSingleResult(sHtmlContent, 'src="([^"]+)')
            hoster = {'link': link, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    ref = ParameterHandler().getValue('entryUrl')
    if 'alleserien' in sUrl:
        request = cRequestHandler(sUrl)
        request.addHeaderEntry('Referer', ref)
        request.addHeaderEntry('Host', 'www.alleserienplayer.com')
        request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
        sHtmlContent = request.request()
        pattern = 'file":"([^"]+)'
        isMatch, sUrl2 = cParser().parse(sHtmlContent, pattern)
        if not isMatch:
            return
        return [{'streamUrl': sUrl2[0], 'resolved': False}]
    else:
        return [{'streamUrl': sUrl, 'resolved': False}]
