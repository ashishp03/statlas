"""statlas — a natural-language sports stats engine.

Pipeline (see README):
    question -> entities.resolver -> nlu.parser -> query.planner -> query.executor -> engine.answer

The golden rule of this codebase: the LLM/parser NEVER computes a statistic.
It only turns language into a structured query. DuckDB (the SQL engine) does the math.
"""

__version__ = "0.0.1"
