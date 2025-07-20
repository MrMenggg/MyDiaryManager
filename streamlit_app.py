import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
from diary_stats import collect_diary_data, add_stopwords
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import yaml
import altair as alt

#todo 长图保存，生成pdf，接入ai

CONFIG_PATH = "config.yaml"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    config_file = os.path.join(BASE_DIR, CONFIG_PATH)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        return {}

config = load_config()
default_root_path = config.get('base_path', '')

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)

def generate_wordcloud(word_freq):
    freq_dict = dict(word_freq)
    # 自动选择可用字体（支持中英文）
    font_candidates = [
        r"C:/Windows/Fonts/msyh.ttc",  # Windows
        r"/System/Library/Fonts/PingFang.ttc",  # macOS
        r"/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
    ]
    font_path = next((f for f in font_candidates if os.path.isfile(f)), None)

    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=400,
        background_color='white'
    ).generate_from_frequencies(freq_dict)
    return wc

def main():
    st.title("📔 日记统计与词云分析")
    # 初始化 session_state，避免 KeyError
    if 'filter_mode' not in st.session_state:
        st.session_state['filter_mode'] = "按月"
    if 'compare_filter_mode' not in st.session_state:
        st.session_state['compare_filter_mode'] = "按年"
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = date.today()
    if 'end_date' not in st.session_state:
        st.session_state['end_date'] = date.today()
    if 'selected_year' not in st.session_state:
        st.session_state['selected_year'] = None
    if 'selected_month' not in st.session_state:
        st.session_state['selected_month'] = None
    if 'stopwords_path' not in st.session_state:
        st.session_state['stopwords_path'] = None
    config = load_config()
    default_root = config.get('base_path', '')
    default_stopwords = config.get('stopwords_path', '')

    # 清除按钮
    # TODO 按钮没用，因为浏览器根本不会保存数据


    # 根目录输入
    root_path = st.text_input("📁 日记根目录（请粘贴或输入完整路径）", value=default_root, key='root_path')
    if not root_path or not os.path.isdir(root_path):
        st.warning("请输入有效的日记根目录路径！")
        st.stop()

    # 停用词上传
    uploaded_file = st.file_uploader("🚫 上传停用词文件（可选）", type=["txt"], key='uploaded_stopwords')
    stopwords_path = None
    if uploaded_file:
        os.makedirs("temp", exist_ok=True)
        stopwords_path = os.path.join("temp", uploaded_file.name)
        with open(stopwords_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state['stopwords_path'] = stopwords_path
        st.success(f"已上传停用词文件：{uploaded_file.name}")
    else:
        if st.session_state.get('stopwords_path'):
            candidate = st.session_state['stopwords_path']
            if not os.path.isabs(candidate):
                candidate = os.path.join(BASE_DIR, candidate)
            if os.path.isfile(candidate):
                stopwords_path = candidate
            else:
                # fallback 默认文件
                candidate = os.path.join(BASE_DIR, "stopwords.txt")
                if os.path.isfile(candidate):
                    stopwords_path = candidate
                    st.session_state['stopwords_path'] = candidate
                else:
                    stopwords_path = None
        else:
            candidate = os.path.join(BASE_DIR, "stopwords.txt")
            if os.path.isfile(candidate):
                stopwords_path = candidate
                st.session_state['stopwords_path'] = candidate
            else:
                stopwords_path = None
    st.write(f"当前停用词文件：{stopwords_path or '无'}")

    with st.expander("➕ 添加新的停用词"):
        new_word_input = st.text_input("输入新停用词（多个用逗号分隔）")
        if st.button("添加到停用词表"):
            if new_word_input.strip():
                new_words = [w.strip() for w in new_word_input.split(",") if w.strip()]
                added, total = add_stopwords(new_words, st.session_state.get('stopwords_path'))
                st.success(f"已添加 {added} 个新停用词，当前总数：{total}")
            else:
                st.warning("请输入至少一个词")

    # 保存路径时转换为相对路径方便迁移
    rel_stopwords_path = ''
    if stopwords_path:
        try:
            rel_stopwords_path = os.path.relpath(stopwords_path, BASE_DIR)
        except ValueError:
            rel_stopwords_path = stopwords_path

    # 保存配置按钮
    if st.button("💾 保存当前配置"):
        config['base_path'] = root_path
        config['stopwords_path'] = rel_stopwords_path
        save_config(config)
        st.success("配置已保存！")

    # 选择筛选模式
    filter_mode = st.selectbox("筛选模式", ["按日区间", "按月", "按年"], index=["按日区间", "按月", "按年"].index(st.session_state['filter_mode']), key='filter_mode')

    start_date = None
    end_date = None
    selected_year = None
    selected_month = None

    if 'filter_mode' not in st.session_state:
        st.session_state['filter_mode'] = "按月"
        col1, col2 = st.columns(2)
        if 'start_date' not in st.session_state:
            st.session_state['start_date'] = date.today()
        if 'end_date' not in st.session_state:
            st.session_state['end_date'] = date.today()
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", key='start_date')
        with col2:
            end_date = st.date_input("结束日期", key='end_date')

        if start_date > end_date:
            st.error("开始日期不能晚于结束日期")
            st.stop()

    elif filter_mode == "按月":
        year_list = sorted([int(d) for d in os.listdir(root_path) if d.isdigit()], reverse=True)
        if not year_list:
            st.warning("找不到年份目录")
            st.stop()
        if 'selected_year' not in st.session_state or st.session_state['selected_year'] not in year_list:
            st.session_state['selected_year'] = year_list[0]
        selected_year = st.selectbox("选择年份", year_list, index=year_list.index(st.session_state['selected_year']), key='selected_year')

        month_dir = os.path.join(root_path, str(selected_year))
        month_list = []
        if os.path.isdir(month_dir):
            month_list = sorted([int(d[-2:]) for d in os.listdir(month_dir) if d.isdigit()], reverse=True)
        if not month_list:
            st.warning("找不到月份目录")
            st.stop()
        if 'selected_month' not in st.session_state or st.session_state['selected_month'] not in month_list:
            st.session_state['selected_month'] = month_list[0]
        selected_month = st.selectbox("选择月份", month_list, index=month_list.index(st.session_state['selected_month']), key='selected_month')

        start_date = date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = date(selected_year, 12, 31)
        else:
            end_date = date(selected_year, selected_month + 1, 1) - pd.Timedelta(days=1)

    elif filter_mode == "按年":
        year_list = sorted([int(d) for d in os.listdir(root_path) if d.isdigit()], reverse=True)
        if not year_list:
            st.warning("找不到年份目录")
            st.stop()
        if 'selected_year' not in st.session_state or st.session_state['selected_year'] not in year_list:
            st.session_state['selected_year'] = year_list[0]
        selected_year = st.selectbox("选择年份", year_list, index=year_list.index(st.session_state['selected_year']), key='selected_year')

        start_date = date(selected_year, 1, 1)
        end_date = date(selected_year, 12, 31)

    # 调用后端采集数据
    results = collect_diary_data(root_path, stopwords_path, start_date, end_date)
    df = results["dataframe"]
    char_by_year = results.get("char_count_by_year", {})
    char_by_month = results.get("char_count_by_month", {})
    char_by_day = results.get("char_count_by_day", {})
    word_freq = results.get("word_freq", [])

    st.markdown(f"**符合条件的日记文件数量：** {len(df)}")

    # 显示字数统计
    st.subheader("📊 字数统计")
    if char_by_year:
        st.markdown("**按年统计：**")
        st.bar_chart(pd.Series(char_by_year))
    if char_by_month:
        st.markdown("**按月统计：**")
        st.bar_chart(pd.Series(char_by_month))
    if char_by_day:
        st.markdown("**按日统计：**")
        st.bar_chart(pd.Series(char_by_day))

    # 词频展示
    with st.expander("🧪 打开词频图"):
        if word_freq:
            # 表格
            df_freq = pd.DataFrame(word_freq, columns=["词语", "频率"])
            st.dataframe(df_freq)

            # 图表
            st.subheader("前 30 高频词可视化")
            df_top30 = df_freq.head(30)
            chart = alt.Chart(df_top30).mark_bar().encode(
                x=alt.X("频率:Q"),
                y=alt.Y("词语:N", sort='-x')
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("无词频数据")

    # 生成词云
    if word_freq:
        st.subheader("☁️ 词云图")
        wc = generate_wordcloud(word_freq)
        fig, ax = plt.subplots(figsize=(10,5))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

        # 保存词云到文件，供分享
        save_dir = os.path.join(root_path, "wordclouds")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        wc_path = os.path.join(save_dir, f"wordcloud_{timestamp}.png")
        wc.to_file(wc_path)
        st.markdown(f"[点击下载或分享词云图]({wc_path})")

    # === 📈 区间对比分析模块 ===
    st.subheader("📊 区间对比分析")

    with st.expander("🧪 打开对比分析工具", expanded=True):
        st.markdown("选择两个日期区间，系统将对比两个时间段的字数总量与高频词汇变化。")

        compare_filter_mode = st.selectbox("区间筛选模式", ["按日区间", "按月", "按年"], index=["按日区间", "按月", "按年"].index(st.session_state['compare_filter_mode']), key="compare_filter_mode")

        def select_date_range(prefix):
            s_date = None
            e_date = None
            if compare_filter_mode == "按日区间":
                col1, col2 = st.columns(2)
                if f"{prefix}_start_date" not in st.session_state:
                    st.session_state[f"{prefix}_start_date"] = date.today()
                if f"{prefix}_end_date" not in st.session_state:
                    st.session_state[f"{prefix}_end_date"] = date.today()
                with col1:
                    s_date = st.date_input(f"{prefix} - 开始日期", value=st.session_state[f"{prefix}_start_date"], key=f"{prefix}_start_date")
                with col2:
                    e_date = st.date_input(f"{prefix} - 结束日期", value=st.session_state[f"{prefix}_end_date"], key=f"{prefix}_end_date")
                if s_date > e_date:
                    st.error(f"{prefix}：开始日期不能晚于结束日期")
                    return None, None

            elif compare_filter_mode == "按月":
                year_list = sorted([int(d) for d in os.listdir(root_path) if d.isdigit()], reverse=True)
                if not year_list:
                    st.warning("找不到年份目录")
                    return None, None
                if f"{prefix}_year" not in st.session_state or st.session_state[f"{prefix}_year"] not in year_list:
                    st.session_state[f"{prefix}_year"] = year_list[0]
                selected_year = st.selectbox(f"{prefix} - 选择年份", year_list, index=year_list.index(st.session_state[f"{prefix}_year"]), key=f"{prefix}_year")

                month_dir = os.path.join(root_path, str(selected_year))
                month_list = []
                if os.path.isdir(month_dir):
                    month_list = sorted([int(d[-2:]) for d in os.listdir(month_dir) if d.isdigit()], reverse=True)
                if not month_list:
                    st.warning("找不到月份目录")
                    return None, None
                if f"{prefix}_month" not in st.session_state or st.session_state[f"{prefix}_month"] not in month_list:
                    st.session_state[f"{prefix}_month"] = month_list[0]
                selected_month = st.selectbox(f"{prefix} - 选择月份", month_list, index=month_list.index(st.session_state[f"{prefix}_month"]), key=f"{prefix}_month")

                s_date = date(selected_year, selected_month, 1)
                if selected_month == 12:
                    e_date = date(selected_year, 12, 31)
                else:
                    e_date = date(selected_year, selected_month + 1, 1) - pd.Timedelta(days=1)

            elif compare_filter_mode == "按年":
                year_list = sorted([int(d) for d in os.listdir(root_path) if d.isdigit()], reverse=True)
                if not year_list:
                    st.warning("找不到年份目录")
                    return None, None
                if f"{prefix}_year" not in st.session_state or st.session_state[f"{prefix}_year"] not in year_list:
                    st.session_state[f"{prefix}_year"] = year_list[0]
                selected_year = st.selectbox(f"{prefix} - 选择年份", year_list, index=year_list.index(st.session_state[f"{prefix}_year"]), key=f"{prefix}_year")

                s_date = date(selected_year, 1, 1)
                e_date = date(selected_year, 12, 31)
            return s_date, e_date

        compare_start_1, compare_end_1 = select_date_range("区间1")
        compare_start_2, compare_end_2 = select_date_range("区间2")

        if compare_start_1 and compare_end_1 and compare_start_2 and compare_end_2:
            result_1 = collect_diary_data(root_path, stopwords_path, compare_start_1, compare_end_1)
            result_2 = collect_diary_data(root_path, stopwords_path, compare_start_2, compare_end_2)

            df1 = result_1["dataframe"]
            if df1.empty or '字数' not in df1.columns:
                st.warning("区间1没有符合条件的日记文件，无法统计字数")
                return  # 或者用 continue 跳过，避免后续报错

            char_count_1 = df1["字数"].sum()

            count_1 = len(result_1["dataframe"])
            avg_1 = char_count_1 / count_1 if count_1 > 0 else 0

            df2 = result_2["dataframe"]
            if df2.empty or '字数' not in df2.columns:
                st.warning("区间2没有符合条件的日记文件，无法统计字数")
                return

            char_count_2 = df2["字数"].sum()

            count_2 = len(result_2["dataframe"])
            avg_2 = char_count_2 / count_2 if count_2 > 0 else 0

            st.markdown(f"📐 区间1总字数：**{char_count_1}**，日均字数：**{avg_1:.2f}** （{count_1} 篇）")
            st.markdown(f"📐 区间2总字数：**{char_count_2}**，日均字数：**{avg_2:.2f}** （{count_2} 篇）")

            delta = char_count_2 - char_count_1
            delta_str = f"📈 增加了 {delta}" if delta > 0 else f"📉 减少了 {abs(delta)}"
            st.markdown(f"📊 总字数变化：{delta_str}")
            avg_delta = avg_2 - avg_1
            avg_delta_str = f"📈 增加了 {avg_delta:.2f}" if avg_delta > 0 else f"📉 减少了 {abs(avg_delta):.2f}"
            st.markdown(f"📊 日均字数变化：{avg_delta_str}")

            # 对比词云
            st.markdown("☁️ 高频词对比（Top 100）")

            word_freq_1 = dict(result_1.get("word_freq", [])[:100])
            word_freq_2 = dict(result_2.get("word_freq", [])[:100])

            # 合并两个词典，计算词频差异
            all_words = set(word_freq_1.keys()) | set(word_freq_2.keys())
            diff_data = {
                "词汇": [],
                "区间1频率": [],
                "区间2频率": [],
                "变化": []
            }

            for word in sorted(all_words):
                freq1 = word_freq_1.get(word, 0)
                freq2 = word_freq_2.get(word, 0)
                diff_data["词汇"].append(word)
                diff_data["区间1频率"].append(freq1)
                diff_data["区间2频率"].append(freq2)
                diff_data["变化"].append(freq2 - freq1)

            diff_df = pd.DataFrame(diff_data).sort_values("变化", ascending=False)
            st.dataframe(diff_df, use_container_width=True)

            # 生成两个词云图
            st.markdown("☁️ 词云图对比")

            # --- 词云图部分 ---
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            wc1 = generate_wordcloud(result_1["word_freq"])
            wc2 = generate_wordcloud(result_2["word_freq"])
            axes[0].imshow(wc1, interpolation='bilinear')
            axes[0].axis("off")
            axes[0].set_title("区间1")
            axes[1].imshow(wc2, interpolation='bilinear')
            axes[1].axis("off")
            axes[1].set_title("区间2")
            st.pyplot(fig)

            # --- 条形图部分 ---
            st.markdown("📊 高频词对比（Top 30）")

            # 构造 DataFrame
            df1 = pd.DataFrame(result_1["word_freq"][:30], columns=["词语", "频率"])
            df1["区间"] = "区间1"

            df2 = pd.DataFrame(result_2["word_freq"][:30], columns=["词语", "频率"])
            df2["区间"] = "区间2"

            # 合并
            df_all = pd.concat([df1, df2])

            # 条形图
            chart = alt.Chart(df_all).mark_bar().encode(
                x=alt.X("频率:Q"),
                y=alt.Y("词语:N", sort='-x'),
                color="区间:N",
                tooltip=["词语", "频率", "区间"]
            ).properties(height=600)

            st.altair_chart(chart, use_container_width=True)

            # 保存对比图
            compare_dir = os.path.join(root_path, "compare_clouds")
            os.makedirs(compare_dir, exist_ok=True)
            compare_path = os.path.join(compare_dir, f"compare_wordclouds_{timestamp}.png")
            fig.savefig(compare_path, bbox_inches='tight')
            st.markdown(f"[📥 下载词云对比图]({compare_path})")

if __name__ == "__main__":
    main()
