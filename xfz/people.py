#coding:utf-8
import urllib2
import urllib
import cookielib
import hashlib
import sys
from scrapy import Selector
reload(sys)
sys.setdefaultencoding('utf-8')
from xml.dom.minidom import parse
import xml.dom.minidom
import pymongo
import time
import datetime
import re
regular = re.compile('<[^>]+>')

try:
    conn = pymongo.Connection('localhost',27017)
    info_table = conn.content_db.info2
    print 'Create mongodb connection successfully.'
except Exception as e:
    print e
    exit(-1)


def get_html_by_data(keyword, page, url, use_cookie=False):
    data = {
        "basenames":"rmwsite",
        "where":"(CONTENT=("+keyword+") or TITLE=("+keyword+"))",
        "curpage":page,
        "pagecount":20,
        "classvalue":"ALL",
        "classfield":"CLASS2",
        "isclass":0,
        "keyword":keyword,
        "sortfield":"-INPUTTIME",
        "id":0.03899359633214772,
    }
    postdata = urllib.urlencode(data).encode('utf-8')
    data = {}
    post_data = urllib.urlencode(data)
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    req = urllib2.Request(url, postdata)
    if use_cookie:
        cookie_file = open('cookie')
        cookie = cookie_file.read()
        req.add_header("Cookie", cookie)
    req.add_header("User-agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36")
    f = opener.open(req, timeout=20)
    html = f.read()
    html_file = open('temp.xml','w')
    print >> html_file, html
    f.close()
    return html

def get_html(url, use_cookie=False):
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
    f = opener.open(req, timeout=20)
    html = unicode(f.read(),'gbk')
    html_file = open('test.html','w')
    print >> html_file, html
    f.close()
    return html

def crawl_prod(prod):
    hxs = Selector(text=get_html(prod['content_url']))
    font_list = hxs.xpath('//font')
    prod['text'] = ""
    for font in font_list:
        text_list = font.xpath('.//text()')
        for text in text_list:
            prod['text'] += text.extract().strip()
    prod['text'] = prod['text'].replace('人 民 网 版 权 所 有 ，未 经 书 面 授 权 禁 止 使 用','')
    prod['text'] = prod['text'].replace('留言板管理员','')
    #print prod['text']

def save_db(prod):
    prod['id'] = hashlib.md5(prod['title']).hexdigest().upper()
    info_table.save(prod)

def handle_date(prod):
    ori_date = prod['ori_date'].strip().encode('utf-8')
    prod['timestamp'] = time.mktime(time.strptime(ori_date, "%Y年%m月%d日%H时%M分%S秒"))
    prod['date'] = time.strftime("%Y-%m-%d %H:%M", time.localtime(prod['timestamp']))
    print 'date: ' + prod['date']

def work(keyword):
    page = 1
    still_cnt = 0
    info_cnt = info_table.count()
    while True:
        try:
            print keyword + ' page:' + str(page)
            content = get_html_by_data(keyword, page, 'http://search.people.com.cn/rmw/GB/rmwsearch/gj_searchht.jsp')
            DOMTree = xml.dom.minidom.parse('temp.xml')
            collection = DOMTree.documentElement
            item_list = collection.getElementsByTagName("RESULT")
            if len(item_list) == 0 or page > 1000:
                print keyword + ' crawl finished'
                break
        except:
            break
        for item in item_list:
            prod = {}
            prod['baseword'] = keyword
            try:
                title = item.getElementsByTagName('TITLE')[0]
                prod['title'] = title.childNodes[0].data.strip()
                prod['title'] = regular.sub('', prod['title'])
                print prod['title']
                content_url = item.getElementsByTagName('DOCURL')[0]
                prod['content_url'] = content_url.childNodes[0].data.strip()
                print prod['content_url']
                ori_date = item.getElementsByTagName('PUBLISHTIME')[0]
                prod['ori_date'] = ori_date.childNodes[0].data.strip()
                print prod['ori_date']
                handle_date(prod)                
                try:
                    crawl_prod(prod)
                except Exception as e:
                    print e
                    prod['text'] = ''
                save_db(prod)
            except Exception as e:
                print e
                continue
        curr_info_cnt = info_table.count()
        if curr_info_cnt > info_cnt:
            info_cnt = curr_info_cnt
            print 'info_cnt: ' + str(info_cnt)
            still_cnt = 0
        else:
            still_cnt += 1
        if still_cnt > 20:
            break
        page += 1


if __name__ == '__main__':
    customer_types = ['消费者','顾客','客户']
    conflicts = ['投诉','索赔','投诉','状告','告上法庭','不满','恶劣','损害','误导','欺骗','欺诈','违法','曝光','危机','丑闻','质量问题','安全问题','道歉','召回','下架','处罚','罚款']
    company_names = ['3M','ABB','雅培','苹果公司','巴斯夫','拜耳','宝马','普利司通','佳能','家乐福','可口可乐','戴姆勒','达能','戴尔','杜邦','艾默生','福特','富士通','通用电气','通用汽车','日立','本田','现代汽车','英特尔','强生','卡夫','爱立信','LG','马自达','麦德龙','米其林','三菱','NEC','雀巢','尼桑','诺基亚','诺华','松下','百事','标致','辉瑞','宝洁','理光','罗氏','飞利浦','三星','夏普','索尼','铃木','乐购','东芝','丰田','联合利华','大众汽车','沃尔玛','施乐']
    charitys = ['慈善','公益','捐赠']
    
    start = False
    for customer_type in customer_types:
        for conflict in conflicts:
            if start == False:
                if customer_type == '顾客' and conflict == '曝光':
                    start = True
                continue
            baseword = customer_type + '+' + conflict
            work(baseword)
    
    for company_name in company_names:
        for charity in charitys:
            baseword = company_name + '+中国+' + charity
            work(baseword)
