"""Nom d'ouverture à deux niveaux (famille / variante) depuis ECOUrl ou ECO."""
import re

# Mot qui clôt le nom de famille : "Sicilian Defense", "Italian Game", "London System"...
FAMILY_END = {"Opening", "Defense", "Game", "Gambit", "Countergambit", "Attack", "System"}

# Les slugs chess.com perdent les apostrophes.
POSSESSIVES = {
    "Queens": "Queen's", "Kings": "King's", "Bishops": "Bishop's", "Alekhines": "Alekhine's",
    "Petrovs": "Petrov's", "Owens": "Owen's", "Birds": "Bird's", "Larsens": "Larsen's",
    "Philidors": "Philidor's", "Ponzianis": "Ponziani's", "Petroffs": "Petroff's",
}


def _slug_tokens(eco_url):
    slug = eco_url.rstrip("/").rsplit("/", 1)[-1]
    tokens = []
    for tok in slug.split("-"):
        # la suite de coups ("3.Nc3", "2...e6") marque la fin du nom
        if re.match(r"^\d", tok) or "..." in tok or "." in tok:
            break
        if tok:
            tokens.append(POSSESSIVES.get(tok, tok))
    # "Modern-Defense-with-1-e4" : on retire les mots de liaison orphelins en fin de nom
    while tokens and tokens[-1] in {"with", "and", "without"}:
        tokens.pop()
    return tokens


def split_opening(eco_url, eco):
    """Retourne (famille, variante)."""
    tokens = _slug_tokens(eco_url) if eco_url else []
    if not tokens:
        return (f"ECO {eco}" if eco else "Inconnue"), ""
    for i, tok in enumerate(tokens):
        if tok in FAMILY_END:
            family, rest = tokens[: i + 1], tokens[i + 1:]
            break
    else:
        family, rest = tokens, []
    return " ".join(family), " ".join(rest)
