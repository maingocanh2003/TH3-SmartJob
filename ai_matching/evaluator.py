"""
Evaluation Framework for SmartJob AI Recommendation System
Calculates IR & Recommender Metrics:
- Precision@K (K = 1, 3, 5, 10)
- Recall@K (K = 1, 3, 5, 10)
- NDCG@K (K = 1, 3, 5, 10)
- Mean Reciprocal Rank (MRR)
- Mean Average Precision (MAP)
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .ranking import rank_jobs_for_candidate


DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_CVS_FILE = DATA_DIR / "sample_cvs.json"
DEFAULT_JOBS_FILE = DATA_DIR / "sample_jobs.json"
DEFAULT_BENCHMARK_FILE = DATA_DIR / "ground_truth_relevance.json"


def dcg_at_k(relevances: List[int], k: int) -> float:
    """Calculate Discounted Cumulative Gain at rank K."""
    relevances = relevances[:k]
    score = 0.0
    for i, rel in enumerate(relevances):
        # 2^rel - 1 formulation rewards highly relevant items more strongly
        gain = (2.0 ** rel) - 1.0
        discount = math.log2(i + 2.0)  # log2(rank + 1), i starts at 0 -> i + 2
        score += gain / discount
    return score


def ndcg_at_k(actual_relevances: List[int], ideal_relevances: List[int], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain at rank K."""
    idcg = dcg_at_k(ideal_relevances, k)
    if idcg <= 0.0:
        return 1.0 if not any(actual_relevances[:k]) else 0.0
    dcg = dcg_at_k(actual_relevances, k)
    return min(1.0, max(0.0, dcg / idcg))


