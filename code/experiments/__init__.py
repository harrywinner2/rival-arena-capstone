"""Experiment drivers for the protected MPU spine (A5, A1, B1) and beyond.

Each driver builds a list of MatchSpecs (the factor cells x seeds), runs them via
the harness with bounded concurrency, attaches metrics, and writes the
definition-of-done artifacts. Exploratory vs confirmatory is a *labeling* concern
(see prereg/) — the same driver runs both; only the analysis spec differs.
"""
