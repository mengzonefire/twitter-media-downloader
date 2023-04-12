'''
Author: mengzonefire
Date: 2021-09-21 09:20:04
LastEditTime: 2023-04-10 14:12:30
LastEditors: mengzonefire
Description: 工具模块, 快1k行了, 抽空分模块拆分一下
'''
import json
import sys
import time
import queue
import traceback
import httpx
import argparse
from common.text import *
from common.const import *
from common.logger import writeLog
from argparse import RawTextHelpFormatter

isWinPlatform = sys.platform in ['win32', 'win64']
if isWinPlatform:
    import winreg


def clear():
    if sys.platform in ['win32', 'win64']:  # 判断是否为win平台
        os.system('cls')
    else:
        os.system('clear')


def getHttpText(httpCode: int):
    if httpCode in httpCodeText:
        return httpCodeText[httpCode]
    return f'请前往issue页反馈:\n{issue_page}'


def initalArgs():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-c', '--cookie', dest='cookie', type=str,
                        help='for access locked users&tweets, default use cfg file, input " " to clear')
    parser.add_argument('-p', '--proxy', dest='proxy', type=str,
                        help='support http&socks5, default use cfg file, input " " to clear')
    parser.add_argument('-d', '--dir', dest='dir',
                        type=str, help='set download path, default: twitter_media_download/ or use cfg file')
    parser.add_argument('-n', '--num', dest='concurrency', type=int,
                        help='downloader concurrency, default: 8 or use cfg file')
    parser.add_argument('-t', '--type', dest='type', type=str,
                        help='desired media type, default: photo&animated_gif&video&full_text or use cfg file')
    parser.add_argument('-f', '--fileName', dest='fileName', type=str,
                        help='output fileName, valid var: {userId},{twtId},{ori},{date},{time},{type}\ndefault: {userName}-{twtId}-{date}_{time}-{type} or use cfg file')
    parser.add_argument('-m', '--media', action="store_true", dest='media',
                        help='exclude non-media tweets')
    parser.add_argument('-q', '--quoted', action="store_true", dest='quoted',
                        help='exclude quoted tweets')
    parser.add_argument('-r', '--retweeted', action="store_true", dest='retweeted',
                        help='exclude retweeted')
    parser.add_argument('-v', '--version', action='store_true',
                        help='show version and check update')
    parser.add_argument('url', type=str, nargs='*', help=url_args_help)
    args = parser.parse_args()
    setContext('args', args)


def argsHandler():
    args = getContext('args')
    if args.version:
        print('version: {}\ndonate page: {}\nissue page: {}\n'.format(
            version, donate_page, issue_page))
        checkUpdate()
        return
    if args.proxy:
        if not setProxy(args.proxy):
            return
    if args.cookie:
        if not setCookie(args.cookie):
            return
    if args.dir:
        setContext('dl_path', args.dir)
    if args.concurrency:
        setContext('concurrency', args.concurrency)
    if args.type:
        setContext('type', args.type)
    if args.fileName:
        if not len(p_unexpect_var.findall(args.fileName)):
            setContext('fileName', re.sub(
                r'[\\/:*?"<>|]', '', args.fileName.strip()))
        else:
            print(unexpectVar_arg_warning)
            return
    setContext('media', not args.media)
    setContext('quoted', not args.quoted)
    setContext('retweeted', not args.retweeted)
    saveEnv()
    print(save_cfg_finsh.format(conf_path))
    showConfig()


def getGuestCookie():  # 获取游客token
    headers = getContext('headers')
    if headers['Cookie'] or 'x-guest-token' in headers:  # cookie/游客token已配置
        return True
    with httpx.Client(proxies=getContext('proxy'), headers=getContext('headers'), timeout=5, verify=False) as client:
        for i in range(1, 6):
            try:
                response = client.post(hostUrl).json()
                break
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
                if i >= 5:
                    print(network_error_warning)
                    return False
                else:
                    print(timeout_warning.format(i))
                    time.sleep(1)
    if 'guest_token' in response:
        x_guest_token = response['guest_token']
        headers['x-guest-token'] = x_guest_token
        setContext('headers', headers)
        return True
    else:
        print(token_warning)
        input(exit_ask)
        exit()


