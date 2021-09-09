# get_movie_info
"""获取猫眼电影中当前热门影片信息"""
获取到的结果保存为: -> list[dict, dict, dict, ...]
现只在运行结束后将结果数据打印出来，可自行保存到本地

use tools:\n
  selenium
  
need pakages:
  selenium
  lxml
  requests
  fontTools
  difflib
  cv2
 
页面中反爬机制：
  票房等一些数字进行了字体加密（已解决）
  进入下一页后会出现滑块验证码（已解决）
