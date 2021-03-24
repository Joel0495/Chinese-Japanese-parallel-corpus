import argparse
import multiprocessing
import re, os, datetime, time
import tqdm

start = datetime.datetime.now()

parser = argparse.ArgumentParser(description='Process jazh cleaner.')
parser.add_argument("--file_type", type=str, default="single")  #双语文件模式 两个单文件模式
parser.add_argument("--file_path", type=str, default=None) #双语文件路径或单文件的日语文件路径
parser.add_argument("--file_path2", type=str, default=None) #双语文件路径或单文件的中文文件路径
parser.add_argument("--output_1", type=str, default='./filted.jazh') #输出文件路径1(筛选过)
parser.add_argument("--output_2", type=str, default='./unclean.jazh') #输出文件路径2(被筛选掉的)
parser.add_argument("--pool", dest='process_num', type=int, default=8) #并行池数
parser.add_argument("--mappingtable_path", type=str, default="./kanji_mapping_table.txt") #汉字对照表路径
parser.add_argument("--commonhanzi_path", type=str, default="./3500common_hanzi_table.txt") #3500常用汉字（中文）表
parser.add_argument("--sn_ratio", type=int, default=0.5) #数字符号字母量筛选比例
parser.add_argument("--bl_ratio", type=int, default=0.5) #中日文长度筛选比例
parser.add_argument("--ratio_zh", type=int, default=0.1) #共通汉字占中文长度筛选比例
parser.add_argument("--ratio_jp", type=int, default=0.3) #共通汉字占日语长度筛选比例
parser.add_argument("--ratio_gap", type=int, default=0.25) #实词占比筛选比例
args = parser.parse_args()
args_dic = vars(args)


file_type = args_dic['file_type']
file_path = args_dic['file_path']
file_path2 = args_dic['file_path2']
output1 = args_dic['output_1']
output2 = args_dic['output_2']
n_process = args_dic['process_num']
mappingtable_dir = args_dic['mappingtable_path']
commontable_dir = args_dic['commonhanzi_path']
sn_ratio = args_dic['sn_ratio']
bl_ratio = args_dic['bl_ratio']
ratio_zh = args_dic['ratio_zh']
ratio_jp = args_dic['ratio_jp']
ratio_gap = args_dic['ratio_gap']

