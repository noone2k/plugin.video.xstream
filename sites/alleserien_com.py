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
URL_MAIN = 'https://alleserien.com'
URL_SERIEN = URL_MAIN + '/serien'
URL_FILME = URL_MAIN + '/filme'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('page', 1)
    params.setParam('genre', 'Alle')
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_SERIEN)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('stype', 'name')
    oGui.addFolder(cGuiElement('Sortiert nach Name', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('stype', 'best')
    oGui.addFolder(cGuiElement('Am besten bewertet', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('stype', 'latest')
    oGui.addFolder(cGuiElement('Neueste Release', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('stype', 'name')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'divider.*?<div[^>]class'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return
    pattern = '#">(.*?)<'
    isMatch, aResult = cParser.parse(sContainer, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    for sName in aResult:
        params.setParam('genre', sName)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    import time
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    stype = params.getValue('stype')
    page = params.getValue('page')
    genre = params.getValue('genre')
    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatch, url = cParser.parseSingleResult(sHtmlContent, "url : '([^']+)")
    isMatch, token = cParser.parseSingleResult(sHtmlContent, "token':'([^']+)")
    oRequest = cRequestHandler(url)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addParameters('_token', token)
    oRequest.addParameters('from', 1900)
    oRequest.addParameters('page', page)
    oRequest.addParameters('rating', 0)
    oRequest.addParameters('sortBy', stype)
    oRequest.addParameters('to', time.strftime("%Y", time.localtime()))
    oRequest.addParameters('type', genre)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '<a title=[^>]"(.*?)" href=[^>]"([^"]+).*?src=[^>]"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail in aResult:
        isTvshow = True if 'folge' in sUrl else False
        sThumbnail = sThumbnail.replace('\/', '/')
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        oGuiElement = cGuiElement(sName[:-1], SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail[:-1])
        oGuiElement.setFanart(sThumbnail[:-1])
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl.replace('\/', '/')[:-1])
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = 'Next.*?data-p=[^>]"([\d]+).*?d-flex'
        isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatch:
            params.setParam('page', sUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'folge' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]class="collapse[^>]m.*?id="s([\d]+)">'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonNr in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        params.setParam('sSeasonNr', sSeasonNr)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'id="s%s">.*?</table>' % sSeasonNr
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    pattern = "href = '([^']+).*?episodeNumber.*?>([\d]+)"
    isMatch, aResult = cParser.parse(sHtmlContainer, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sEpisodeNr in aResult:
        oGuiElement = cGuiElement('Folge ' + str(sEpisodeNr), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setEpisode(sEpisodeNr)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '"partItem" data-id="([\d]+).*?data-controlid="([\d]+)">.*?image/(.*?).png'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    result, sHoster = cParser().parseSingleResult(sHtmlContent, 'controlid.*?url:[^>]"([^"]+)')
    result, token = cParser().parseSingleResult(sHtmlContent, "controlid.*?_token':'([^']+)")
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
        isMatch, sUrl = cParser().parse(sHtmlContent, pattern)
        if not isMatch:
            return
        return [{'streamUrl': sUrl[0], 'resolved': False}]
    else:
        return [{'streamUrl': sUrl, 'resolved': False}]
