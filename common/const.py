'''
Author: mengzonefire
Date: 2023-01-15 23:14:36
LastEditTime: 2023-04-02 18:03:27
LastEditors: mengzonefire
Description: 存放全局常量
'''

import re
import os
import configparser

version = '1.3.1'

# const
twtCount = 100  # 列表api的count参数
url_args_help = \
    '''tw url to collect, must be like:
    1. https://twitter.com/***/status/***
    2. https://twitter.com/***(/media|likes|following) (user page, *** is user_id)
    3. @*** (search page, plz check README)'''
conf = configparser.RawConfigParser()
conf_path = os.path.expanduser('~') + '/tw_media_downloader.conf'

# api auth token
authorization = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

# context/config
context = {
    'proxy': None,
    'headers': {'authorization': authorization, 'Cookie': ''},
    'dl_path': 'twitter_media_download',
    'log_path': 'log',
    'updateInfo': {'LastCheckDate': '', 'tagName': '', 'name': ''},
    'concurrency': 8,
    'type': 'photo&animated_gif&video&full_text',
    'fileName': '{userName}-{twtId}-{date}_{time}-{type}',
    'quoted': True,
    'retweeted': True,
    'media': True,  # 是否包含非媒体(纯文本)推文
    'readFile': False,  # 是否开启文件读取模式
    'readFilePath': 'data'  # 文件路径 默认data
}


def setContext(key, value):
    context[key] = value


def getContext(key=None):
    if key:
        return context[key]
    else:
        return context


# api url
hostUrl = 'https://api.twitter.com/1.1/guest/activate.json'
singlePageApi = 'https://twitter.com/i/api/graphql/XjlydVWHFIDaAUny86oh2g/TweetDetail'
userSearchApi = 'https://api.twitter.com/2/search/adaptive.json'
userInfoApi = 'https://twitter.com/i/api/graphql/Vf8si2dfZ1zmah8ePYPjDQ/UserByScreenNameWithoutResults'
userLikesApi = 'https://api.twitter.com/graphql/nYrjBgnUWQFt_tRyCGatZA/Likes'
userFollowingApi = 'https://api.twitter.com/graphql/fzE3zNMTkr-CJufrDwjC4A/Following'
userHomeApi = 'https://api.twitter.com/graphql/CkON7wJrKLwEVV59ClcmjA/UserTweets'
userMediaApi = 'https://api.twitter.com/graphql/YcKL-v9RI2t42QCEDfv-9g/UserMedia'
checkUpdateApi = 'https://api.github.com/repos/mengzonefire/twitter-media-downloader/releases/latest'

# api parameter
singlePageApiPar = '{{"focalTweetId":"{}","with_rux_injections":false,"includePromotedContent":true,"withCommunity":true,"withQuickPromoteEligibilityTweetFields":true,"withBirdwatchNotes":false,"withSuperFollowsUserFields":true,"withDownvotePerspective":false,"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true,"withVoice":true,"withV2Timeline":true}}'
userSearchApiPar = '{{"include_profile_interstitial_type":1,"include_blocking":1,"include_blocked_by":1,"include_followed_by":1,"include_want_retweets":1,"include_mute_edge":1,"include_can_dm":1,"include_can_media_tag":1,"include_ext_has_nft_avatar":1,"include_ext_is_blue_verified":1,"include_ext_verified_type":1,"skip_status":1,"cards_platform":"Web-12","include_cards":1,"include_ext_alt_text":true,"include_ext_limited_action_results":false,"include_quote_count":true,"include_reply_count":1,"tweet_mode":"extended","include_ext_collab_control":true,"include_ext_views":true,"include_entities":true,"include_user_entities":true,"include_ext_media_color":true,"include_ext_media_availability":true,"include_ext_sensitive_media_warning":true,"include_ext_trusted_friends_metadata":true,"send_error_codes":true,"simple_quoted_tweet":true,"q":"{}","tweet_search_mode":"live","count":{},"query_source":"typed_query",{}"pc":1,"spelling_corrections":1,"include_ext_edit_control":true,"ext":"mediaStats,highlightedLabel,hasNftAvatar,voiceInfo,birdwatchPivot,enrichments,superFollowMetadata,unmentionInfo,editControl,collab_control,vibe"}}'
userInfoApiPar = '{{"screen_name":"{}","withHighlightedLabel":false}}'
userLikesApiPar = '{{"userId":"{}","count":{},{}"includePromotedContent":false,"withSuperFollowsUserFields":true,"withDownvotePerspective":false,"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}}'
userFollowingApiPar = '{{"userId":"{}","count":{},{}"includePromotedContent":false,"withSuperFollowsUserFields":true,"withDownvotePerspective":false,"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true}}'
userFollowingApiPar2 = '{"responsive_web_twitter_blue_verified_badge_is_enabled":true,"responsive_web_graphql_exclude_directive_enabled":false,"verified_phone_label_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"vibe_api_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":false,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":false,"interactive_text_enabled":true,"responsive_web_text_conversations_enabled":false,"responsive_web_enhance_cards_enabled":false}'
userHomeApiPar = '{{"userId":"{}","count":{},{}"includePromotedContent":true,"withQuickPromoteEligibilityTweetFields":true,"withSuperFollowsUserFields":true,"withDownvotePerspective":false,"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true,"withVoice":true,"withV2Timeline":true}}'
userMediaApiPar = '{{"userId":"{}","count":{},{}"includePromotedContent":false,"withSuperFollowsUserFields":true,"withDownvotePerspective":false,"withReactionsMetadata":false,"withReactionsPerspective":false,"withSuperFollowsTweetFields":true,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}}'
commonApiPar = '{"responsive_web_twitter_blue_verified_badge_is_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"vibe_api_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":false,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":false,"interactive_text_enabled":true,"responsive_web_text_conversations_enabled":false,"longform_notetweets_richtext_consumption_enabled":false,"responsive_web_enhance_cards_enabled":false}'

# re pattern
p_csrf_token = re.compile(r'ct0=(.+?)(?:;|$)')
pProxy = re.compile(r'.+?:\d+$')
pProxy2 = re.compile(r'(http|socks5)://(.+:.+@)?.+?:\d+$')
p_user_id = re.compile(r'"rest_id":"(\d+)"')
p_user_link = re.compile(
    r'https://twitter.com/([^/]+?)(?:/media|/likes|/following)?$')
p_twt_link = re.compile(r'https://twitter.com/(.+?)/status/(\d+)')
p_unexpect_var = re.compile(
    r'\{(?!(userName)|(twtId)|(time)|(date)|(type)|(ori))([^}]+?)?\}')

# http code text warning
httpCodeText = {403: '本机IP已被推特服务器禁止访问, 请尝试更换代理节点',
                401: '导入的cookie无效, 请重新获取并导入', 400: '请求错误, 请前往issue页反馈'}
