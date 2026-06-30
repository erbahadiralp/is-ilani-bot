"""
scrapers/__init__.py
"""
from .kariyer import KariyerScraper
from .jobspy_scraper import JobSpyScraper
from .company_scraper import CompanyScraper

__all__ = ["KariyerScraper", "JobSpyScraper", "CompanyScraper"]