def getToken(cookie):  # 从cookie内提取csrf token
    csrf_token = p_csrf_token.findall(cookie)
    if len(csrf_token) != 0:
        return csrf_token[0]
    else:
        return None


def getSysProxy():
    if not isWinPlatform:  # 非win平台, 跳过
        return
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings")
    proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
    if proxy_enable:
        proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
        if 'socks=' in proxy_server:
            setContext('proxy', f'socks5://{proxy_server}')
        else:
            setContext('proxy', f'http://{proxy_server}')


def setCookie(cookie=''):  # 设置cookie
    inputFlag = False
    headers = getContext("headers")
    if not cookie:  # 输入cookie
        inputFlag = True
        clear()
        cookie = input(input_cookie_ask).strip()
        clear()
        if cookie == '0':
            return True
    elif cookie == ' ':  # 清除cookie
        cookie = ''
    else:
        cookie = cookie.strip()
    if cookie:  # 设置cookie
        token = getToken(cookie)
        if token:
            headers['x-csrf-token'] = token
            headers['Cookie'] = cookie
        else:  # 格式错误
            if inputFlag:
                input(cookie_input_warning)
                return setCookie()
            else:
                print(cookie_arg_warning)
                return False
    else:
        headers['Cookie'] = ''
    setContext('headers', headers)
    return True


def setProxy(proxy=''):
    inputFlag = False
    if not proxy:  # 输入代理
        inputFlag = True
        clear()
        proxy = input(input_proxy_ask).strip()
        clear()
        if proxy == '0':
            return True
        elif proxy == '1':
            getSysProxy()
            return True
        elif proxy == '':
            setContext('proxy', None)
            return True
    elif proxy == ' ':
        setContext('proxy', None)
        return True
    else:  # 命令行参数
        proxy = proxy.strip()
    proxyMatch = pProxy.match(proxy)
    proxyMatch2 = pProxy2.match(proxy)
    if proxyMatch2:
        setContext('proxy', proxy)
        return True
    elif proxyMatch:  # 不带协议默认为http
        setContext('proxy', f'http://{proxy}')
        return True
    else:  # 格式错误
        if inputFlag:
            input(proxy_input_warning)
            return setProxy()
        else:
            print(proxy_arg_warning)
            return False


'''
description: 保存配置到本地, 注意key字段会自动处理为小写, 请勿使用含大写字母的key
'''


def saveEnv():
    conf.read(conf_path, encoding='utf-8')
    if 'global' not in conf.sections():
        conf.add_section('global')
    conf.set("global", "download_path", getContext("dl_path"))
    conf.set("global", "cookie", getContext("headers")['Cookie'])
    conf.set("global", "updateinfo", getContext("updateInfo"))
    conf.set("global", "concurrency", getContext("concurrency"))
    conf.set("global", "type", getContext("type"))
    conf.set("global", "filename", getContext("fileName"))
    conf.set("global", "quoted", getContext("quoted"))
    conf.set("global", "retweeted", getContext("retweeted"))
    conf.set("global", "media", getContext("media"))
    conf.set("global", "readfile", getContext("readFile"))
    conf.set("global", "readfilepath", getContext("readFilePath"))
    proxy = getContext("proxy")
    if proxy:
        conf.set("global", "proxy", proxy)
    conf.write(open(conf_path, 'w', encoding='utf-8'))


'''
description: 从本地读取配置
'''


