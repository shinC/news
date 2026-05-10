import pandas as pd
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)

def analyze_and_sort(news_data: List[Dict[str, Any]], similarity_threshold: float = 0.4) -> List[Dict[str, Any]]:
    """
    수집된 뉴스 데이터를 기반으로 유사도 검사를 수행하여 중복 기사를 클러스터링하고,
    시간순 및 클러스터 크기(중복도)순으로 정렬합니다.
    """
    if not news_data:
        logger.warning("분석할 뉴스 데이터가 없습니다.")
        return []

    df = pd.DataFrame(news_data)
    
    # 1. TF-IDF를 이용한 텍스트 벡터화
    # 제목과 요약본을 합쳐서 유사도 비교에 사용
    df['combined_text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('')
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    except Exception as e:
        logger.error(f"유사도 분석 중 오류 발생: {e}")
        df['cluster_size'] = 1
        return df.to_dict('records')

    # 2. 클러스터링 (간단한 Greedy 알고리즘 적용)
    n_samples = len(df)
    visited = set()
    clusters = []
    
    for i in range(n_samples):
        if i in visited:
            continue
        
        # 임계값 이상의 유사도를 가진 기사들의 인덱스를 찾음
        similar_indices = np.where(cosine_sim[i] >= similarity_threshold)[0]
        
        # 아직 방문하지 않은 인덱스만 클러스터에 포함
        cluster = [idx for idx in similar_indices if idx not in visited]
        if cluster:
            clusters.append(cluster)
            visited.update(cluster)
            
    # 클러스터 크기를 각 행에 저장
    cluster_size_map = {}
    cluster_id_map = {}
    for c_id, cluster in enumerate(clusters):
        size = len(cluster)
        for idx in cluster:
            cluster_size_map[idx] = size
            cluster_id_map[idx] = c_id
            
    df['cluster_size'] = df.index.map(cluster_size_map)
    df['cluster_id'] = df.index.map(cluster_id_map)
    
    # 정렬 수행
    # publish_date가 None인 경우를 처리하기 위해 과거 시간으로 채움
    df['publish_date'] = pd.to_datetime(df['publish_date'], utc=True, errors='coerce')
    
    # 정렬 기준 1: 키워드 가중치 (내림차순)
    # 정렬 기준 2: 시간순 (내림차순, 최신 우선)
    # 정렬 기준 3: 중복도 (클러스터 크기, 내림차순, 많이 다뤄진 이슈 우선)
    df = df.sort_values(by=['priority_score', 'publish_date', 'cluster_size'], ascending=[False, False, False])
    
    logger.info(f"총 {len(clusters)}개의 이슈 클러스터가 형성되었습니다.")
    
    # 클러스터별 대표 기사만 남길지, 아니면 전체를 보여줄지는 선택
    # 여기서는 모두 보여주되 정렬만 수행
    return df.to_dict('records')
