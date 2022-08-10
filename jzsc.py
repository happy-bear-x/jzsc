import asyncio
import csv
import json
import os
import random
import time

import aiohttp
import requests

from decrypt import AESDecrypt
# header需要accessToken和userAgent
headers = {
    'accessToken': 'jkFXxgu9TcpocIyCKmJ+tfpxe/45B9dbWMUXhdY7vLVhTOHUbjCc3IXPvP6vgf4lhpUUKvcMtoMqfGfwdLCb8g==',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/86.0.4240.198 Safari/537.36 '
}
# 登录信息过期信息
timeoutStr = '4bd02be856577e3e61e83b86f51afca55280b5ee9ca16beb9b2a65406045c9497c089d5e8ff97c63000f62b011a64f4019b64d9a050272bd5914634d030aab69'
# 公司项目url
companyProjectUrl='http://jzsc.mohurd.gov.cn/api/webApi/dataservice/query/comp/compPerformanceListSys?qy_id=002105291248690048&pg=%d&pgsz=15'

# 公司项目总数 {"code":200,"data":{"proTotal":"45","ryTotal":"1","aptTotal":"1"},"message":"","success":true}
companyTotalProUrl = 'http://jzsc.mohurd.gov.cn/api/webApi/dataservice/query/comp/getTotal?qyId=002105291239451473&qyCode=911501007794541363'
# 地区url
regionUrl = 'http://jzsc.mohurd.gov.cn/api/webApi/asite/region/index'
class JZSC:
    """ 抓取全国建筑市场监管公共服务平台数据
        
        目前可抓取资质信息、地区信息、公司信息
    """

    url = 'http://jzsc.mohurd.gov.cn/api/webApi/dataservice/query/comp/list?pg=%d&pgsz=%d'
    apt_url = "http://jzsc.mohurd.gov.cn/api/webApi/asite/qualapt/aptData"
    region_url = "http://jzsc.mohurd.gov.cn/api/webApi/asite/region/index"
    proxy_url = "http://127.0.0.1:5010"
    file_header = ('企业名称', '企业法定代表人', '企业注册属地', '统一社会信用代码')

    # 每页大小只能15条
    pgsz = 15

    def __init__(self, start_page=1, end_page=3838):
        """ 设置抓取的起始页和结束页 """
        self.start_page = start_page
        self.end_page = end_page

    def get_region_list(self):
        """ 获取地区信息 
        
        查询地区接口获取全部地区信息，返回值需解密

        Returns: 
            返回地区信息列表，地区信息用元组表示：(地区id, 地区名称)
            例如：
                [('FDFDFCFCFCFC', '北京'), ('FDFEFCFCFCFC', '天津')]
        """
        response = requests.get(self.region_url)
        if not response.ok:
            return []
        data = AESDecrypt.decrypt(response.text)
        return [(item['region_id'], item['region_name']) for item in json.loads(data)['data']['category']['provinces']]

    def get_apt_list(self):
        """ 获取资质信息 
        
        查询资质接口获取全部资质信息，返回值需解密

        Returns: 
            返回地区信息列表，地区信息用元组表示：(资质码, 资质名称)
            例如：
                [('A30904B', '工程设计核工业行业核设施退役及放射性三废处理处置工程专业乙级'), ('A31006B', '工程设计电子通信广电行业电子系统工程专业乙级')]
        
        """
        response = requests.get(self.apt_url)
        if not response.ok:
            return []
        data = AESDecrypt.decrypt(response.text)
        return [(item['APT_CODE'], item['APT_CASENAME']) for item in json.loads(data)['data']['pageList']]

    async def request(self, session, page):
        """ 请求目标页面
        
        真实发起请求，如果请求未成功则删除该代理，并重试，直到抓取到了正确的数据

        Args:
            session: aiohttp.ClientSession() 实例，用来发起请求
            page：要获取的页面

        Returns:
            返回响应中的加密字符串

        """
        # 随机睡1-300秒不等，防止并发太高，对目标网站产生过大压力
        await asyncio.sleep(random.randint(1, 50))
        while True:
            # proxy = await self.get_proxy(session)
            async with session.get(self.url % (page, self.pgsz), timeout=30) as response:
                if response.status == 200:
                    print(f'第{page}页数据已抓取！')
                    return (await response.text(), page)
                elif response.status == 401:
                    print(f'{page} 系统繁忙。。。')
                    await asyncio.sleep(5)

    async def parse_data(self, enc_str):
        """ 解析数据
        
        解密响应中的加密字符串，并解析成期望的数据格式

        Args:
            enc_str: 响应返回的加密字符串
        解密后：
        
        [{
            "QY_FR_NAME":"于延鹏","QY_REGION":"370200","QY_NAME":"青岛国电蓝德环境工程有限公司","QY_REGION_NAME":"山东省-青岛市","QY_ORG_CODE":"913702007277950437",
            "COLLECT_TIME":1622263196000,"RN":31,"QY_ID":"002105291239451342","QY_SRC_TYPE":"0","OLD_CODE":"727795043"
         }]
        Returns:
            返回公司信息列表，公司信息格式：(企业名称, 企业法定代表人, 企业注册属地, 统一社会信用代码)
            例如：
                [('9XXX0702XXXE6U****','浙江**建筑工程有限公司','xxx','浙江省-金华市')]

        """
        try:
            data = json.loads(AESDecrypt.decrypt(enc_str))
        except ValueError:
            return []
        items = data['data']['list']
        ret = []
        for item in items:
            ret.append((item['QY_NAME'], item['QY_FR_NAME'], item['QY_REGION_NAME'], item['QY_ORG_CODE']))
        return ret

    async def fetch(self):
        """ 抓取全部建筑企业信息
        
        按照每页100条，一直抓取到3838页，就可以抓取到全部数据，
        异步抓取，并将返回值存储到指定csv文件中

        """
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            for page in range(self.start_page, self.end_page + 1):
                tasks.append(asyncio.create_task(self.request(session, page)))
            with open(os.getcwd() + f'\\jzsc_{self.start_page}_{self.end_page}.csv', 'w+') as fp:
                writer = csv.writer(fp)
                writer.writerow(self.file_header)
                for task in tasks:
                    enc_str, page = await task
                    items = await self.parse_data(enc_str)
                    if not items:  # 如果数据为空，说明抓取错误，则重新抓取
                        tasks.append(asyncio.create_task(self.request(session, page)))
                    for item in items:
                        writer.writerow(item)


if __name__ == '__main__':
    header = {}
    # 分批抓取，每次抓取100页
    page = 1
    while page < 2:
        jzsc = JZSC(page, page + 1)
        asyncio.run(jzsc.fetch())
        page += 100
        time.sleep(10)
