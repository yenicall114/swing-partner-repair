import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

st.set_page_config(page_title="파트너 대응 검색 봇", layout="wide")

@st.cache_data
def load_data() -> Dict[str, List[Dict[str, Any]]]:
    data = {"regular": [], "slack": []}

    file1 = Path("(종료)파트너사 대응 답변 예시.xlsx")
    file2 = Path("파트너 대응 메뉴얼_오류코드_.xlsx")
    file3 = Path("슬랙_QA_정리.xlsx")

    if file1.exists():
        df1 = pd.read_excel(file1)
        for _, row in df1.iterrows():
            title = str(row.get("문제내용") or row.get("발생 문제 구분") or "").strip()
            description = str(row.get("발생문제 항목값") or "").strip()
            response = str(row.get("응대방법") or row.get("해결방안") or "").strip()
            if not title and not response:
                continue
            data["regular"].append({
                "source": file1.name,
                "title": title if title else "(제목 없음)",
                "description": description,
                "response": response if response else title,
            })

    if file2.exists():
        xls = pd.ExcelFile(file2)
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet)
            for _, row in df.iterrows():
                error_code = str(row.get("오류 코드") or "").strip()
                title = f"{sheet} - {error_code}" if error_code else sheet
                description = str(row.get("원인") or "").strip()
                response = str(row.get("대응내용") or "").strip()
                if not response and not description:
                    continue
                data["regular"].append({
                    "source": f"{file2.name} ({sheet})",
                    "title": title,
                    "description": description,
                    "response": response if response else description,
                })

    if file3.exists():
        df3 = pd.read_excel(file3)
        for _, row in df3.iterrows():
            title = str(row.get("질문") or "").strip()
            description = str(row.get("상세") or "").strip()
            response = str(row.get("답변") or "").strip()
            if not title and not response:
                continue
            data["slack"].append({
                "source": file3.name,
                "title": title,
                "description": description,
                "response": response,
            })

    return data


def search_records(query: str, records: List[Dict[str, Any]], top_n: int = 10):
    if not query:
        return []
    query_lower = query.lower()
    scored = []
    for rec in records:
        content = " ".join([rec["title"], rec["description"], rec["response"]]).lower()
        score = content.count(query_lower)
        if query_lower in content:
            scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [rec for _, rec in scored[:top_n]]


def render_results(results, title):
    if results:
        st.subheader(f"검색 결과 ({title}) - {len(results)}건")
        option_labels = [
            f"""[{idx+1}] {rec['title']}
출처: {rec['source']}
원인: {rec['description']}
대응내용: {rec['response'][:50]}..."""
            for idx, rec in enumerate(results)
        ]
        selected = st.radio(f"결과 목록 ({title})", option_labels, index=0, key=f"result_radio_{title}")
        sel_idx = option_labels.index(selected)
        rec = results[sel_idx]

        st.markdown("### 파트너사 전달 문구")
        st.code(rec["response"], language="text")
        st.button("복사하기", on_click=lambda: st.session_state.update({f"copied_{title}": True}))
        if st.session_state.get(f"copied_{title}"):
            st.success("복사되었습니다! (Ctrl+C / Command+C)")


def main():
    st.title("파트너 대응 검색 봇")
    st.markdown(
        """**사용 방법**  
    1. 검색어를 입력합니다.  
    2. 기존 데이터와 메카닉 응답 데이터가 분리되어 검색됩니다.  
    3. 각각의 결과에서 항목을 선택하면 전달 문장이 생성됩니다.  
    """
    )

    all_data = load_data()
    query = st.text_input("검색어를 입력하세요", placeholder="예: E0, 배터리, DP 해제 ...")

    if query:
        regular_results = search_records(query, all_data["regular"])
        slack_results = search_records(query, all_data["slack"])

        if regular_results:
            render_results(regular_results, "기존 자료")
        if slack_results:
            render_results(slack_results, "메카닉 응답")

        if not regular_results and not slack_results:
            st.warning("검색 결과가 없습니다. 다른 키워드를 입력해보세요.")


if __name__ == "__main__":
    main()