def getEnv():
    if os.path.exists(conf_path):
        conf.read(conf_path, encoding='utf-8')
        if 'global' in conf.sections():
            headers = getContext("headers")
            items = conf.items('global')
            for item in items:
                if item[0] == 'cookie' and item[1]:
                    token = getToken(item[1])
                    if token:
                        headers['x-csrf-token'] = token
                        headers['Cookie'] = item[1]
                elif item[0] == 'download_path' and item[1]:
                    setContext('dl_path', item[1])
                elif item[0] == 'updateinfo' and item[1]:
                    setContext('updateInfo', eval(item[1]))
                elif item[0] == 'concurrency' and item[1]:
                    setContext('concurrency', int(item[1]))
                elif item[0] == 'type' and item[1]:
                    setContext('type', item[1])
                elif item[0] == 'filename' and item[1]:
                    setContext('fileName', item[1])
                elif item[0] == 'media' and item[1]:
                    setContext('media', eval(item[1]))
                elif item[0] == 'quoted' and item[1]:
                    setContext('quoted', eval(item[1]))
                elif item[0] == 'retweeted' and item[1]:
                    setContext('retweeted', eval(item[1]))
                elif item[0] == 'readfilepath' and item[1]:
                    setContext('readFilePath', str(item[1]))
                elif item[0] == 'readfile' and item[1]:
                    setContext('readFile', eval(item[1]))
                elif item[0] == 'proxy' and item[1] and (pProxy.match(item[1]) or pProxy2.match(item[1])):
                    setContext('proxy', item[1])
            setContext('headers', headers)


'''
description: 推主名 -> 推主id (用于接口请求参数)
param {str} userName 推主名
return {int|None} userId 推主id
'''


def getUserId(userName: str) -> int | None:
    with httpx.Client(proxies=getContext('proxy'), headers=getContext('headers'), verify=False) as client:
        for i in range(1, 6):
            try:
                response = client.post(userInfoApi, params={'variables': userInfoApiPar.format(
                    userName)})
                break
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
                if i >= 5:
                    print(network_error_warning)
                    return False
                else:
                    print(timeout_warning.format(i))
                    time.sleep(1)
    if response.status_code != httpx.codes.OK:
        print(http_warning.format('getUserId',
                                  response.status_code, getHttpText(response.status_code)))
        return None
    page_content = response.text
    userId = p_user_id.findall(page_content)
    if userId:
        return int(userId[0])
    else:
        print(user_warning)
        writeLog(userName, json.dumps(page_content))
        return None


'''
description: 从直链下载文件
param {*} client 下载器对象
param {str} url 媒体直链
param {str} filePath 下载文件路径
param {str} fileName 文件名
return {bool} True下载成功, False下载失败
'''


def downloader(client, url: str, filePath: str, fileName: str) -> bool:
    for _ in range(1, 6):
        try:
            with client.stream('GET', url) as response:
                if response.status_code != httpx.codes.OK:
                    print(http_warning.format(
                        'downloadFile', response.status_code, getHttpText(response.status_code)))
                    return False
                with open(f'{filePath}.cache', 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=1024 * 128):
                        if chunk:
                            f.write(chunk)
                os.rename(f'{filePath}.cache', filePath)
                return True
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError):
            # print(download_timeout_warning.format(fileName, '正在重试...', i))
            time.sleep(1)
        except Exception as e:
            print(download_warning.format(e))
    print(download_timeout_warning.format(fileName, '失败次数过多...', ''))
    return False


'''
description: 下载任务队列中的直链
param {str} savePath 下载路径
param {queue} dataList 任务队列
param {queue} done 已完成队列
'''


