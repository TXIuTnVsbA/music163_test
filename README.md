# music163_test

Core.js

		

FM_play_test.py

		输入play或者next开始播放，默认红心歌曲
		
		del命令取消默认红心并且将歌曲丢进FM的垃圾桶里，
		
		原理：
		
			利用web版网易云的api获取私人Fm的歌单，
		
			再利用songid转换成mp3_url的api下载mp3，
		
			播放mp3并提交数据表示已经听完一首歌且红星这首歌，
		

test_get_song_url.py

		songid转换成mp3_url的api
		
test_phone_login.py

		登录函数
		
tornado_test_url.py

		将songid转换成mp3_url，再套用tornado框架反馈
		
100.py

		利用提交函数刷听歌量

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
