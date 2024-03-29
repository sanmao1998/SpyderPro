import requests
import re
import csv
from concurrent import futures
from bs4 import BeautifulSoup
from multiprocessing import Pool as MP

import time, random
from threading import Lock

'''获取2k多个城市的历史天气情况'''


class WeatherData(object):
    def __init__(self):
        self.s = requests.Session()
        self.headers = {
            'Host': 'www.tianqihoubao.com',
            'User-Agent': 'Mozilla/5.0 (Macinto¬sh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'
        }
        self.use = ['Mozilla/5.0 (X11; Linux i686; rv:64.0) Gecko/20100101 Firefox/64.0',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:10.0) Gecko/20100101 Firefox/62.0',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/71.0.3578.98 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134']

    def get_province_link(self):
        """
        获取进入每个城市具体的区域--***省份***---链接入口
        :return:
        """
        url = 'http://www.tianqihoubao.com/lishi/'
        data = self.s.get(url=url, headers=self.headers)
        pre_url = 'http://www.tianqihoubao.com/'
        sounp = BeautifulSoup(data.content, 'lxml')  # 此处不要使用data.text，会出现乱码，改用response保证原有样子
        sounp.prettify()
        datalist = list()
        for res in sounp.find_all(name='a', href=re.compile('^/lishi.*[htm]$')):
            url_lis = list()
            url_lis.append(pre_url)
            url_lis.append(res['href'])
            url = ''.join(url_lis)  # 链接拼接
            dic = dict()
            province = res.string  # 省份
            dic['province'] = province
            dic['url'] = url
            datalist.append(dic)

            # self.get_city_pastlink(url)
        return datalist

    def get_city_pastlink(self, url) -> list:
        """
        获取省份下所有城市分区链接
        :param url: 省份链接入口
        :return:list
        """

        data = self.s.get(url=url, headers=self.headers)
        pre_url = 'http://www.tianqihoubao.com/'
        sounp = BeautifulSoup(data.content, 'lxml')  # 此处不要使用data.text，会出现乱码，改用response保证原有样子
        sounp.prettify()
        # pool = MP(processes=4)
        datalist = list()
        for res in sounp.find_all(name='dd'):
            res = res.find_all(name='a')
            dic = dict()
            for info in res:
                cityname = info.string  # 城市名字
                url_lis = list()
                url_lis.append(pre_url)
                url_lis.append(info['href'])
                url = ''.join(url_lis)  # 城区天气历史链接
                dic['url'] = url
                dic['city'] = cityname
                datalist.append(dic)
        return datalist
        #
        #         pool.apply_async(func=self.getAllCity_Partition, args=(l,))
        # pool.close()  # 记得是写在最外层，否则会引起pool error
        # pool.join()

    # 获取城市分区下所有月份的历史天气链接
    def get_city_allpartition(self, url) -> list:
        """
               请求获取区域10多年来多每个月的天气数据链接
               :param url:
               :return: list
               """
        result = self.__into_area(url)
        return result

    # 进入每个

    def __into_area(self, url) -> list:
        """
        请求获取区域10多年来多每个月的天气数据链接
        :param url:
        :return: list
        """
        headers = {
            'Host': 'www.tianqihoubao.com',
            'User-Agent': random.choice(self.use)
        }
        pre_url = "http://www.tianqihoubao.com/"
        try:
            data = requests.get(url=url, headers=headers)
            if data.status_code != 200:
                return "网络链接%d" % data.status_code
        except ConnectionResetError:
            print("断网了")
            return ["ConnectionResetError"]

        except ConnectionError:
            print("该链接链接出现问题%s" % url)

            return ["ConnectionError"]
        except Exception as e:
            print(e)
            print("%s出问题了" % url)
            return ["Error --%s" % e]
        sounp = BeautifulSoup(data.text, 'lxml')  # 此处不要使用data.text，会出现乱码，改用response保证原有样子
        sounp.prettify()
        content = sounp.find(name='div', attrs={"class": "wdetail"})
        tags = content.find_all(name="a")

        urllist = list()
        for tag in tags[:-2]:  # 将date这个说明跳过
            href = tag.get("href")
            if "201812" in href:
                url = "http://www.tianqihoubao.com/lishi/" + href
            else:
                url = pre_url + href
            urllist.append(url)
        return urllist