def downloadFile(savePath: str, dataList: queue.Queue, done: queue.Queue):
    while True:
        if dataList.qsize():
            break
    while True:
        try:
            datalist = dataList.get(timeout=30)
            dataList.task_done()
        except queue.Empty:
            print(queue_empty_warning)
            return
        if not datalist:
            return
        headers = getContext('headers')
        try:
            with httpx.Client(proxies=getContext('proxy'), headers=headers, verify=False) as client:
                for userName in datalist:
                    for twtId, datalayer in datalist.get(userName).items():
                        date = datalayer.get('date').split(' ')
                        time, date = (date[-1], date[0])
                        for datatype, data in datalayer.get('dataList').items():
                            if datatype in ['pic', 'gif', 'vid']:  # media
                                count = 0
                                for url in data:
                                    count += 1
                                    ori, ext = os.path.splitext(
                                        url.split('?')[0].split('/')[-1])
                                    if datatype == 'pic':
                                        url += '?name=orig'  # add query '?name=orig' can get original pic file
                                    fileName = getContext('fileName').format(
                                        userName=userName, twtId=twtId, ori=ori, date=date, time=time,
                                        type=f'{datatype}{count}') + ext
                                    filePath = os.path.join(savePath, fileName)
                                    if os.path.exists(filePath) or os.path.exists(f'{filePath}.cache'):
                                        continue
                                    elif downloader(client, url, filePath, fileName):
                                        done.put('done')
                            else:  # text
                                fileName = getContext('fileName').format(
                                    userName=userName, twtId=twtId, date=date, time=time, type='text', ori='') + '.txt'
                                filePath = os.path.join(savePath, fileName)
                                if os.path.exists(filePath):
                                    continue
                                elif saveText(filePath, data):
                                    done.put('done')
        except Exception:
            print(download_warning.format(traceback.format_exc()))


'''
description: 保存推文文本内容
param {str} filePath 写入文件路径
param {str} content 推文内容(文本)
param {str} date 推文发布日期
'''


def saveText(filePath: str, content: str):
    if os.path.exists(filePath):
        return True
    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True


'''
description: 单条推文数据解析器
param {*} tweet 单条推文元数据
return {*} 解析出的目标数据(内含媒体url)
'''


def getResult(tweet):
    def getresult(result):
        return result if result['__typename'] == 'Tweet' else \
            (result['tweet'] if result['__typename'] == 'TweetWithVisibilityResults' else
             ({'errText': result['tombstone']['text']['text']} if result['__typename'] == 'TweetTombstone' else None))

    if 'entryId' not in tweet:
        return tweet
    if tweet['content']['entryType'] == 'TimelineTimelineItem':
        # SelfThread -> singlePageTask
        if 'tweetDisplayType' in tweet['content']['itemContent'] and \
                tweet['content']['itemContent']['tweetDisplayType'] in ['Tweet', 'SelfThread']:
            result = tweet['content']['itemContent']['tweet_results']
            if 'result' in result:
                return getresult(result['result'])
            else:
                return None
        else:
            return None
    elif tweet['content']['entryType'] == 'TimelineTimelineModule':
        if 'tweetDisplayType' in tweet['content'] and \
                tweet['content']['tweetDisplayType'] == 'VerticalConversation':
            result = tweet['content']['items'][-1]['item']['tweet_results']
            if 'result' in result:
                return getresult(result['result'])
            else:
                return None
        else:
            return None
    else:
        return None


'''
description: 从列表api元数据解析follow用户名列表
param {Dict} pageContent api返回的元数据
param {int} cursor api翻页锚点参数
param {List} dataList 数据容器
'''


def getFollower(pageContent, dataList: list):
    cursor = None
    if 'errors' in pageContent:
        message = pageContent['errors'][0]['message']
        print(apiErr_warning.format(message))
        return None
    if 'user' in pageContent['data']:
        result = pageContent['data']['user']['result']
        if result['__typename'] == 'UserUnavailable':
            print(user_unavailable_warning)
            return None
        instructions = result['timeline']['timeline']['instructions']
        for instruction in instructions:
            if instruction['type'] == 'TimelineAddEntries':
                entries = instruction['entries']
                if len(entries) == 0 or len(entries) == 2 and 'entryId' in entries[-2] and 'cursor-bottom' in \
                        entries[-2]['entryId']:
                    # 翻页完成, 两个follow接口的entries[-1]为cursor-top, [-2]为cursor-bottom (与推文的接口相反)
                    return None
                for entry in entries:
                    if 'entryId' in entry and 'user-' in entry['entryId']:
                        dataList.append(entry['content']['itemContent']
                                        ['user_results']['result']['legacy']['screen_name'])
                cursor = entries[-2]['content']['value'] if len(
                    entries) != 0 else None
                break
    return cursor


