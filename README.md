# music163_test
网易云音乐_算法测试（登录算法似乎已经过期）

FM_play_test.py

		输入play或者next开始播放，默认红心歌曲
		
		del命令取消默认红心并且将歌曲丢进FM的垃圾桶里，
		
		原理：
		
				利用web版网易云的api获取私人Fm的歌单，
		
				再利用songid转换成mp3_url的api下载mp3，
		
				播放mp3并提交数据表示已经听完一首歌且红星这首歌，
		

大部分参考：

	https://github.com/darknessomi/musicbox
	
	http://www.jianshu.com/p/3269321e0df5
	
	https://www.zhihu.com/question/36081767
	
  
	
如何获取加密前的json请求？

	断点关键字：
	
		params:
	and
		var h = {}
		
Crypto在win下用不了？

	http://blog.csdn.net/werewolf_st/article/details/45935913
