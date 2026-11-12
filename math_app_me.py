import os
import socket
import matplotlib.pyplot as plt
import numpy as np
import requests
import streamlit as st
import urllib3.util.connection as urllib3_cn


def allowed_gai_family():
  return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stHorizontalBlock"] > div:first-child {
        border-right: 2px solid #000000;
        padding-right: 2rem;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) {
        padding-left: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("数学用AIアプリ")

problem = st.text_area(
    "数学の問題を入力してください",
    placeholder="例：y = x^2 - 4 のグラフを書いて、x軸との交点を教えて",
)

if st.button("解説を見る") and problem:
  api_key = os.environ.get("GEMINI_API_KEY")
  if not api_key:
    st.error(
        "APIキーが設定されていません。ターミナルで \$env:GEMINI_API_KEY を設定してください。"
    )
  else:
    with st.spinner("AIが考えています..."):
      full_url = "".join([
          "https",
          "://",
          "generativelanguage",
          ".googleapis.com",
          "/v1beta/models/",
          "gemini-3.5-flash-lite",
          ":generateContent",
      ])

      prompt = (
          "次の数学の問題を解き、日本語の「解説」、途中式・答えの「数式（LaTeX形式）」、および「グラフ描画用のPythonコード」を分けて出力してください。\n"
          "必ず以下のフォーマット通りに出力し、余計な挨拶は書かないでください。\n\n"
          "解説の文章をここに書く\n\n"
          "===式===\n"
          "1行目の数式（\$マークは不要）\n"
          "2行目の数式（\$マークは不要）\n\n"
          "===グラフ===\n"
          "関数や図形などグラフを描画すべき問題の場合は、matplotlib.pyplot(plt)とnumpy(np)を使ったPythonコードのみを出力してください。\n"
          "条件1: plt.show() は絶対に書かないこと。\n"
          "条件2: グラフ内の文字（title, xlabel, ylabel, label）は文字化け防止のため必ず英語または数式のみにし、日本語は一切使わないこと。\n"
          "条件3: グリッド線(plt.grid(True))とx軸・y軸の基準線(axhline, axvline)を入れて見やすくすること。\n"
          "条件4: グラフが不要な問題（単なる計算など）の場合は、単語で「なし」とだけ書くこと。\n\n"
          f"問題: {problem}"
      )

      payload = {"contents": [{"parts": [{"text": prompt}]}]}

      try:
        res = requests.post(
            full_url,
            params={"key": api_key.strip()},
            json=payload,
            timeout=(5, 20),
        )

        if res.status_code != 200:
          st.error(f"サーバーエラー (コード {res.status_code}): {res.text}")
        else:
          data = res.json()
          candidate = data["candidates"].pop(0)
          part = candidate["content"]["parts"].pop(0)
          text = part["text"]

          explanation_part = text
          formula_part = ""
          graph_code = ""

          if "===式===" in text:
            explanation_part, rest = text.split("===式===", 1)
            if "===グラフ===" in rest:
              formula_part, graph_code = rest.split("===グラフ===", 1)
            else:
              formula_part = rest

          col_left, col_right = st.columns(2)

          with col_left:
            st.subheader("解説")
            st.write(explanation_part.strip())

          with col_right:
            st.subheader("式")
            for line in formula_part.strip().split("\n"):
              if line.strip():
                st.latex(line.strip().strip("\$"))

            clean_code = graph_code.strip()
            if clean_code and "なし" not in clean_code:
              clean_code = (
                  clean_code.replace("```python", "")
                  .replace("```", "")
                  .strip()
              )
              st.subheader("グラフ")
              try:
                plt.clf()
                fig, ax = plt.subplots()
                exec_env = {"plt": plt, "np": np, "fig": fig, "ax": ax}
                exec(clean_code, exec_env)
                st.pyplot(plt.gcf())
              except Exception as plot_err:
                st.info(f"グラフの自動生成をスキップしました: {plot_err}")

      except Exception as e:
        st.error(f"通信エラー: {e}")