'''
description: 从列表api元数据解析推文id列表
param {Dict} pageContent api返回的元数据
param {int} cursor api翻页锚点参数
param {bool} isfirst 是否为第一页
'''


def getTweet(pageContent, cursor=None, isfirst=False):
    if 'errors' in pageContent:
        message = pageContent['errors'][0]['message']
        print(apiErr_warning.format(message))
        return None, None
    elif 'globalObjects' in pageContent:  # 搜索接口
        entries = list(pageContent['globalObjects']['tweets'].values())
        if not entries and isfirst:
            print(needCookie_warning)
        cursor = \
            pageContent['timeline']['instructions'][0]['addEntries']['entries'][-1]['content']['operation']['cursor'][
                'value'] \
                if len(entries) != 0 and pageContent['timeline']['instructions'][0]['addEntries']['entries'][-1][
                'entryId'] == 'sq-cursor-bottom' \
                else (
                pageContent['timeline']['instructions'][-1]['replaceEntry']['entry']['content']['operation']['cursor'][
                    'value']
                if len(pageContent['timeline']['instructions']) != 1 and
                   pageContent['timeline']['instructions'][-1]['replaceEntry'][
                       'entryIdToReplace'] == 'sq-cursor-bottom' else None)
    elif 'user' in pageContent['data']:
        result = pageContent['data']['user']['result']
        if result['__typename'] == 'UserUnavailable':
            print(user_unavailable_warning)
            return None, None
        elif result['__typename'] == 'Age-restricted adult content':
            print(age_restricted_warning)
            return None, None
        elif not result['timeline_v2']:
            print(need_cookie_warning)
            return None, None
        instructions = result['timeline_v2']['timeline']['instructions']
        for instruction in instructions:
            if instruction['type'] == 'TimelineAddEntries':
                entries = instruction['entries']
                cursor = entries[-1]['content']['value'] if len(
                    entries) != 0 else None
                break
    elif 'threaded_conversation_with_injections_v2' in pageContent['data']:
        entries = pageContent['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries']
    # 搜索接口返回的entries不包括cursor
    if len(entries) == 0 or len(entries) == 2 and 'entryId' in entries[-1] and 'cursor-bottom' in entries[-1][
        'entryId']:
        # 翻页完成
        return None, None
    tweets = []
    for tweet in entries:
        if 'entryId' in tweet and 'tweet-' in tweet['entryId']:
            tweets.append(tweet)
        elif 'entryId' not in tweet:
            tweets.append(tweet)
    return tweets, cursor


'''
description: api数据解析
param {*} pageContent api返回的元数据
param {*} total 任务总量计数器
param {*} userName 推主名
param {*} dataList 任务数据队列
param {*} user_id 推主id
param {*} rest_id_list 推文id列表
param {*} cursor api翻页锚点参数
param {*} cfg 推文解析参数
dataList数据结构：
    [{'推主id': {'推文id':{'date':'日期(%Y%m%d %H%M%S)','dataList':{'数据类型':['下载链接'],'text':'文本内容'}}}}}}]
'''


