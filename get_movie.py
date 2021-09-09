import time
import re
import os
import random
import requests
from random import randint
from common import SecretFont, ComputeSlider
from lxml import etree
from selenium.webdriver import Chrome, ActionChains


class Main(object):
    """使用selenium获取猫眼电影页面中最新上映影片信息"""
    def __init__(self):
        self.url = 'https://maoyan.com/'
        self.font_folder = os.path.join(os.path.expanduser('~'), "Desktop", "MaoYanMovie")
        self.filepath = {}
        self.browser = None
        self.xpath = None
        self.html = None
        self.movie_content = []
        self.code_times = 10    # 验证码重试的次数

    def init_filepath(self):
        """初始化文件路径"""
        self.filepath = {
            'font_file': os.path.join(self.font_folder, 'font.woff'),
            'small_img': os.path.join(self.font_folder, 'small.png'),
            'bg_img': os.path.join(self.font_folder, 'background.png'),
        }
        if not os.path.isdir(self.font_folder):
            os.mkdir(self.font_folder)

    def init_xpath(self):
        """初始化xpath"""
        self.xpath = {
            'main_page': '//div[@class="main"]',
            'all_movie_button': '//a[@data-act="all-playingMovie-click"]',
            'movie_list': '//dl[@class="movie-list"]/dd',
            'next_page': '//a[contains(text(), "下一页")]',
            'banner': '//div[@class="banner"]',
            'movie_CN_name': '//h1[@class="name"]/text()',
            'movie_EN_name': '//div[@class="ename ellipsis"]/text()',
            'movie_type': '(//li[@class="ellipsis"])[1]//text()',
            'time_length': '(//li[@class="ellipsis"])[2]//text()',
            'release_time': '(//li[@class="ellipsis"])[3]//text()',
            'director': '(//div[contains(text(),"导演")]/following-sibling::*[1])[1]//div[@class="info"]/a//text()',
            'performer': '//li[@class="celebrity actor"]/div/a//text()',
            'role': '//li[@class="celebrity actor"]/div/span//text()',
            'movie_content': '//span[@class="dra"]//text()',
            'comment_user': '//div[@class="mod-content"]//ul/li//span[@class="name"]//text()',
            'comment_content': '//div[@class="mod-content"]//ul/li//div[@class="comment-content"]//text()',
            'movie_score': '//span[@class="index-left info-num"]/span//text()',
            'score_times': '//span[@class="score-num"]/span//text()',
            'box_office': '//div[@class="movie-index-content box"]/span[@class="stonefont"]//text()',
            'unit': '//div[@class="movie-index-content box"]/span[@class="unit"]//text()',
            'verification': '//div[@id="tcaptcha_transform"]/iframe',
            'bg_img': '//html[@lang="zh-cmn-Hans"]//div[@id="slideBgWrap"]/img',
            'small_img': '//html[@lang="zh-cmn-Hans"]//div[@id="slideBlockWrap"]/img',
            'drag_button': '//div[@class="tc-drag-thumb"]',
            'refresh_code': '//div[@class="tc-action-icon"]',
        }

    def wait_element_loaded(self, xpath: str, timeout=10, close_browser=False):
        """等待页面元素成功加载完成
        :param xpath: xpath表达式
        :param timeout: 最长等待超时时间
        :param close_browser: 元素等待超时后是否关闭浏览器
        """
        now_time = int(time.time())
        while int(time.time()) - now_time < timeout:
            try:
                element = self.browser.find_element_by_xpath(xpath)
                if element:
                    return True
                time.sleep(1)
            except Exception:
                pass
        else:
            if close_browser:
                self.close_browser()
            print("查找页面元素失败，如果不存在网络问题请尝试修改xpath表达式")
            return False

    @staticmethod
    def format_text(text: list, result='str'):
        """将获取到的文本内容进行格式化
        :param text: 进行格式化的文本
        :param result: 返回结果为 'list' or 'str'
        """
        temp = [i.replace('\n', '').replace(' ', '') for i in text]
        if result == 'list':
            return [i for i in temp if i]
        return ','.join([i for i in temp if i])

    @staticmethod
    def download_file(url, filepath):
        """下载远端文件到本地
        :param url: 目标url
        :param filepath: 保存的路径
        """
        response = requests.get(url)
        if not response.ok:
            return False
        with open(filepath, 'wb') as file:
            file.write(response.content)
        return True

    @staticmethod
    def handle_distance(distance):
        """将直线距离转为缓慢的轨迹"""
        import random
        current = []
        while sum(current) <= distance:
            current.append(random.randint(-2, 15))

        if sum(current) != distance:
            current.append(distance - sum(current))
        return current

    @staticmethod
    def move_slider(website, slider, track, **kwargs):
        """将滑块移动到终点位置
        :param website: selenium页面对象
        :param slider: selenium页面中滑块元素对象
        :param track: track=iterable, 小图片移动到终点的距离,iterable中的值从小到大让其分开. 如:
        [1, 1, 1, 2, 1, 3, 3, 3, 4, 5, 6, 5, 5, 6, 6, 7, 7, 7, 8, 8, 9, 9, 9, 10, 11, 8, 10, 8, 9, 3, -4]
        """
        name = kwargs.get('name', '滑块')
        try:
            if track[0] > 200:
                return track[0]
            # 点击滑块元素并拖拽
            ActionChains(website).click_and_hold(slider).perform()
            time.sleep(0.15)
            for i in track:
                # 随机上下浮动鼠标
                ActionChains(website).move_by_offset(xoffset=i, yoffset=randint(-2, 2)).perform()
            # 释放元素
            time.sleep(1)
            ActionChains(website).release(slider).perform()
            time.sleep(1)
            # 随机拿开鼠标
            ActionChains(website).move_by_offset(xoffset=randint(200, 300), yoffset=randint(200, 300)).perform()
            print(f'[网页] 拖拽 {name}')
        except Exception as e:
            print(f'[网页] 拖拽 {name} 失败 {e}')

    def get_element_text(self, element_obj, xpath, text_format=False, result='str', separator=','):
        """从页面元素对象中获取指定的文本内容
        :param element_obj: 页面元素对象(etree._Element对象)
        :param xpath: xpath表达式
        :param text_format: 是否对获取到的文本进行格式化
        :param result: 指定返回结果为 str 或 list
        :param separator: 指定返回str时的分隔符
        :return: 如果成功获取到文本则返回文本,获取不到则返回空
        """
        text = element_obj.xpath(xpath)
        if not text:
            if result == 'str':
                return ''
            return []

        if text_format:
            return self.format_text(text, result=result)
        if result == 'str':
            return separator.join(text)
        return text

    def analysis_font(self, source_str):
        """解析字体
        :param source_str: 加密后的字符
        :return: 解析后的真实字符
        """
        if not source_str:
            return '0'

        point_index = None
        unit = None
        if '.' in source_str:
            point_index = source_str.find('.')
            source_str = source_str.replace('.', '')
        if '万' in source_str:
            unit = '万'
            source_str = source_str.replace('万', '')

        # 调用解析方法
        real_str = SecretFont.analysis_font_my(source_str, self.filepath['font_file'])

        if point_index:
            real_str.insert(point_index, '.')
        if unit:
            real_str.append(unit)
        return ''.join(real_str)

    def start_browser(self):
        """启动浏览器并打开页面"""
        self.browser = Chrome()
        self.browser.maximize_window()
        self.browser.get(self.url)

    def close_browser(self):
        """关闭浏览器"""
        self.browser.quit()

    def handle_verification_code(self):
        """处理滑块验证码"""
        iframe = self.browser.find_element_by_xpath(self.xpath['verification'])
        # 切换iframe
        self.browser.switch_to.frame(iframe)
        time.sleep(1)
        # 单个滑块验证码最多重试的次数
        for _ in range(self.code_times):
            bg_img = self.browser.find_element_by_xpath(self.xpath['bg_img'])
            small_img = self.browser.find_element_by_xpath(self.xpath['small_img'])
            # 获取验证码背景图和需要滑动的小图
            bg_url = bg_img.get_attribute('src')
            small_url = small_img.get_attribute('src')
            top_px = small_img.value_of_css_property('top').replace('px', '')
            left_px = small_img.value_of_css_property('left').replace('px', '')
            # 下载背景图和小图
            self.download_file(bg_url, self.filepath['bg_img'])
            self.download_file(small_url, self.filepath['small_img'])
            # 因为页面中渲染的验证码图片是缩小1倍后的图片,
            # 那么得到的像素距离需乘以2后才是真正图片中的像素距离
            top = int(top_px) * 2
            left = int(left_px) * 2

            if self.process_slider(self.filepath['bg_img'], self.filepath['small_img'], top, left):
                self.browser.switch_to.default_content()
                break
            self.browser.find_element_by_xpath(self.xpath['refresh_code']).click()
            time.sleep(2)
        else:
            print("未能解决验证码！")
            return False
        return True

    def process_slider(self, bg_img, small_img, top_px: int, left_px: int, show_img=False):
        """调用计算轨迹方法、拖动滑块方法
        :param bg_img: 验证码背景大图(路径不能包含中文)
        :param small_img: 需要滑动的小图(路径不能包含中文)
        :param top_px: 小图距离在大图上的顶部边距(像素偏移量)
        :param left_px: 小图距离在大图上的左部边距(像素偏移量)
        :param show_img: 是否展示图片
        :return: 是否成功解决验证码
        """
        compute = ComputeSlider(bg_img, small_img, offset_top_px=top_px, show_img=show_img)
        # 获取移动所需的距离
        distance = compute.get_distance()
        # 因为页面中的图像倍缩小,所以得到像素距离后需除以2才是页面中所要移动的距离
        real_distance = (distance - left_px) / 2
        track = self.handle_distance(real_distance)
        slider_element = self.browser.find_element_by_xpath(self.xpath['drag_button'])

        self.move_slider(self.browser, slider_element, track)
        time.sleep(2)
        # 如果滑动完成则返回True
        if not self.wait_element_loaded(self.xpath['drag_button'], timeout=2, close_browser=False):
            return True
        else:
            return False

    def save_movie_info(self):
        """将页面中主要信息进行解析保存"""

        movie_CN_name = self.get_element_text(self.html, self.xpath['movie_CN_name'])
        movie_EN_name = self.get_element_text(self.html, self.xpath['movie_EN_name'])
        movie_type = self.get_element_text(self.html, self.xpath['movie_type'], text_format=True)
        movie_area = self.get_element_text(self.html, self.xpath['time_length'], text_format=True)
        release_time = self.get_element_text(self.html, self.xpath['release_time'])
        movie_content = self.get_element_text(self.html, self.xpath['movie_content'])
        director = self.get_element_text(self.html, self.xpath['director'], text_format=True)
        performer = self.get_element_text(self.html, self.xpath['performer'], text_format=True, result='list')
        role = self.get_element_text(self.html, self.xpath['role'], text_format=True, result='list')
        comment_user = self.get_element_text(self.html, self.xpath['comment_user'], text_format=True, result='list')
        comment_content = self.get_element_text(self.html, self.xpath['comment_content'], True, result='list')
        movie_score = self.get_element_text(self.html, self.xpath['movie_score'])
        score_times = self.get_element_text(self.html, self.xpath['score_times'])
        box_office = self.get_element_text(self.html, self.xpath['box_office'])
        unit = self.get_element_text(self.html, self.xpath['unit'])

        if '/' in movie_area:
            time_length = movie_area.split('/')[1]
        else:
            time_length = ''
        movie_area = movie_area.split('/')[0]

        if movie_score:
            movie_score = self.analysis_font(movie_score) + "分"
        else:
            movie_score = "暂无评分"
        score_times = self.analysis_font(score_times) + "人评分"
        box_office = self.analysis_font(box_office) + unit

        temp_dict = {
            'grab_date': time.strftime("%Y-%m-%d %H:%M:%S"),
            'movie_CN_name': movie_CN_name,
            'movie_EN_name': movie_EN_name,
            'movie_type': movie_type,
            'movie_area': movie_area,
            'time_length': time_length,
            'release_time': release_time,
            'movie_content': movie_content,
            'director': director,
            'performer_table': dict(zip(performer, role)),
            'comment': dict(zip(comment_user, comment_content)),
            'movie_score': movie_score,
            'score_times': score_times,
            'box_office': box_office,
        }
        self.movie_content.append(temp_dict)

    def process_page(self):
        """处理主页中内容"""
        if not self.wait_element_loaded(self.xpath['main_page']):
            print("主页加载失败,请检查后重试！")
            exit(-1)
        self.browser.find_element_by_xpath(self.xpath['all_movie_button']).click()

        while True:
            self.wait_element_loaded(self.xpath['movie_list'])
            movie_list = self.browser.find_elements_by_xpath(self.xpath['movie_list'])

            for movie_page in movie_list:
                movie_page.click()
                # 切换窗口
                self.browser.switch_to.window(self.browser.window_handles[-1])
                """检测是否出现验证码"""
                if self.wait_element_loaded(self.xpath['verification'], timeout=2):
                    if not self.handle_verification_code():
                        return
                self.wait_element_loaded(self.xpath['banner'])
                time.sleep(2)
                body_html = self.browser.find_element_by_xpath('//body').get_attribute("outerHTML")
                head_html = self.browser.find_element_by_xpath('//head').get_attribute("outerHTML")
                font_link = 'https:' + re.findall(r"url\('(.+?\.woff)'\)", head_html)[0]
                # 请求本次的字体文件
                self.download_file(font_link, self.filepath['font_file'])
                self.html = etree.HTML(body_html)
                self.save_movie_info()
                self.browser.close()
                # 切换窗口
                self.browser.switch_to.window(self.browser.window_handles[0])
                time.sleep(random.randint(1, 4))
            if not self.wait_element_loaded(self.xpath['next_page'], timeout=2):
                break
            self.browser.find_element_by_xpath(self.xpath['next_page']).click()

    def run(self):
        self.init_filepath()
        self.init_xpath()
        self.start_browser()
        self.process_page()
        return self.movie_content


if __name__ == '__main__':
    main = Main()
    movie_info = main.run()
    print(movie_info)
