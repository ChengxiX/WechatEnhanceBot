import json
import requests

def requestXiaosi(spoken, appid='xiaosi', userid='user'):
    url = 'https://api.ownthink.com/bot?spoken=' + spoken + '&appid=' + appid + '&userid=' + userid
    try:
        sess = requests.get(url)
        answer = sess.text
        answer = json.loads(answer)
        return answer
    except:
        pass


def requestQingyun(msg, key='free',appid='0'):
    url = 'http://api.qingyunke.com/api.php?key=' + key + '&appid=' + appid + '&msg=' + msg
    try:
        sess = requests.get(url)
        answer = json.loads(sess.text)
        return answer
    except:
        pass

def top_news():
    url = 'http://api.avatardata.cn/TouTiao/Query?key=f1e821d4270a46ebabd038add0868915&type=top'
    try:
        res = requests.get(url)
        res = json.loads(res.text)
        return res
    except:
        pass

if __name__ == '__main__':
    while True:
        print(requestXiaosi(input()))