def parseData(pageContent, total, userName, dataList, cfg, rest_id_list, cursor):
    includeNonMedia = cfg['media']
    includeRetweeted = cfg['retweeted']
    includeQuoted = cfg['quoted']
    if cursor:
        tweet_list, cursor = getTweet(pageContent)
    else:
        tweet_list, cursor = getTweet(pageContent, isfirst=True)
    if not tweet_list:
        return cursor, rest_id_list
    twtDic = {}
    userIdDic = pageContent['globalObjects']['users'] if 'globalObjects' in pageContent else {
    }
    for tweet in tweet_list:
        result = getResult(tweet)
        if not result:
            print(parse_warning)
            writeLog(f'{userName}_unexpectData',
                     f'{traceback.format_exc()}\n\n{json.dumps(tweet)}')
            continue
        elif 'errText' in result:
            print(dataErr_warning.format(result.get('errText')))
            continue
        # 转推
        if 'legacy' in result and 'retweeted_status_result' in result['legacy']:
            if includeRetweeted:
                result = result['legacy']['retweeted_status_result']['result']['tweet'] \
                    if 'tweet' in result['legacy']['retweeted_status_result']['result'] \
                    else result['legacy']['retweeted_status_result']['result']
            else:
                continue
        twtId = result.get('rest_id') or result.get('id_str')
        if not twtId:
            raise KeyError('twtId获取失败')
        _userName = result['core']['user_results']['result']['legacy'][
            'screen_name'] if 'core' in result else userIdDic[result['user_id_str']]['screen_name']
        legacy = result['legacy'] if 'legacy' in result else result
        legacylist = [[_userName, twtId, legacy]]
        media_type = getContext('type').split('&')
        if includeQuoted:  # 包括引用，如 https://twitter.com/Liyu0109/status/1611734998402633728
            # 判断是否有引用，以及引用是否能查看，搜索接口的引用tweet直接在tweet_list里面，其他接口则嵌套在result里面
            if 'quoted_status_result' in result and 'legacy' in result['quoted_status_result']['result']:
                _userName = result['quoted_status_result']['result']['core']['user_results']['result']['legacy'][
                    'screen_name']
                twtId = result['quoted_status_result']['result']['rest_id']
                legacy = result['quoted_status_result']['result']['legacy']
                legacylist.append([_userName, twtId, legacy])
        else:
            # 搜索接口, userName为空(@&advanced=)时忽略引用过滤
            if 'quoted_status_id_str' in result and userName and userName != _userName:
                continue
        for _userName, twtId, legacy in legacylist:
            picList = []
            gifList = []
            vidList = []
            if twtId in rest_id_list:
                continue
            else:
                rest_id_list.append(twtId)
            if 'extended_entities' in legacy:
                for media in legacy['extended_entities']['media']:

                    # photo
                    if media['type'] == 'photo' and media['type'] in media_type:
                        # get {'url', url}, add query '?name=orig' can get original pic file
                        url = media['media_url_https']
                        if url:
                            picList.append(url)
                            total.put('add')

                    # gif(.mp4)
                    elif media['type'] == 'animated_gif' and media['type'] in media_type:
                        # [{'bitrate':filesize',url':url}]
                        variants = media['video_info']['variants'][0]
                        url = variants['url']
                        if url:
                            gifList.append(url)
                            total.put('add')

                    # video(.mp4)
                    elif media['type'] == 'video' and media['type'] in media_type:
                        # [{'bitrate':filesize',url':url},{}...] choose largest resolution
                        variants = sorted(media['video_info']['variants'],
                                          key=lambda s: s['bitrate'] if 'bitrate' in s else 0, reverse=True)[0]
                        url = variants['url']
                        if url:
                            vidList.append(url)
                            total.put('add')
                    # fail
                    elif media['type'] and media['type'] not in ['video', 'animated_gif', 'photo']:
                        print(parse_warning)
                        writeLog(f'{twtId}_unexpectType', json.dumps(media))
            twtId = str(twtId)
            isMediaTwt = len(picList) or len(gifList) or len(vidList)
            if _userName not in twtDic:
                twtDic[_userName] = {}
            twtDic[_userName][twtId] = {
                'dataList': {'pic': picList, 'gif': gifList, 'vid': vidList},
                'date': time.strftime("%Y%m%d %H%M%S",
                                      time.strptime(legacy['created_at'], "%a %b %d %H:%M:%S +0000 %Y"))
            }
            # get twt text content,Ignore empty text,&非媒体推文过滤器
            if (legacy['full_text'] and 'full_text' in media_type) and (includeNonMedia or isMediaTwt):
                twtDic[_userName][twtId]['dataList']['text'] = legacy['full_text']
                total.put('add')
    dataList.put(dict(**twtDic))
    return cursor, rest_id_list


