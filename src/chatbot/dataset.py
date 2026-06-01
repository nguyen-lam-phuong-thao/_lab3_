from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

from src.chatbot.models import SearchHit, WorkRecord


STOPWORDS = {
    "la",
    "là",
    "va",
    "và",
    "cho",
    "toi",
    "tôi",
    "mot",
    "một",
    "cac",
    "các",
    "nhung",
    "những",
    "co",
    "có",
    "cua",
    "của",
    "ve",
    "về",
    "hay",
    "hãy",
    "tim",
    "tìm",
    "kiem",
    "kiếm",
    "goi",
    "gợi",
    "y",
    "ý",
    "de",
    "đề",
    "xuat",
    "xuất",
    "recommend",
    "search",
    "summary",
    "tom",
    "tóm",
    "tat",
    "tắt",
    "gioi",
    "giới",
    "thieu",
    "thiệu",
    "sach",
    "book",
    "tac",
    "tác",
    "gia",
    "giả",
    "pham",
    "phẩm",
    "ten",
    "tên",
    "the",
    "thể",
    "loai",
    "loại",
    "khu",
    "vuc",
    "vực",
    "giup",
    "giúp",
    "minh",
    "about",
}

GENRE_ALIASES = {
    "truyen ngan": "truyện ngắn",
    "truyện ngắn": "truyện ngắn",
    "tieu thuyet": "tiểu thuyết",
    "tiểu thuyết": "tiểu thuyết",
    "tho": "thơ",
    "thơ": "thơ",
    "kich": "kịch",
    "kịch": "kịch",
}

REGION_ALIASES = {
    "viet nam": "Việt Nam",
    "việt nam": "Việt Nam",
    "nuoc ngoai": "Nước ngoài",
    "nước ngoài": "Nước ngoài",
    "foreign": "Nước ngoài",
}


def normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    without_d = without_marks.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", without_d).strip()


def tokenize(value: str) -> List[str]:
    return [token for token in normalize_text(value).split() if token and token not in STOPWORDS]


def parse_year_bounds(value: str) -> tuple[Optional[int], Optional[int]]:
    years = [int(match) for match in re.findall(r"\d{4}", value or "")]
    if not years:
        return None, None
    if len(years) == 1:
        return years[0], years[0]
    return years[0], years[-1]


