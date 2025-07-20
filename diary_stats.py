import os
from collections import Counter
from datetime import datetime, date
import re
import jieba
import pandas as pd

def tokenize_text(text):
    # 1. 先用正则匹配所有英文单词和网址，暂时抽取出来
    # 匹配网址：https:// 或 http://开头，非空白字符直到空格
    urls = re.findall(r'https?://[^\s]+', text)

    # 匹配英文单词（连续字母，不拆分）
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)

    # 2. 把网址和英文单词在文本里替换成特殊占位符，避免jieba分词拆分他们
    placeholder = "URL_OR_ENGWORD"
    text_tmp = text
    for u in urls:
        text_tmp = text_tmp.replace(u, placeholder)
    for w in english_words:
        text_tmp = text_tmp.replace(w, placeholder)

    # 3. 用jieba分词，对替换后的文本做分词
    words_cn = [w for w in jieba.cut(text_tmp) if w.strip() and w != placeholder]

    # 4. 合并所有英文单词和网址（保持原样）
    tokens = words_cn + english_words + urls

    return tokens

def load_stopwords(stopwords_path=None):
    if not stopwords_path:
        stopwords_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords.txt")
    if not os.path.exists(stopwords_path):
        # 文件不存在，返回空集合，避免程序崩溃
        return set()
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        stopwords = set(word.strip() for word in f if word.strip())
    return stopwords

def add_stopwords(new_words, stopwords_path=None):
    """
    向停用词文件中添加新词，避免重复
    """
    if not stopwords_path:
        stopwords_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords.txt")

    if isinstance(new_words, str):
        new_words = {new_words}
    else:
        new_words = set(new_words)

    # 加载已有的
    current_stopwords = load_stopwords(stopwords_path)
    updated_stopwords = current_stopwords | new_words

    # 写回文件
    with open(stopwords_path, 'w', encoding='utf-8') as f:
        for word in sorted(updated_stopwords):
            f.write(word + '\n')

    return len(new_words - current_stopwords), len(updated_stopwords)

def extract_date_from_path(dirpath, filename, root_path):
    """
    根据相对路径和文件名，组合成完整日期
    例如目录：root_path/2025/202506/ 文件名：20250716.md
    返回 datetime.date(2025,6,16)
    """
    rel_path = os.path.relpath(dirpath, root_path)  # e.g. '2025/202506'
    parts = rel_path.replace("\\", "/").split("/")  # ['2025', '202506']

    if len(parts) < 2:
        # 不够两层目录，无法解析，返回None
        return None

    year_str = parts[0]
    month_str = parts[1]
    day_str = filename[:8]  # 取文件名前8位，形如 '20250716'

    try:
        year = int(year_str)
        # 取月份后两位作为月
        month = int(month_str[-2:])
        day = int(day_str[6:8])
        return date(year, month, day)
    except Exception:
        return None

def collect_diary_data(root_path, stopwords_path=None, start_date=None, end_date=None):
    """
    收集日记数据，支持按日期范围筛选
    返回：
    - dataframe
    - 按年、月、日统计字数的字典（只有对应维度有多样值时才包含）
    - 词频列表（前100）
    """

    # 如果传入的是 datetime.datetime，转换为 date 类型
    if start_date and isinstance(start_date, datetime):
        start_date = start_date.date()
    if end_date and isinstance(end_date, datetime):
        end_date = end_date.date()

    entries = []
    stopwords = load_stopwords(stopwords_path)
    word_counter = Counter()

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if not filename.endswith('.md'):
                continue

            date_obj = extract_date_from_path(dirpath, filename, root_path)
            if not date_obj:
                continue

            # 日期筛选
            if start_date and date_obj < start_date:
                continue
            if end_date and date_obj > end_date:
                continue

            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            char_count = len(content)
            #增加英文词语
            import re

            def tokenize_text(text):
                words_cn = [w for w in jieba.cut(text) if w.strip() and len(w) > 1]
                #words_cn = [w for w in jieba.cut(text) if w.strip()]
                words_en = re.findall(r'\b[a-zA-Z]+\b', text)
                return words_cn + words_en

            # 在循环里：
            words_all = tokenize_text(content)
            words = [w.strip() for w in words_all if w.strip() and w.strip() not in stopwords]
            word_counter.update(words)

            entries.append({
                '文件名': filename,
                '日期': date_obj.strftime('%Y-%m-%d'),
                '年': date_obj.year,
                '月': date_obj.month,
                '日': date_obj.day,
                '字数': char_count
            })

    df = pd.DataFrame(entries)

    # 只统计维度有多样值的情况
    result = {"dataframe": df}

    if not df.empty:
        if df['年'].nunique() > 1:
            result["char_count_by_year"] = df.groupby("年")["字数"].sum().to_dict()
        else:
            result["char_count_by_year"] = {}

        if df[['年', '月']].drop_duplicates().shape[0] > 1:
            # 以字符串 "YYYY-MM" 为键
            df['年-月'] = df.apply(lambda r: f"{r['年']}-{r['月']:02d}", axis=1)
            result["char_count_by_month"] = df.groupby("年-月")["字数"].sum().to_dict()
        else:
            result["char_count_by_month"] = {}

        if df[['年', '月', '日']].drop_duplicates().shape[0] > 1:
            # 以字符串 "YYYY-MM-DD" 为键
            df['年-月-日'] = df.apply(lambda r: f"{r['年']}-{r['月']:02d}-{r['日']:02d}", axis=1)
            result["char_count_by_day"] = df.groupby("年-月-日")["字数"].sum().to_dict()
        else:
            result["char_count_by_day"] = {}

        result["word_freq"] = word_counter.most_common(100)
    else:
        result["char_count_by_year"] = {}
        result["char_count_by_month"] = {}
        result["char_count_by_day"] = {}
        result["word_freq"] = []

    return result