class RecommendationEvaluator:
    """
    Evaluates AI matching recommendations against a labeled ground-truth benchmark.
    """

    def __init__(
        self,
        cvs_path: Optional[Path] = None,
        jobs_path: Optional[Path] = None,
        benchmark_path: Optional[Path] = None
    ):
        self.cvs_path = cvs_path or DEFAULT_CVS_FILE
        self.jobs_path = jobs_path or DEFAULT_JOBS_FILE
        self.benchmark_path = benchmark_path or DEFAULT_BENCHMARK_FILE

        self.cvs: List[Dict[str, Any]] = []
        self.jobs: List[Dict[str, Any]] = []
        self.benchmark: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self):
        if self.cvs_path.exists():
            with open(self.cvs_path, 'r', encoding='utf-8') as f:
                self.cvs = json.load(f)
        if self.jobs_path.exists():
            with open(self.jobs_path, 'r', encoding='utf-8') as f:
                self.jobs = json.load(f)
        if self.benchmark_path.exists():
            with open(self.benchmark_path, 'r', encoding='utf-8') as f:
                self.benchmark = json.load(f)

    def evaluate(
        self,
        k_values: Tuple[int, ...] = (1, 3, 5, 10),
        relevance_threshold: int = 2
    ) -> Dict[str, Any]:
        """
        Run macro-evaluation over all candidates in benchmark.
        A job is considered 'relevant' if ground truth score >= relevance_threshold (e.g. 2).
        """
        judgments = self.benchmark.get('judgments', {})
        if not judgments or not self.cvs or not self.jobs:
            return {'error': 'Dữ liệu benchmark hoặc CV/Job không đầy đủ'}

        candidate_map = {str(c['candidate_id']): c for c in self.cvs}
        
        per_query_results = []
        macro_metrics = {f'precision@{k}': [] for k in k_values}
        macro_metrics.update({f'recall@{k}': [] for k in k_values})
        macro_metrics.update({f'ndcg@{k}': [] for k in k_values})
        mrr_list = []
        map_list = []

        for cand_id_str, cand_benchmark in judgments.items():
            if cand_id_str not in candidate_map:
                continue

            cand_data = candidate_map[cand_id_str]
            ratings = cand_benchmark.get('ratings', {})
            
            # Ground truth relevance mapping
            # All items with rating >= relevance_threshold are relevant
            total_relevant_count = sum(1 for r in ratings.values() if r >= relevance_threshold)
            ideal_sorted_ratings = sorted(list(ratings.values()), reverse=True)

            # Get AI Recommendations (top 15)
            ranked_jobs = rank_jobs_for_candidate(cand_data, self.jobs, limit=15)
            
            # Extract ranked job IDs and their true relevance scores
            actual_relevances = []
            retrieved_job_ids = []
            for item in ranked_jobs:
                jid = str(item['job_id'])
                retrieved_job_ids.append(item['job_id'])
                true_rel = ratings.get(jid, 0)
                actual_relevances.append(true_rel)

            query_metrics = {
                'candidate_id': int(cand_id_str),
                'candidate_name': cand_benchmark.get('candidate_name', cand_data.get('full_name')),
                'target_role': cand_benchmark.get('target_role', cand_data.get('desired_position')),
                'total_relevant_items': total_relevant_count,
                'top_recommendations': [
                    {
                        'job_id': item['job_id'],
                        'job_title': item['job_title'],
                        'matching_score': item['matching_score'],
                        'true_relevance': ratings.get(str(item['job_id']), 0)
                    }
                    for item in ranked_jobs[:5]
                ]
            }

            # 1. Precision@K, Recall@K, NDCG@K
            for k in k_values:
                top_k_rels = actual_relevances[:k]
                relevant_retrieved = sum(1 for r in top_k_rels if r >= relevance_threshold)

                # Precision@K
                p_k = relevant_retrieved / k
                macro_metrics[f'precision@{k}'].append(p_k)
                query_metrics[f'precision@{k}'] = round(p_k, 4)

                # Recall@K
                r_k = (relevant_retrieved / total_relevant_count) if total_relevant_count > 0 else 1.0
                macro_metrics[f'recall@{k}'].append(r_k)
                query_metrics[f'recall@{k}'] = round(r_k, 4)

                # NDCG@K
                ndcg = ndcg_at_k(actual_relevances, ideal_sorted_ratings, k)
                macro_metrics[f'ndcg@{k}'].append(ndcg)
                query_metrics[f'ndcg@{k}'] = round(ndcg, 4)

            # 2. Reciprocal Rank (RR)
            first_rel_rank = next((idx + 1 for idx, r in enumerate(actual_relevances) if r >= relevance_threshold), None)
            rr = (1.0 / first_rel_rank) if first_rel_rank else 0.0
            mrr_list.append(rr)
            query_metrics['mrr'] = round(rr, 4)

            # 3. Average Precision (AP)
            cum_hits = 0
            sum_prec = 0.0
            for idx, r in enumerate(actual_relevances):
                if r >= relevance_threshold:
                    cum_hits += 1
                    sum_prec += cum_hits / (idx + 1)
            ap = (sum_prec / total_relevant_count) if total_relevant_count > 0 else 0.0
            map_list.append(ap)
            query_metrics['ap'] = round(ap, 4)

            per_query_results.append(query_metrics)

        # Calculate Macro Averages
        summary = {
            'num_queries_evaluated': len(per_query_results),
            'total_jobs_in_pool': len(self.jobs),
            'metrics': {
                k: round(sum(vals) / len(vals), 4) if vals else 0.0
                for k, vals in macro_metrics.items()
            },
            'mrr': round(sum(mrr_list) / len(mrr_list), 4) if mrr_list else 0.0,
            'map': round(sum(map_list) / len(map_list), 4) if map_list else 0.0,
            'details': per_query_results
        }

        return summary


_evaluator = RecommendationEvaluator()


def run_recommendation_evaluation(
    k_values: Tuple[int, ...] = (1, 3, 5, 10),
    relevance_threshold: int = 2
) -> Dict[str, Any]:
    return _evaluator.evaluate(k_values, relevance_threshold)