class MetadataRepository:
    def __init__(self, csv_path: str | Path):
        self.csv_path = Path(csv_path)
        self.records = self._load_records()

    def _load_records(self) -> List[WorkRecord]:
        records: List[WorkRecord] = []
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            for row in reader:
                if len(row) < 6:
                    continue
                year_start, year_end = parse_year_bounds(row[2])
                records.append(
                    WorkRecord(
                        author=row[0].strip(),
                        title=row[1].strip(),
                        year_label=row[2].strip(),
                        genre=row[4].strip(),
                        region=row[5].strip(),
                        year_start=year_start,
                        year_end=year_end,
                    )
                )
        return records

    def extract_genre(self, query: str) -> Optional[str]:
        normalized = normalize_text(query)
        for alias, genre in GENRE_ALIASES.items():
            if alias in normalized:
                return genre
        return None

    def extract_region(self, query: str) -> Optional[str]:
        normalized = normalize_text(query)
        for alias, region in REGION_ALIASES.items():
            if alias in normalized:
                return region
        return None

    def extract_year(self, query: str) -> Optional[int]:
        match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", query)
        return int(match.group(1)) if match else None

    def find_title_match(self, query: str) -> Optional[WorkRecord]:
        normalized_query = normalize_text(query)
        title_hits = []
        for record in self.records:
            normalized_title = normalize_text(record.title)
            if normalized_title and normalized_title in normalized_query:
                title_hits.append(record)
        if not title_hits:
            return None
        return sorted(title_hits, key=lambda item: len(item.title), reverse=True)[0]

    def find_author_match(self, query: str) -> Optional[str]:
        normalized_query = normalize_text(query)
        author_hits = []
        for author in {record.author for record in self.records}:
            normalized_author = normalize_text(author)
            if normalized_author and normalized_author in normalized_query:
                author_hits.append(author)
        if not author_hits:
            return None
        return sorted(author_hits, key=len, reverse=True)[0]

    def search(self, query: str, top_k: int = 5) -> List[SearchHit]:
        query_tokens = tokenize(query)
        genre_filter = self.extract_genre(query)
        region_filter = self.extract_region(query)
        year_filter = self.extract_year(query)
        normalized_query = normalize_text(query)
        matched_title = self.find_title_match(query)
        matched_author = self.find_author_match(query)

        hits: List[SearchHit] = []
        for record in self.records:
            title_norm = normalize_text(record.title)
            author_norm = normalize_text(record.author)
            searchable = normalize_text(
                " ".join(
                    [
                        record.title,
                        record.author,
                        record.genre,
                        record.region,
                        record.year_label,
                    ]
                )
            )

            score = 0.0
            if title_norm == normalized_query or author_norm == normalized_query:
                score += 120
            if title_norm in normalized_query:
                score += 70
            if author_norm in normalized_query:
                score += 55

            for token in query_tokens:
                if token in title_norm:
                    score += 14
                if token in author_norm:
                    score += 10
                if token in searchable:
                    score += 4

            if genre_filter and record.genre == genre_filter:
                score += 24
            if region_filter and record.region == region_filter:
                score += 18
            if year_filter and record.year_start and record.year_end:
                if record.year_start <= year_filter <= record.year_end:
                    score += 22

            if score > 0:
                hits.append(SearchHit(record=record, score=score))

        prioritized_hits = self._prioritize_exact_matches(
            hits,
            matched_title=matched_title,
            matched_author=matched_author,
        )
        return sorted(
            prioritized_hits,
            key=lambda hit: (
                -hit.score,
                hit.record.author,
                hit.record.title,
            ),
        )[:top_k]

    def _prioritize_exact_matches(
        self,
        hits: List[SearchHit],
        matched_title: Optional[WorkRecord],
        matched_author: Optional[str],
    ) -> List[SearchHit]:
        if matched_title:
            exact_title_hits = [hit for hit in hits if hit.record.title == matched_title.title]
            if exact_title_hits:
                return exact_title_hits
        if matched_author:
            exact_author_hits = [hit for hit in hits if hit.record.author == matched_author]
            if exact_author_hits:
                return exact_author_hits
        return hits

    def summarize_work(self, record: WorkRecord) -> str:
        same_author = [
            candidate.title
            for candidate in self.records
            if candidate.author == record.author and candidate.title != record.title
        ][:3]
        same_genre_region = [
            candidate.title
            for candidate in self.records
            if candidate.genre == record.genre
            and candidate.region == record.region
            and candidate.title != record.title
        ][:3]

        parts = [
            f'"{record.title}" là một {record.genre} của {record.author}',
            f"được ghi nhận trong tập dữ liệu với mốc sáng tác {record.display_year}",
            f"thuộc nhóm tác phẩm {record.region.lower()}",
        ]

        if same_author:
            parts.append(f"Cùng tác giả còn có: {', '.join(same_author)}")
        if same_genre_region:
            parts.append(
                f"Các tác phẩm gần nhất theo metadata ({record.genre}, {record.region.lower()}): "
                f"{', '.join(same_genre_region)}"
            )
        return ". ".join(parts) + "."

    def summarize_author(self, author: str) -> str:
        works = [record for record in self.records if record.author == author]
        genres = sorted({record.genre for record in works})
        regions = sorted({record.region for record in works})
        earliest = min((record.year_start for record in works if record.year_start is not None), default=None)
        latest = max((record.year_end for record in works if record.year_end is not None), default=None)
        titles = ", ".join(record.title for record in works[:5])

        time_text = "không rõ giai đoạn"
        if earliest and latest:
            time_text = str(earliest) if earliest == latest else f"{earliest}-{latest}"

        return (
            f"{author} xuất hiện {len(works)} lần trong dataset, "
            f"trải trên các thể loại {', '.join(genres)} và khu vực {', '.join(regions)}. "
            f"Giai đoạn sáng tác được ghi nhận: {time_text}. "
            f"Một số tác phẩm tiêu biểu trong bộ dữ liệu: {titles}."
        )

    def recommend_by_record(self, record: WorkRecord, top_k: int = 5) -> List[WorkRecord]:
        candidates = []
        for candidate in self.records:
            if candidate.title == record.title:
                continue

            score = 0
            if candidate.author == record.author:
                score += 100
            if candidate.genre == record.genre:
                score += 35
            if candidate.region == record.region:
                score += 20
            if candidate.year_start and record.year_start:
                score += max(0, 20 - min(abs(candidate.year_start - record.year_start), 20))

            if score > 0:
                candidates.append((score, candidate))

        candidates.sort(key=lambda item: (-item[0], item[1].author, item[1].title))
        return [candidate for _, candidate in candidates[:top_k]]

    def recommend(self, query: str, top_k: int = 5) -> List[WorkRecord]:
        title_match = self.find_title_match(query)
        if title_match:
            return self.recommend_by_record(title_match, top_k=top_k)

        author_match = self.find_author_match(query)
        if author_match:
            author_records = [record for record in self.records if record.author == author_match]
            if author_records:
                seed = author_records[0]
                own_titles = author_records[:top_k]
                if len(own_titles) >= top_k:
                    return own_titles
                extra = [
                    record
                    for record in self.recommend_by_record(seed, top_k=top_k + len(own_titles))
                    if record.author != author_match
                ]
                return (own_titles + extra)[:top_k]

        genre_filter = self.extract_genre(query)
        region_filter = self.extract_region(query)
        year_filter = self.extract_year(query)

        filtered = []
        for record in self.records:
            if genre_filter and record.genre != genre_filter:
                continue
            if region_filter and record.region != region_filter:
                continue
            if year_filter and record.year_start and record.year_end:
                if not (record.year_start <= year_filter <= record.year_end):
                    continue
            filtered.append(record)

        if filtered:
            return filtered[:top_k]

        hits = self.search(query, top_k=top_k)
        if hits:
            return [hit.record for hit in hits]
        return self.records[:top_k]
