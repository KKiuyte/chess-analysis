"""Découpage ouverture / milieu de partie / finale."""
import chess

PIECE_VALUES = {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def non_pawn_material(board, color):
    return sum(v * len(board.pieces(p, color)) for p, v in PIECE_VALUES.items())


def phase(board, move_no, opening_moves=12, endgame_material=13):
    """Phase de la position `board`, avant le coup numéro `move_no`."""
    if move_no <= opening_moves:
        return "opening"
    if min(non_pawn_material(board, chess.WHITE),
           non_pawn_material(board, chess.BLACK)) <= endgame_material:
        return "endgame"
    return "middlegame"
