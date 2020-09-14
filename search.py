import json
import requests
from win10toast import ToastNotifier
import time
import threading
import re


class CourseSearcher():

    def __init__(self):
        self.cookies = dict()
        self.cookies_file = 'cookies.txt'
        self.search_urls = {
            '学位基础课': 'http://yjsxk.fudan.edu.cn/yjsxkapp/sys/xsxkappfudan/xsxkCourse/loadXwzykCourseInfo.do?_=1599458690255',
            # '学位专业课': 'http://yjsxk.fudan.edu.cn/yjsxkapp/sys/xsxkappfudan/xsxkCourse/loadXwzykCourseInfo.do?_=1599458706907',
            # '专业选修课': 'http://yjsxk.fudan.edu.cn/yjsxkapp/sys/xsxkappfudan/xsxkCourse/loadXwzykCourseInfo.do?_=1599458740795',
        }
        self.toaster = ToastNotifier()
        self.blacklist = [
            '软件定义网络',
            '智能视频监控技术',
            '计算理论',
            '知识图谱',
            '高级数据库'
        ]
        self.whitelist = [
            '机器学习理论'
        ]

    def read_cookies(self):
        with open(self.cookies_file, 'r', encoding='utf-8') as f:
            cookies_txt = f.read().strip(';')  # 读取文本内容
            # 由于requests只保持 cookiejar 类型的cookie，而我们手动复制的cookie是字符串需先将其转为dict类型后利用requests.utils.cookiejar_from_dict转为cookiejar 类型
            # 手动复制的cookie是字符串转为字典：
            for cookie in cookies_txt.split(';'):
                name, value = cookie.strip().split('=', 1)  # 用=号分割，分割1次
                self.cookies[name] = value  # 为字典cookies添加内容
        # 将字典转为CookieJar：
        cookiesJar = requests.utils.cookiejar_from_dict(
            self.cookies, cookiejar=None, overwrite=True)
        return cookiesJar

    def available_hints(self, course):
        self.toaster.show_toast("有余量了",
                                "{}: {}".format(
                                    course['KCLBMC'], course['KCMC']),
                                icon_path=None,
                                duration=5,
                                threaded=False)

    def is_course_available(self, course_type_resp):
        print('=============================================')
        for index, course in enumerate(course_type_resp['datas']):
            print("{} {} {}".format(
                course['KCMC'], course['KXRS'], course['DQRS']))

            if course['KXRS'] != course['DQRS']:
                if course['KCMC'] in self.whitelist:
                    if course['RKJS'] == '池明旻':
                        continue
                    self.available_hints(course)
                else:
                    if course['IS_CONFLICT'] == 0 and course['KCMC'] not in self.blacklist:
                        self.available_hints(course)

    # 刷课
    def search(self):
        self.session = requests.session()
        self.session.cookies = self.read_cookies()
        while True:
            time.sleep(1.5)
            for course_type, url in self.search_urls.items():
                try:
                    response = self.session.get(url, timeout=5)
                except:
                    continue

                response = response.content.decode()
                response = json.loads(response)

                self.is_course_available(response)

    # 抢课（捡漏）
    def frequent_course_request(self):
        self.session_choose = requests.session()
        self.session_choose.cookies = self.read_cookies()

        form_data = {
            'bjdm': '2020202101COMP630036.02',
            'lx': '8',
            'csrfToken': None
        }

        while True:
            new_token = self._refresh_csrfToken(self.session_choose)
            form_data['csrfToken'] = new_token

            while True:
                time.sleep(1.5)
                response = self._request_course(self.session_choose, form_data)

                if response['code'] == 0:
                    if '过期' in response['msg']:
                        break
                else:
                    return

    def _request_course(self, session, form_data):
        response = session.post(
            url='http://yjsxk.fudan.edu.cn/yjsxkapp/sys/xsxkappfudan/xsxkCourse/choiceCourse.do?_=1600059897179',
            data=form_data
        )
        response = response.content.decode()
        response = json.loads(response)

        print(response)
        return response

    def _refresh_csrfToken(self, session):
        response = self.session_choose.get(
            'http://yjsxk.fudan.edu.cn/yjsxkapp/sys/xsxkappfudan/xsxkHome/gotoChooseCourse.do')
        response = response.content.decode()
        new_token = re.findall(r"csrfToken\" value='(.*)'", response)[0]

        return new_token


if __name__ == "__main__":
    s = CourseSearcher()
    # s.search()
    # s.test_choose_course()
    s.frequent_course_request()