try:
    with open(commontable_dir, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        hanzi = []
        for line in lines:
            line = line.replace('\n', '')
            hanzi.append(line)
except:
    raise Exception('常用汉字文件路径错误或不存在')

try:
    with open(mappingtable_dir, 'r', encoding='utf-8') as f:
        lines = f.readlines()[17:]
        
        jasc, seldom_list = {}, []
        for line in lines:
            line = line.replace('\n', '')
            jasc[line.split('\t')[0]] = line.split('\t')[-1].split(',')
            if line.split('\t')[-1].split(',') == ['N/A']:
                seldom_list.append(line.split('\t')[0])
except:
    raise Exception('mapping文件路径错误或不存在')

#常用汉字筛选
#hanzi为list，处理部分在顶部
def commonhanzi(textzh, hanzi_list):

    hanzi_filter = re.compile('[^\u4E00-\u9FD5]+')
    hanzi_only = hanzi_filter.sub('', textzh)

    for hanzi in hanzi_only:
        if hanzi not in hanzi_list:
            return False
    
    return True


#数字、字母、符号占比筛选
def symbolnumbers(textzh, textja, sn_ratio):
    zh_filter = re.compile('[^\u4E00-\u9FD5]+')
    ja_filter = re.compile('[^\u4e00-\u9fbf\u3040-\u309F\u30A0-\u30FF]+')
    zh_only = zh_filter.sub('', textzh)
    ja_only = ja_filter.sub('', textja)
    
    if zh_only and len(zh_only) > sn_ratio * len(textzh) and \
      ja_only and len(ja_only) > sn_ratio * len(textja):
        return True
    else:
        return False

#中文里混了日语筛选
def mixlingualstripper(textzh):
    delspecial = re.sub(u"([^\u4e00-\u9fbf\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3040-\u309F\u30A0-\u30FF])","",textzh)
    if delspecial >= u'\u4e00' and delspecial <= u'\u9fa5':
        return True
    else:
        return False

#中日语料长度比筛选
def unbalance(textzh, textja, bl_ratio):
    lenzh, lenja = len(textzh), len(textja)
    filter = re.compile('[^a-zA-z0-9]+')
    if lenzh > bl_ratio * lenja:
        return True

        #出现的专有名词，数字等在另一个语料里也对应出现
        #lis_zh = re.sub(filter, ' ', textzh).split()
        #lis_jp = re.sub(filter, ' ', textja).split()
        #num = 0
        #for wordnum in lis_zh:
        #    if wordnum not in lis_jp:
        #        num += 1
        
        #if num <= 0.6*len(lis_zh):
        #    return False
        #else:
        #    return True

    else:
        return False

#极其特殊符号筛选
def specialsymbol(textzh, textja):
    commonsym = '＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､　、〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。'
    
    for sym in re.sub('[a-zA-Z0-9\u4e00-\u9fbf\u3040-\u309F\u30A0-\u30FF\s]+', "", textzh):
        if sym not in commonsym: 
            return False
    
    for sym in re.sub('[a-zA-Z0-9\u4e00-\u9fbf\u3040-\u309F\u30A0-\u30FF\s]+', "", textja):
        if sym not in commonsym: 
            return False
    
    return True

#生僻字筛选
def seldom(seldom_list, textzh, textja):
    kanjis = re.sub(u"([^\u4e00-\u9fbf])","",textja)
    for kanji in kanjis:
        if kanji in seldom_list:
            return False
    
    return True

#相同连续子串筛选(长度大于一个成语（4）不是日期 且不是大部分为非中文名词)
def samecontentidentify(zh, ja):

    def longestCommonSubsequence(text1, text2):
        n, m = len(text1), len(text2)
        res = 0
        
        dp = [[0]*(m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if i == 0 or j == 0:
                    dp[i][j] == 0
                if text1[i - 1] == text2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    res = max(res, dp[i][j])
                else:
                    dp[i][j] == 0

        return res, dp

    def lcschecker(text1, res, dp):
        common = ''

        for row in range(len(dp)):
            for col in range(len(dp[row])):
                if dp[row][col] == res:
                    index_t1, tmp = row, res
                    while True:
                        tmp -= 1
                        row -= 1
                        col -= 1
                        if dp[row][col] == tmp and tmp == 0:
                            common += text1[row:index_t1]
                            break
                        if dp[row][col] == tmp: continue
                        else: break

        return common

    lmax, mat = longestCommonSubsequence(ja, zh)
    if lmax > 4:
        if ('月' or '日') not in ja:
            common = lcschecker(ja, lmax, mat)
            filter_pattern = re.compile('[^\u4E00-\u9FD5]+')
            chinese_only = filter_pattern.sub('', common)
            if chinese_only != '' and len(chinese_only) > 0.5 * len(common):
                return False
            else:
                return True
        else:
            return True
    else:
        return True


#1–gram common Chinese character overlap with threshold of 0.1 for Chinese and 0.3 for Japanese.
#jasc: dict from kanji_mapping_table.txt(日中汉字转换)。 注：格式为列表
def CC(jasc, textzh, textja, ratio_zh, ratio_jp):
    kanjis = re.sub(u"([^\u4e00-\u9fbf])","",textzh)
    ja2sc_list = []
    for kanji in kanjis:
        if kanji in jasc:
            ja2sc_list.append(jasc[kanji])
        else:
            ja2sc_list.append(list(kanji))
    
    common_count = 0
    for sc_list in ja2sc_list:
        for sc in sc_list:
            if sc in textzh:
                common_count += 1
                break
            else:
                continue
    
    if common_count >= ratio_zh*len(textzh) and common_count >= ratio_jp*len(kanjis):
        return True
    else:
        return False


#nagisa, jieba库
#default listja = ['副詞', '名詞', '動詞', '形容詞', '形状詞']
#default listzh = ['n', 'v', 'd', 'a']
def contentwords(content_listja, content_listzh, textzh, textja, ratio_gap):
    zhwords = jieba.posseg.cut(textzh)

    jawords_all  = nagisa.tagging(textja)
    jawords_content = nagisa.extract(textja, extract_postags=content_listja)

    count_content, count_total = 0, 0

    for word, flag in zhwords:
        count_total += 1
        if flag[0] in content_listzh:
            count_content += 1

    if abs( (len(jawords_content.words) / len(jawords_all.words)) - (count_content / count_total) ) > ratio_gap:
        return False
    
    return True


#---------------------------
def datafilter(data, sn_ratio = sn_ratio, bl_ratio = bl_ratio, \
    ratio_zh = ratio_zh, ratio_jp = ratio_jp, ratio_gap = ratio_gap):
    
    t1 = data.split('\t')[-1].replace('\n', '')
    t2 = data.split('\t')[0].replace('\n', '')

    if not t1.split() or not t2.split(): #去除空白
        return '丢了吧', 2

    jud = 0
    
    try:
        import nagisa
        import jieba.posseg

        if t1 != t2 and \
            symbolnumbers(t1, t2, sn_ratio) and \
            mixlingualstripper(t1) and \
            specialsymbol(t1, t2) and \
            commonhanzi(t1, hanzi) and \
            unbalance(t1, t2, bl_ratio) and \
            seldom(seldom_list, t1, t2) and \
            CC(jasc, t1, t2, ratio_zh, ratio_jp) and \
            samecontentidentify(t1, t2) and \
            contentwords(['副詞', '名詞', '動詞', '形容詞', '形状詞'], \
                         ['d', 'n', 'v', 'a'], t1, t2, ratio_gap):
            jud = 1
            
    except:
        if t1 != t2 and \
            symbolnumbers(t1, t2, sn_ratio) and \
            mixlingualstripper(t1) and \
            specialsymbol(t1, t2) and \
            commonhanzi(t1, hanzi) and \
            unbalance(t1, t2, bl_ratio) and \
            seldom(seldom_list, t1, t2) and \
            CC(jasc, t1, t2, ratio_zh, ratio_jp) and \
            samecontentidentify(t1, t2):
            jud = 1
    
    if jud == 1:
        #去除首位空白
        if t2[0] == ' ':
            t2 = t2[1:]
        return (t2 + '\t' + t1 + '\n'), 1
    else:
        if t2[0] == ' ':
            t2 = t2[1:]
        return (t2 + '\t' + t1 + '\n'), 0


def dataprocess(line, num, n_process):
    list_f, list_u = [], []
    for i in tqdm.tqdm(line[num * len(line) // n_process : (num + 1) * len(line) // n_process]):
        text, jud = datafilter(i, sn_ratio = sn_ratio, bl_ratio = bl_ratio, ratio_zh = ratio_zh, \
                                  ratio_jp = ratio_jp, ratio_gap = ratio_gap)
        if jud == 2: continue
        elif jud == 1: 
            list_f.append(text)
        else: 
            list_u.append(text)
    
    return list_f, list_u

#--------------------------------------------------------------------------

if __name__ == '__main__':

    filted, unclean = [], []

    if file_type == 'single':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all = f.read()
        except:
            raise Exception('*.jazh文件不存在')

    if file_type != 'single':
        try:
            confirm1 = file_path.split('.')[-1]
            confirm2 = file_path2.split('.')[-1]
        except:
            raise Exception('*.ja或 *.zh文件至少一个路径不存在')

        if confirm1 != 'ja' or confirm2 != 'zh':
            raise Exception('请确认path为ja，path2为zh')

        with open(file_path, 'r', encoding='utf-8') as f1, \
             open(file_path2, 'r', encoding='utf-8') as f2:
            l1 = f1.readlines()
            l2 = f2.readlines()
    
        all = []
        for line in range(len(l1)):
            all.append(l1[line] + '\t' + l2[line])
    
    print('总条数：', len(all))
    line = list(set(all))
    print('去重：', len(line))
    
    try:
        import nagisa
        import jieba.posseg
    except:
        print('----未安装库nagisa和jieba，将不使用实词筛选函数----')

    pool = multiprocessing.Pool(processes = n_process)
    pool_list = []
    for num in range(n_process):
        pool_list.append(pool.apply_async(dataprocess, (line, num, n_process)))
    
    for part in pool_list:
        filted.append(part.get()[0])
        unclean.append(part.get()[1])
    
    pool.close()
    pool.join()

    with open(output1, 'w', encoding='utf-8') as fw1, \
         open(output2, 'w', encoding='utf-8') as fw2:
        for f in filted:
            for i in f:
                #i = i.replace('【', '').replace('】', '')
                #i = i.replace('「', '').replace('」', '')
                #i = re.sub(u"\\（.*?）", "", i)
                fw1.write(i)
        
        for f in unclean:
            for i in f:
                fw2.write(i)
    
    end = datetime.datetime.now()
    print('共', len(line), '条用时：', end-start)
    print('保留对数：', sum([len(i) for i in filted]))