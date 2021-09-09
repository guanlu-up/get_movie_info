from base_data import NUM2ARRAY_MY, NUM2ARRAY_GYS, EN2INT_QD
from difflib import SequenceMatcher
from fontTools.ttLib import TTFont
from lxml import etree
import re
import cv2


class SecretFont:

    @staticmethod
    def analysis_font_qd(encrypted_char, woff_path):
        """解析起点小说页面中的加密字体
        :param encrypted_char: 页面中原始的加密字符
        :param woff_path: 字体文件路径
        :return: 加密字体对应的真实字符 -> list
        """
        decimals = [ord(encrypted_char[i]) for i in range(len(encrypted_char))]
        font_obj = TTFont(woff_path)
        result = []
        for decimal in decimals:
            english = [v for k, v in font_obj.getBestCmap().items() if decimal == k]
            if not english:
                print(f"转为十进制的{decimal},不在此woff文件中")
                continue
            result.append(english[0])
        return [str(EN2INT_QD.get(i)) for i in result]

    @staticmethod
    def get_array(encrypted_char, font_path):
        """获取字体文件中对应字体的轮廓形状信息
        :param encrypted_char: 页面中原始的加密字符
        :param font_path: xml字体文件路径
        :return: 字形轮廓信息 -> list
        """
        src_hex = hex(ord(encrypted_char))
        with open(font_path, 'r') as file:
            file_content = file.read()

        # 将XML文件中第一行声明信息去除
        content = re.sub(r'<\?.+\?>', '', file_content)
        xml = etree.XML(content)
        # 获取文件中十六进制与描述名字的对应关系
        code = xml.xpath('//cmap_format_12/map/@code')
        name = xml.xpath('//cmap_format_12/map/@name')
        hex2name = {k: v for k, v in zip(code, name)}
        target_name = hex2name.get(src_hex)
        if not target_name:
            raise ValueError(f"十进制字体:{ord(encrypted_char)},不在此文件中")

        # 获取指定描述名字的字形轮廓信息并格式化
        text = xml.xpath(f'//CharString[@name="{target_name}"]/text()')
        result = [int(j) for i in text[0].split('\n') for j in i.split(' ') if not j.isalpha() and j]

        return result

    def analysis_font_gys(self, encrypted_char, xml_path):
        """解析中国供应商页面中的加密字体
        :param encrypted_char: 页面中原始的加密字符
        :param xml_path: 字体文件转为xml文件后的路径
        :return: 加密字体对应的真实字符 -> list
        """
        result = []
        for i in range(len(encrypted_char)):
            char_array = self.get_array(encrypted_char[i], xml_path)
            for num, array in NUM2ARRAY_GYS.items():
                if char_array == array:
                    result.append(num)
        return result

    @staticmethod
    def analysis_font_my(encrypted_char, woff_path):
        """解析猫眼电影页面中的加密字体
        :param encrypted_char: 页面中原始的加密字符
        :param woff_path: 字体文件路径
        :return: 加密字体对应的真实字符 -> list
        """
        secret_name = ["uni" + hex(ord(encrypted_char[i]))[2:].upper() for i in range(len(encrypted_char))]
        font_obj = TTFont(woff_path)
        result = []
        for name in secret_name:
            array = font_obj['glyf'][name].coordinates.array
            contrast_list = [[k, SequenceMatcher(None, array, v).ratio()] for k, v in NUM2ARRAY_MY.items()]
            result.append(str(max(contrast_list, key=lambda x: x[1])[0]))
        return result


def show_image(img_array, resize_flag=False):
    """展示图片"""
    maxHeight = 540
    maxWidth = 960
    scaleX = maxWidth / img_array.shape[1]
    scaleY = maxHeight / img_array.shape[0]
    scale = min(scaleX, scaleY)
    if resize_flag and scale < 1:
        img_array = cv2.resize(img_array, (0, 0), fx=scale, fy=scale)
    cv2.imshow('auth_code', img_array)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


class ComputeSlider:
    """计算滑块验证码需要滑动的距离
    将验证码背景大图和需要滑动的小图进行处理,先在大图中找到相似的小图位置,再获取对应的像素偏移量"""
    def __init__(self, background_path: str, small_image_path: str, offset_top_px: int, show_img=False):
        """
        :param background_path: 验证码背景大图
        :param small_image_path: 需要滑动的小图
        :param offset_top_px: 小图距离在大图上的顶部边距(像素偏移量)
        :param show_img: 是否展示图片
        """
        self.background_img = None
        self.tpl_img = None
        self.offset_px = offset_top_px
        self.show_img = show_img
        # 如果小图的长度与大图的长度一致则不用将大图进行切割,可以将self.cutting_background()注释掉
        self.cutting_background(background_path, small_image_path)

    def handle_image(self):
        """处理背景图和需要滑动的小图
        :return: 终点距离
        """
        # 将小图转换为灰色
        tpl_gray = cv2.cvtColor(self.tpl_img, cv2.COLOR_BGR2GRAY)
        h, w = tpl_gray.shape
        # 将背景图进行二值化处理
        _, thresh = cv2.threshold(self.background_img, 150, 255, cv2.THRESH_BINARY)
        Background_gray = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)
        Background_gray2 = cv2.bitwise_not(Background_gray)
        # 得到二值化后的小图
        _, threshold_img = cv2.threshold(tpl_gray, 10, 255, cv2.THRESH_BINARY)
        # 将小图与大图进行模板匹配,找到所对应的位置
        result = cv2.matchTemplate(Background_gray2, threshold_img, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 左上角位置
        top_left = (max_loc[0], max_loc[1] + self.offset_px)
        # 右下角位置
        bottom_right = (top_left[0] + w, top_left[1] + h)
        # 在源背景图中画出小图需要移动到的终点位置
        cv2.rectangle(self.background_img, top_left, bottom_right, (0, 0, 255), 2)
        if self.show_img:
            # 展示图片
            show_image(self.background_img)
        return top_left[0]

    def cutting_background(self, background_path, small_image_path):
        """切割验证码图片的上下多余部分"""
        background_img = cv2.imread(background_path)
        tpl_img = cv2.imread(small_image_path)
        px_up = self.offset_px
        px_down = self.offset_px + tpl_img.shape[0]
        # 将大图中上下多余部分去除
        self.background_img = background_img[px_up:px_down, :]
        self.tpl_img = tpl_img

    def get_distance(self):
        return self.handle_image()
