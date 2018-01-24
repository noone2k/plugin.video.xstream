# -*- coding: utf-8 -*-
from resources.lib import logger, pyaes
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil
import base64, hashlib, re, urlparse

SITE_IDENTIFIER = 'hd-streams_org'
SITE_NAME = 'HD-Streams'
SITE_ICON = 'hdstreams_org.png'

URL_MAIN = 'https://hd-streams.org/'
URL_FILME = URL_MAIN + 'movies?perPage=54'
URL_SERIE = URL_MAIN + 'seasons?perPage=54'
URL_SEARCH = URL_MAIN + 'search?q=%s&movies=true&seasons=true&actors=false&didyoumean=false'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Filme Genre', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Serien Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = "text: '([^']+)', value: '([^']+)"
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return
    for sName, sID in aResult:
        params.setParam('sUrl', entryUrl + '&genre[]=' + sID)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = 'data-id=.*?">[^>]*<a[^>]href="([^"]+)".*?'
    pattern += "(?:url[^>]'([^']+)?).*?"
    pattern += 'filename">([^<]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return
    cf = createUrl(entryUrl, oRequest)
    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        sYear = re.compile("(.*?)\((\d*)\)").findall(sName)
        for name, year in sYear:
            sName = name
            sYear = year
            break
        isTvshow = True if "series" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail + cf)
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)"[^>]*rel="next"')
    if isMatchNextPage:
        sNextUrl = cUtil.cleanse_text(sNextUrl)
        params.setParam('sUrl', sNextUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
    if not sGui:
        oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = 'click="loadEpisode\S([\d]+).*?subheading">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return
    total = len(aResult)
    for sName, sTitle in aResult:
        oGuiElement = cGuiElement('Folge ' + sName + ' - ' + sTitle, SITE_IDENTIFIER, 'showHosterserie')
        params.setParam('Episodes', sName)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosterserie():
    sUrl = ParameterHandler().getValue('entryUrl')
    Episodes = ParameterHandler().getValue('Episodes')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = "loadEpisodeStream[^>]'%s', '([^']+).*?title>([^<]+)" % Episodes
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)
    pattern = '<meta name="csrf-token" content="([^"]+)">'
    token = re.compile(pattern, flags=re.I | re.M).findall(sHtmlContent)[0]
    hosters = []
    for h, sName in aResult:
        sUrl2 = getLinks(sUrl, Episodes, h, token)
        hoster = {'link': sUrl2, 'name': sName}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = "loadStream[^>]'([^']+)', '([^']+)', '([^']+).*?"
    sPattern += '>.*?>([^"]+)</v-btn>'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)
    pattern = '<meta name="csrf-token" content="([^"]+)">'
    token = re.compile(pattern, flags=re.I | re.M).findall(sHtmlContent)[0]
    hosters = []
    for e, h, sLang, sName in aResult:
        sUrl2 = getLinks(sUrl, e, h, token, sLang)
        hoster = {'link': cUtil.cleanse_text(sUrl2), 'name': cUtil.cleanse_text(sName).strip()}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    results = []
    if 'nxload' in sUrl:
        sHtmlContent = cRequestHandler(sUrl).request()
        sPattern = 'sources.*?"([^"]+)'
        isMatch, sUrl = cParser.parse(sHtmlContent, sPattern)
        return [{'streamUrl': sUrl[0], 'resolved': True}]
    else:
        return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip(), oGui)


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '"title":"([^"]+).*?"url":"([^"]+).*?src":"([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return
    cf = createUrl(entryUrl, oRequest)
    total = len(aResult)
    for sName, sUrl, sThumbnail in aResult:
        sYear = re.compile("(.*?)\((\d*)\)").findall(sName)
        for name, year in sYear:
            sName = name
            sYear = year
            break
        isTvshow = True if "series" in sUrl else False
        oGuiElement = cGuiElement(cUtil.cleanse_text(sName), SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail.replace('\/', '/') + cf)
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('entryUrl', sUrl.replace('\/', '/'))
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        oGui.setEndOfDirectory()


def getLinks(sUrl, e, h, token, sLang=False):
    oRequest = cRequestHandler(sUrl + '/stream')
    oRequest.addHeaderEntry('X-CSRF-TOKEN', token)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addParameters('e', e)
    oRequest.addParameters('h', h)
    if sLang:
        oRequest.addParameters('lang', sLang)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = 'ct[^>]":[^>]"([^"]+).*?iv[^>]":[^>]"([^"]+).*?s[^>]":[^>]"([^"]+).*?e"[^>]([^}]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    for ct, iv, s, e in aResult:
        ct = re.sub(r"\\", "", ct[::-1])
        s = re.sub(r"\\", "", s)
        sUrl2 = evp_decode(ct, base64.b64encode(token), s.decode('hex'))
        return sUrl2.replace('\/', '/').replace('"', '')


def createUrl(sUrl, oRequest):
    parsed_url = urlparse.urlparse(sUrl)
    netloc = parsed_url.netloc[4:] if parsed_url.netloc.startswith('www.') else parsed_url.netloc
    cfId = oRequest.getCookie('__cfduid', '.' + netloc)
    cfClear = oRequest.getCookie('cf_clearance', '.' + netloc)
    if cfId and cfClear and 'Cookie=Cookie:' not in sUrl:
        delimiter = '&' if '|' in sUrl else '|'
        sUrl = delimiter + "Cookie=Cookie: __cfduid=" + cfId.value + "; cf_clearance=" + cfClear.value
    if 'User-Agent=' not in sUrl:
        delimiter = '&' if '|' in sUrl else '|'
        sUrl += delimiter + "User-Agent=" + oRequest.getHeaderEntry('User-Agent')
    return sUrl


def evp_decode(cipher_text, passphrase, salt=None):
    cipher_text = base64.b64decode(cipher_text)
    if not salt:
        salt = cipher_text[8:16]
        cipher_text = cipher_text[16:]
    data = evpKDF(passphrase, salt)
    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(data['key'], data['iv']))
    plain_text = decrypter.feed(cipher_text)
    plain_text += decrypter.feed()
    return plain_text


def evpKDF(passwd, salt, key_size=8, iv_size=4):
    target_key_size = key_size + iv_size
    derived_bytes = ""
    number_of_derived_words = 0
    block = None
    hasher = hashlib.new("md5")
    while number_of_derived_words < target_key_size:
        if block is not None:
            hasher.update(block)
        hasher.update(passwd)
        hasher.update(salt)
        block = hasher.digest()
        hasher = hashlib.new("md5")
        for _i in range(1, 1):
            hasher.update(block)
            block = hasher.digest()
            hasher = hashlib.new("md5")
        derived_bytes += block[0: min(len(block), (target_key_size - number_of_derived_words) * 4)]
        number_of_derived_words += len(block) / 4
    return {
        "key": derived_bytes[0: key_size * 4],
        "iv": derived_bytes[key_size * 4:]
    }
