# Chinese-Japanese-parallel-corpus

weblio爬取的中日翻译语句对，方便使用按50音做了整合，仅对齐未清洗未分词

<br/>

文件格式：*.zh 和 \*.ja，可直接读取  

processed.zip: 过筛

un.zip: 未过筛

CJKC.json：中日汉字对照表

ja-zhcleaner.py (加入multiprocessing并行处理库)  
 
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
