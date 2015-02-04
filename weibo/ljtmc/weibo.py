# -*- coding: utf-8 -*-
import urllib2, urllib, cookielib
from scrapy import Selector
import pdb 
import sys 
import time
import datetime
reload(sys)
sys.setdefaultencoding('utf-8')

def get_html_by_data(url, use_cookie=False):
    data = {}
    post_data = urllib.urlencode(data)
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    req = urllib2.Request(url)
    if use_cookie:
        cookie_file = open('cookie')
        cookie = cookie_file.read()
        req.add_header("Cookie", cookie)
    req.add_header("User-agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36")
    download = False
    try_times = 0
    f = opener.open(req)
    html = f.read()
    html_file = open('test.html','w')
    print >> html_file, html
    f.close()
    download = True
    return html

def crawl_profile(userid, prod):
    url = 'http://weibo.cn/' + userid + '/info'
    hxs = Selector(text=get_html_by_data(url,use_cookie=True))
    prod['gender'] = prod['city'] = prod['birth'] = ''
    try:
        lists = hxs.xpath('//div[@class="c"][3]/text()')
        for list in lists:
            str = list.extract()
            if str.find('性别') != -1:
                prod['gender'] = str.split(':')[1]
            elif str.find('地区') != -1:
                location = str.split(':')[1]
                res = location.split(' ')
                if len(res) > 1:
                    prod['province'] = res[0]
                    prod['city'] = res[1]
            elif str.find('生日') != -1:
                prod['birth'] = str.split(':')[1]
    except Exception as e:
        print e

def crawl_list(url):
    hxs = Selector(text=get_html_by_data(url,use_cookie=True))
    try:
        lists = hxs.xpath('//div[@class="c"]')
        prod = {}
        for list in lists:
            id = list.xpath('./@id')
            if len(id) == 0:
                continue            

            weibo_name = list.xpath('.//a[@class="nk"]/text()')[0].extract()
            prod['weibo_name'] = weibo_name
            print prod['weibo_name']            
            
            content_list = list.xpath('.//span[@class="ctt"]/a/text()|.//span[@class="ctt"]/text()|.//span[@class="ctt"]/span/text()')
            prod['content'] = ""
            for elem in content_list:
                prod['content'] += elem.extract()
            prod['content'] = prod['content'][1:]
            print prod['content']
           
            comment_url = list.xpath('.//div/a[@class="cc"]/@href')[0].extract()
            user_id = comment_url.split('uid=')[1].split('&')[0]
            prod['url'] = 'http://weibo.com/u/' + user_id
            comment_url = comment_url.split('?')[0]
            eq = comment_url.rfind('/')
            weibo_id = comment_url[eq+1:]
            print 'user_id: ' + user_id
            print 'weibo_id: ' + weibo_id
            
            crawl_profile(user_id, prod)
            print 'gender: ' + prod['gender']
            print 'city: ' + prod['city']
            print 'birth: ' + prod['birth']

            eq1 = prod['content'].find('#')
            eq2 = prod['content'].rfind('#')
            if eq1 != eq2 and eq1 != -1 and eq2 != -1:
                prod['keyword'] = prod['content'][eq1:eq2+1]
            else:
                prod['keyword'] = ''
            print prod['keyword']

            date = list.xpath('.//span[@class="ct"]/text()')[0].extract()
            prod['date'] = date.split(' ')[0]
            if prod['date'].find('今天') != -1 or prod['date'].find('前') != -1:
                prod['date'] = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            elif prod['date'].find('月') != -1:
                prod['date'] = '2014-' + prod['date'].replace('月','-').replace('日','')
            print prod['date']

            text_list = list.xpath('.//a/text()')
            for text in text_list:
                text = text.extract()
                if text.find('转发') != -1:
                    eq1 = text.find('[') 
                    eq2 = text.find(']')
                    prod['quote'] = text[eq1+1:eq2]
                    print 'quote: ' + prod['quote']  
                if text.find('评论') != -1:
                    eq1 = text.find('[') 
                    eq2 = text.find(']')
                    prod['comment'] = text[eq1+1:eq2]
                    print 'comment: ' + prod['comment']
                if text.find('赞') != -1:  
                    eq1 = text.find('[') 
                    eq2 = text.find(']')
                    prod['like'] = text[eq1+1:eq2]
                    print 'like: ' + prod['like']
            save_csv(prod)

    except Exception as e:
        print e

def add(key, prod):
    if prod.has_key(key):
        return prod[key].replace('\r','').replace('\n','').replace(',',' ') + ','
    return ','

def save_csv(prod):
    file = open('result.csv','a')
    resline = ""
    resline += add('date', prod)
    resline += add('weibo_name', prod)
    #resline += add('url', prod)
    #resline += add('keyword', prod)
    #resline += add('gender', prod)
    #resline += add('birth', prod)
    resline += add('province', prod)
    resline += add('city', prod)
    resline += add('content', prod)
    #resline += add('url', prod)
    #resline += add('quote', prod)
    #resline += add('comment', prod)
    #resline += add('like', prod)
    print >> file, resline.encode('utf-8')

def stat_cnt(url, date):
    hxs = Selector(text=get_html_by_data(url,use_cookie=True))
    try:
        cnt = hxs.xpath('//div[@class="c"]/span[@class="cmt"]/text()')[0].extract()
        cnt = int(cnt.split('共')[1].split('条')[0])
    except:
        cnt = 0
    print cnt
    file = open('count.csv','a')
    resline = date + ',' + str(cnt)
    print >> file, resline.encode('utf-8')
    return cnt 

def work(keyword, cur_date):
    for day in range(0, 365):
        dt_date = cur_date - datetime.timedelta(days=day)
        date = str(dt_date).split(' ')[0].replace('-','')
        sdate = edate = date
        url = 'http://weibo.cn/search/mblog?hideSearchFrame=&keyword=' + keyword + '&advancedfilter=1&hasori=1&starttime=' + sdate + '&endtime=' + edate + '&sort=time'
        try:
            cnt = stat_cnt(url, date)
        except:
            cnt = 101
        for page in range(1, min(101, 1+cnt/10)):
            url = 'http://weibo.cn/search/mblog?hideSearchFrame=&keyword=' + keyword + '&advancedfilter=1&hasori=1&starttime=' + sdate + '&endtime=' + edate + '&sort=time&page=' + str(page)
            print url
            try:
                crawl_list(url)
            except Exception as e:
                print e
                print 'Cannot crawl this page: ' + url
                continue

if __name__ == '__main__':
    year = int(sys.argv[1])
    month = int(sys.argv[2])
    day = int(sys.argv[3])
    cur_date = datetime.datetime(year, month, day)
    work('垃圾填埋场', cur_date)
