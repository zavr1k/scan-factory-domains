#!/usr/bin/env python3

import sqlite3
from collections import Counter
from statistics import mean

DATABASE_PATH = "./domains.db"


def analyze_domains(domains: list[str]) -> tuple[str, int]:
    """Анализирует спискок доменов и возвращает домен 2-го уровня
    и (среднюю длинну - 1) последующих доменов"""
    base_domains = []
    remaining_domain_lengths = []

    for domain in domains:
        domain_levels = domain.split('.')
        base_domains.append('.'.join(domain_levels[-2:]))
        remaining_domain_lengths.append(len('.'.join(domain_levels[:-2])))

    base_domain_counter = Counter(base_domains)
    base_domain = max(base_domain_counter, key=base_domain_counter.get)

    remaining_domain_length = int(mean(remaining_domain_lengths)) - 1
    return base_domain, remaining_domain_length


def create_regexp(domains: list[str]) -> str:
    base_domain, filter_length = analyze_domains(domains)
    second_lvl_domain, first_lvl_domain = base_domain.split('.')
    return (
        fr"^(?!.*\..*\..*\..*\..*\..*)[a-zA-Z0-9\.-]{{1,{filter_length}}}"
        fr"\.{second_lvl_domain}\.{first_lvl_domain}"
    )


def get_project_domains(cursor: sqlite3.Cursor, project_id: str) -> list[str]:
    query = "SELECT name FROM domains WHERE project_id = ?"
    result = cursor.execute(query, (project_id,)).fetchall()
    return [row[0].strip() for row in result]


def get_project_ids(cursor: sqlite3.Cursor) -> list[str]:
    query = "SELECT DISTINCT project_id FROM domains"
    result = cursor.execute(query).fetchall()
    return [row[0] for row in result]


def insert_project_regexp(cursor: sqlite3.Cursor, project_id: str,
                          regexp: str) -> None:
    query = "INSERT INTO rules (project_id, regexp) VALUES (?, ?)"
    cursor.execute(query, (project_id, regexp))


def main() -> None:
    connect = sqlite3.connect(DATABASE_PATH)
    cursor = connect.cursor()
    try:
        project_id_list = get_project_ids(cursor)
        for project_id in project_id_list:
            project_domains = get_project_domains(cursor, project_id)
            filter_regexp = create_regexp(project_domains)
            insert_project_regexp(cursor, project_id, filter_regexp)
            connect.commit()
    finally:
        cursor.close()
        connect.close()


if __name__ == "__main__":
    main()
