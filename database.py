# -*- coding: utf-8 -*-

import struct
import gzip

from othello import Board

def _move_to_str(move):
    player,row,column = move
    if player == Board.BLACK:
        p = '+'
    else:
        p = '-'
    return '{0}{1}{2}'.format(p,chr(ord('a') + column), row+1)


def save_db_as_text(db, output_file):
    with open(output_file, 'w') as f:
        for moves, result in db.games:
            f.write("{0}:{1}\n".format(''.join(map(_move_to_str, moves)), result))

def _byte_to_int(b):
    return struct.unpack('b', b)[0]

class ThorDb(object):
    """WTHOR database format: http://cassio.free.fr/cassio/custom_install/database/FORMAT_WTHOR.TXT
    """
    def __init__(self, database_file=None):
        self.games = []
        self.inconsistencies = 0
        if database_file is not None:
            self.add_file(database_file)

    def add_file(self, file_name):
        self.games.extend(self._read_thor_file(file_name))
        print "inconsistencies = ", self.inconsistencies

    def _read_thor_file(self, file_name):
        file_header_size = 16
        record_header_size = 8
        shots = 60
        record_size = 68

        games = []
        with open(file_name, "rb") as f:
            c = f.read()
            board_size = _byte_to_int(c[12])
            if board_size == 8 or board_size == 0:
                for i in xrange(file_header_size, len(c), record_size):
                    moves = []
                    b = Board()
                    player = Board.BLACK
                    black_score = _byte_to_int(c[i+6])
                    for j in xrange(record_header_size, record_size):
                        play = _byte_to_int(c[i+j])
                        if play > 0:
                            column = (play % 10) -1
                            row = (play // 10) -1
                            if not b.is_feasible(row, column, player):
                                player = Board.opponent(player)
                            moves.append((player, row, column))
                            b.flip(row, column, player)
                            player = Board.opponent(player)

                    score = b.score(Board.BLACK)
                    if b.score(Board.BLACK) > b.score(Board.WHITE):
                        score += b.score(Board.BLANK)
                    if score == black_score:
                        games.append((moves, black_score*2 - 64))
                    else:
                        self.inconsistencies += 1
        return games

class TextDb(object):
    def __init__(self, database_file):
        self.games = []
        if database_file is not None:
            self.add_file(database_file)

    def add_file(self, file_name):
        self.games.extend(self._read_text_file(file_name))

    def _read_text_file(self, file_name):
        games = []
        if file_name.endswith(".gz"):
            f = gzip.open(file_name)
        else:
            f = open(file_name)
        for l in f:
            games.append(self._parse(l))
        f.close()
        return games

    def _parse(self, l):
        moves = []
        tokens = l.strip().split(':')
        steps = len(tokens[0])/3

        for idx in range(0, steps):
            if l[3*idx] == '+':
                player = Board.BLACK
            else:
                player = Board.WHITE
            row = ord(l[3*idx+1]) - ord('a')
            column = int(l[3*idx+2]) - 1
            moves.append((player, row, column))
        result = int(tokens[1])
        return (moves, result)


def validate(db):
    pass

if __name__ == '__main__':
    db = TextDb()
    db.add_file("./database/logbook.txt")
    db.add_file("./database/WTH.txt")