'''
description: 从github api获取新版本信息
'''


def checkUpdate():
    # 从本地缓存获取更新信息
    updateInfo = getContext('updateInfo')
    date = time.strftime("%m-%d", time.localtime())

    tagName = updateInfo['tagName']
    name = updateInfo['name']

    if updateInfo['LastCheckDate'] != date:
        # 从api获取更新信息
        try:
            response = httpx.get(
                checkUpdateApi, proxies=getContext('proxy'), verify=False)
            jsonData = response.json()
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            print(check_update_warning.format(e))
            return

        # api返回数据不正确, 一般是触发频限了
        if "tag_name" not in jsonData:
            print(check_update_warning.format(jsonData))
            return

        tagName = jsonData["tag_name"]
        name = jsonData["name"]
        updateInfo['LastCheckDate'] = date

    # 存在新版本，弹出更新文本提示
    if tagName and compare_version(version, tagName) == 2:
        print("发现新版本: {}\n下载地址: {}\n".format(name, release_page))
        # 覆盖本地缓存数据
        updateInfo['tagName'] = tagName
        updateInfo['name'] = name
    else:
        print("当前版本已是最新\n")

    setContext('updateInfo', updateInfo)
    saveEnv()


'''
description: 显示配置
'''


def showConfig():
    def bool2str(b):
        return '是' if b else '否'

    proxy = getContext('proxy') or '不使用'
    quoted = bool2str(not getContext('quoted'))
    retweeted = bool2str(not getContext('retweeted'))
    media = bool2str(not getContext('media'))
    cookie = bool2str(getContext('headers')['Cookie'])
    concurrency = getContext('concurrency')
    fileName = getContext('fileName')
    dl_path = getContext('dl_path')
    type = getContext('type')
    readFile = bool2str(getContext('readFile'))
    readFilePath = os.path.realpath(getContext('readFilePath')) + ('(文件有效)' if os.path.exists(
        getContext('readFilePath')) and os.path.isfile(getContext('readFilePath')) else '(文件无效)') \
        if getContext("readFilePath") and getContext('readFile') else "未设置"
    print(config_info.format(proxy=proxy, retweeted=retweeted, media=media, cookie=cookie,
                             quoted=quoted, concurrency=concurrency, fileName=fileName, dl_path=dl_path, type=type,
                             readFile=readFile, readFilePath=readFilePath))


'''
description:
param {str} version1 版本号1
param {str} version2 版本号2
param {str} split_flag 版本号分隔符
return {int} 0 1 2: 0为相等， 1为1大， 2为2大
'''


def compare_version(version1=None, version2=None, split_flag="."):
    if (version1 is None) or (version1 == "") or (version2 is None) or (version2 == ""):
        if ((version1 is None) or (version1 == "")) and (version2 is not None) and (version2 != ""):
            return 2
        if ((version2 is None) or (version2 == "")) and (version1 is not None) and (version1 != ""):
            return 1
    if version1 == version2:
        return 0
    try:
        current_section_version1 = version1[:version1.index(split_flag)]
    except:
        current_section_version1 = version1
    try:
        current_section_version2 = version2[:version2.index(split_flag)]
    except:
        current_section_version2 = version2
    if int(current_section_version1) > int(current_section_version2):
        return 1
    elif int(current_section_version1) < int(current_section_version2):
        return 2
    try:
        other_section_version1 = version1[version1.index(split_flag) + 1:]
    except:
        other_section_version1 = ""
    try:
        other_section_version2 = version2[version2.index(split_flag) + 1:]
    except:
        other_section_version2 = ""
    return compare_version(other_section_version1, other_section_version2)
