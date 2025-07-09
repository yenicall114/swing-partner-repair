import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

st.set_page_config(page_title="파트너 대응 검색 봇", layout="wide")

@st.cache_data
def load_data() -> List[Dict[str, Any]]:
    """엑셀 파일 두 개를 불러와서 레코드(list[dict]) 형태로 결합"""
    records: List[Dict[str, Any]] = []

    # 파일 경로 (앱 디렉터리에 두 개의 xlsx 파일을 함께 배포하세요)
    file1 = Path("(종료)파트너사 대응 답변 예시.xlsx")
    file2 = Path("파트너 대응 메뉴얼_오류코드_.xlsx")

    # 첫 번째 파일 – 단일 시트 가정
    if file1.exists():
        df1 = pd.read_excel(file1)
        for _, row in df1.iterrows():
            title = str(row.get("문제내용") or row.get("발생 문제 구분") or "").strip()
            description = str(row.get("발생문제 항목값") or "").strip()
            response = str(row.get("응대방법") or row.get("해결방안") or "").strip()
            if not title and not response:
                continue
            records.append({
                "source": file1.name,
                "title": title if title else "(제목 없음)",
                "description": description,
                "response": response if response else title,
            })

    # 두 번째 파일 – 여러 시트 순회
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
                records.append({
                    "source": f"{file2.name} ({sheet})",
                    "title": title,
                    "description": description,
                    "response": response if response else description,
                })
    return records


def search_records(query: str, records: List[Dict[str, Any]], top_n: int = 10):
    """아주 단순한 키워드 매칭으로 상위 10개 결과 반환"""
    if not query:
        return []
    query_lower = query.lower()
    scored = []
    for rec in records:
        content = " ".join([rec["title"], rec["description"], rec["response"]]).lower()
        score = content.count(query_lower)  # 빈도 기반 스코어
        if query_lower in content:
            scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)  # 점수 높은 순
    return [rec for _, rec in scored[:top_n]]


def main():
    st.title("🔍 파트너 대응 검색 봇")
    st.markdown(
        """**사용 방법**  
    1. 상단 검색창에 오류 코드나 키워드를 입력합니다.  
    2. 최대 10개의 관련 항목이 리스트로 표시됩니다.  
    3. 항목을 선택하면 파트너사에게 전달할 문장이 생성됩니다.  
    """
    )

    # 데이터 로드
    records = load_data()

    # 검색
    query = st.text_input("검색어를 입력하세요", placeholder="예: E0, 배터리, DP 해제 ...")
    results = search_records(query, records) if query else []

    # 결과 표시 & 선택
    if results:
        st.subheader(f"검색 결과 ({len(results)}건)")
        option_labels = [f"[{idx+1}] {rec['title']} - {rec['description'][:50]}" for idx, rec in enumerate(results)]
        selected = st.radio("결과 목록", option_labels, index=0, key="result_radio")
        sel_idx = option_labels.index(selected)
        rec = results[sel_idx]

        st.markdown("### 파트너사 전달 문구")
        st.code(rec["response"], language="text")
        st.button("복사하기", on_click=lambda: st.session_state.update({"copied": True}))
        if st.session_state.get("copied"):
            st.success("복사되었습니다! (Ctrl+C / Command+C)")

    elif query:
        st.warning("검색 결과가 없습니다. 다른 키워드를 입력해보세요.")


if __name__ == "__main__":
    main()
