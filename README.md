# Chinese-Japanese-parallel-corpus

weblio爬取的中日翻译语句对，方便使用按50音做了整合，仅对齐未清洗未分词

<br/>

文件格式：*.zh 和 \*.ja，可直接读取  

processed.zip: 过筛

un.zip: 未过筛

CJKC.json：中日汉字对照表

ja-zhcleaner.py (加入multiprocessing并行处理库)  

&emsp;--file_type, default="single")  #双语文件模式/两个单文件模式
  
&emsp;--file_path, default=None) #双语文件路径或单文件的日语文件路径
  
&emsp;--file_path2, default=None) #单文件的中文文件路径
  
&emsp;--output_1, default='./filted.jazh') #输出文件路径1(筛选过)
  
&emsp;--output_2, default='./unclean.jazh') #输出文件路径2(被筛选掉的)
  
&emsp;--pool", default=8) #并行池数
  
&emsp;--mappingtable_path, default="./kanji_mapping_table.txt") #汉字对照表路径

&emsp;--commonhanzi_path, default="./3500common_hanzi_table.txt") #3500常用汉字（中文）表
  
&emsp;--sn_ratio, default=0.5) #数字符号字母量筛选比例
  
&emsp;--bl_ratio, default=0.5) #中日文长度筛选比例
  
&emsp;--ratio_zh, default=0.1) #共通汉字占中文长度筛选比例
  
&emsp;--ratio_jp, default=0.3) #共通汉字占日语长度筛选比例
  
&emsp;--ratio_gap, default=0.25) #实词占比筛选比例

<br/>

筛选方法：
常用汉字筛选 / 

数字、字母、符号占比筛选 / 

中文里混了日语筛选 / 

中日语料长度比筛选 / 

#极其特殊符号筛选 / 

生僻字筛选 / 

相同连续子串筛选(长度大于一个成语（4）,不是日期 且不是大部分为非中文名词) / 

简易1-gram常用汉字转换后重叠比例筛选 / 

实词占比差筛选(jieba:中文分词, nagisa: 日语分词)
