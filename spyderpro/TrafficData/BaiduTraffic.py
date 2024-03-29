import requests
import json
import time
from urllib.parse import urlencode
from spyderpro.TrafficData.TrafficInterface import Traffic


class BaiduTraffic(Traffic):

    def __init__(self, db):
        self.db = db
        self.s = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36'

        }
        # 获取实时城市交通情况

    # def deco(func):
    #     def Load(self, cityCode):
    #         data = func(self, cityCode)
    #         return data
    #
    #     return Load
    #
    # @deco
    def citytraffic(self, citycode, timetype='minute') -> list:
        """获取实时交通状态，包括日期，拥堵指数，具体时刻

        :param citycode:城市id
        :param timetype:时间间隔单位，day 和minute，默认minute
        :return iterable(dict)
        dict->{'date': '2019-06-14', 'index': 1.49, 'detailTime': '14:00'}"""
        parameter = {
            'cityCode': citycode,
            'type': timetype
        }
        href = 'https://jiaotong.baidu.com/trafficindex/city/curve?' + urlencode(parameter)
        data = self.s.get(url=href, headers=self.headers)
        try:
            g = json.loads(data.text)
        except Exception as e:
            print("网络链接error:%s" % e)
            return None
        today = time.strftime("%Y-%m-%d", time.localtime())  # 今天的日期
        date = today
        if '00:00' in str(g):
            date = time.strftime("%Y-%m-%d", time.localtime(time.time() - 3600 * 24))  # 昨天的日期
        # 含有24小时的数据
        dic = {}
        for item in g['data']['list']:
            # {'index': '1.56', 'speed': '32.83', 'time': '13:45'}
            if item["time"] == '00:00':
                date = today
            dic['date'] = date
            dic['index'] = float(item['index'])
            dic['detailTime'] = item['time']
            yield dic

    def yeartraffic(self, citycode: int, name: str, year: int = int(time.strftime("%Y", time.localtime())),
                    quarter: int = int(time.strftime("%m", time.localtime())) / 3) -> list:
        """
        获取城市年度交通数据
        :param citycode: 城市id
        :param name: 城市名
        :param year: 年份
        :param quarter: 第几季度
        :return: iterable(dict)
        dict->{"date": date, "index": index, "city": name} """

        parameter = {
            'cityCode': citycode,
            'type': 'day'  # 有分钟也有day
        }
        href = 'https://jiaotong.baidu.com/trafficindex/city/curve?' + urlencode(parameter)
        data = self.s.get(url=href, headers=self.headers)
        try:
            obj = json.loads(data.text)
        except Exception as e:
            print("百度年度交通爬取失败！:%s" % e)
            return None
        if not len(obj):
            return None
        year = time.strftime("%Y-", time.localtime())  # 年份

        for item in obj['data']['list']:
            # {'index': '1.56', 'speed': '32.83', 'time': '04-12'}
            date = year + item['time']
            index = float(item["index"])
            yield {"date": date, "index": index, "city": name}

    def roaddata(self, citycode) -> list:
        """
        获取拥堵道路前10名数据, 数据包括路名，速度，数据包，道路方向，道路经纬度数据

        :param citycode:城市id
        :return: iterable(dict)
        dict->{"RoadName": roadname, "Speed": speed, "Direction": direction, "Bounds": bounds, 'Data': data}
        """
        dic = self.__roads(citycode)
        if dic['status'] == 1:
            print("参数不合法")
            return None
        datalist = self.__realtime_road(dic, citycode)

        for item, data in zip(dic['data']['list'], datalist):
            roadname = item["roadname"]
            speed = float(item["speed"])
            direction = item['semantic']
            bounds = json.dumps({"coords": data['coords']})
            info = json.dumps(data['data'])

            yield {"RoadName": roadname, "Speed": speed, "Direction": direction, "Bounds": bounds, 'Data': info}

    def __roads(self, citycode) -> dict:
        """
        获取道路信息包，包括道路pid，道路名，道路方向，速度
        :param citycode:城市id
        :return:dict
        """
        parameter = {
            'cityCode': citycode,
            'roadtype': 0
        }
        href = ' https://jiaotong.baidu.com/trafficindex/city/roadrank?' + urlencode(parameter)
        data = self.s.get(url=href, headers=self.headers)
        dic = json.loads(data.text)
        return dic

    def __realtime_road(self, dic, citycode):
        """
           处理10条道路路实时路况数据
           :param dic:
           :param citycode:
           :return: dict
           """

        for item, i in zip(dic['data']['list'], range(1, 11)):
            data = self.__realtime_roaddata(item['roadsegid'], i, citycode)
            yield data

    # 道路请求
    def __realtime_roaddata(self, pid, i, citycode) -> dict:
        """
         具体请求某条道路的数据
         :param pid:道路id
         :param citycode: 城市id
         :param i: 排名
         :return: dict->{"data": realdata, "coords": bounds}

         """
        parameter = {
            'cityCode': citycode,
            'id': pid
        }
        href = 'https://jiaotong.baidu.com/trafficindex/city/roadcurve?' + urlencode(parameter)
        data = self.s.get(url=href, headers=self.headers)
        obj = json.loads(data.text)
        timelist = []
        data = []
        for item in obj['data']['curve']:  # 交通数据
            timelist.append(item['datatime'])
            data.append(item['congestIndex'])
        realdata = {"num": i, "time": timelist, "data": data}
        bounds = []
        for item in obj['data']['location']:  # 卫星数据
            bound = {}
            for locations, count in zip(item.split(","), range(0, item.split(",").__len__())):
                if count % 2 != 0:

                    bound['lat'] = locations  # 纬度

                else:
                    bound['lon'] = locations  # 纬度
            bounds.append(bound)
        return {"data": realdata, "coords": bounds}
