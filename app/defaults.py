"""Alapértelmezett hírlevél-források (bővíthető az adatbázisban / UI-n)."""

from __future__ import annotations

# Megjelenített név = a < előtti rész; email = technikai kulcs
DEFAULT_SOURCES: list[dict[str, str]] = [
    {"name": "Amazing AI", "email": "iroda@amazingai.hu"},
    {"name": "Csont Attila | businessup.hu", "email": "hello@csontattila.hu"},
    {"name": "Bártfai Balázs", "email": "hello@salesform.hu"},
    {"name": "Molnár Erika - EkkaPixels", "email": "hello@ekkapixels.hu"},
    {"name": "Gerilla Önéletrajz", "email": "barathandras@gerillaoneletrajz.hu"},
    {"name": "Domán Zsolt", "email": "hello@domarketing.hu"},
    {"name": "Pekáry Dorottya", "email": "info@ferficoaching.hu"},
    {"name": "Pikrea", "email": "ugyfelszolgalat@pikrea.hu"},
    {"name": "Knapek Éva", "email": "info@knapekeva.hu"},
]
