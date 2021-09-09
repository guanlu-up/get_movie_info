# get_movie_info
"""获取猫眼电影中当前热门影片信息"""

文件描述：

    get_movie.py: 主流程，安装好第三方库后即可直接运行
    common.py: 主流程中需要的功能函数(解析字体、处理滑块验证码)
    base_data.py: 事先定义的字体匹配数据

    获取到的结果格式为: -> list[dict, dict, dict, ...]
    
现只在运行结束后将结果数据打印出来，可自行保存到本地

## use tools:

    selenium
  
## need pakages:

    selenium
    lxml
    requests
    fontTools
    difflib
    cv2
 
页面中反爬机制：

    票房等一些数字进行了字体加密（已解决）
    进入下一页后会出现滑块验证码（已解决）
