
ANUSVAARA = 'ANUSVAARA'
VISARGA = 'VISARGA'
ANUNAASIKA =  'ANUNAASIKA'

ACH_HRASVA = 'ACH_HRASVA'
ACH_DEERGHA = 'ACH_DEERGHA'
HAL = 'HAL'

# akshara_suffix = ANUSVAARA | VISARGA
# deergha_an = (ACH_DEERGHA ANUNAASIKA) | (ACH_DEERGHA)
# deergha = (deergha_an) | deergha_an
# hrasva_an = (ACH_HRASVA ANUNAASIKA) | (ACH_HRASVA)
# hrasva = (hrasva_an) | hrasva_an
EOF = 'EOF'

TOKEN_CHARS = {
    'ANUSVAARA': ['M'],
    'VISARGA': ['H'],
    'ANUNAASIKA': ['.N'],
    'ACH_HRASVA': 'a|i|u|RRi|LLi'.split('|'),
    'ACH_DEERGHA': 'A|I|U|RRI|LLI|E|ai|O|au'.split('|'),
    'HAL': 'k|kh|g|gh|~N|c|ch|j|jh|~n|T|Th|D|Dh|N|t|th|d|dh|n|p|ph|b|bh|m|y|r|l|v|sh|Sh|s|h'.split('|'),
}

AKSHARA = (ANUNAASIKA, ANUSVAARA, VISARGA, ACH_HRASVA, ACH_DEERGHA, HAL)

HAL_DEERGHA = 'HAL_DEERGHA'
HAL_HRASVA = 'HAL_HRASVA'

HRASVA_AKSHARA = 'HRASVA_AKSHARA'
DEERGHA_AKSHARA = 'DEERGHA_AKSHARA'

#
# DEERGHA_GURU = (DEERGHA_AKSHARA | (DEERGHA_AKSHARA HAL) | (DEERGHA_AKSHARA akshara_suffix)) [GURU]
# HRASVA_GURU = ((HRASVA_AKSHARA HAL) | (HRASVA_AKSHARA akshara_suffix)) [GURU]
# LAGHU = HRASVA_AKSHARA

# HRASVA_GANA = HRASVA_GURU [GURU] | LAGHU [LAGHU]
# GANA = DEERGHA_GURU [GURU] | HRASVA_GANA [LAGHU]
# LINE = GANA*

# YA = LAGHU GURU GURU
# RA = GURU LAGHU GURU
# TA = GURU GURU LAGHU
# BHA = GURU LAGHU LAGHU
# JA  = LAGHU GURU LAGHU
# SA  = LAGHU LAGHU GURU
# MA = GURU GURU GURU
# NA = LAGHU LAGHU LAGHU

class Token(object):
    def __init__(self, type, value, pos):
        self.type = type
        self.value = value
        self.position = pos

    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS '+')
        """
        return 'Token({type}, {value}, {pos})'.format(
            type=self.type,
            value=repr(self.value),
            pos=self.position
        )

    def __repr__(self):
        return self.__str__()

class LexException(Exception):
    pass

class Lexer(object):
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]
        self.pending_token = None

    def error(self):
        raise LexException('Error lexing input "%s" at position %s'%(self.current_char, self.pos), self.pos, self.current_char)

    def advance(self, num=1):
        """Advance the `pos` pointer and set the `current_char` variable."""
        self.pos += num
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def _internal_next_token(self):
        text = self.text
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            val = None
            if len(text) >= self.pos+3:
                if self.current_char == 'R' and text[self.pos+1:self.pos+3] in ('Ri', 'RI'):
                    # RRi, RRI
                    val = text[self.pos:self.pos+3]
                elif self.current_char == 'L' and text[self.pos+1:self.pos+3] in ('Li', 'LI'):
                    # LLi, LLI
                    val = text[self.pos:self.pos+3]

            if (val is None) and (len(text) >= self.pos+2):
                if self.current_char == 'a' and text[self.pos+1] in ('iu'):
                    # ai, au
                    val = text[self.pos:self.pos+2]
                elif self.current_char in ('kgcjTDtdpbsS') and text[self.pos+1] == 'h':
                    # check if followed by h
                    val = text[self.pos:self.pos+2]
                elif self.current_char == '.' and text[self.pos+1] == 'N':
                    # .N
                    val = text[self.pos:self.pos+2]
                elif self.current_char == '~' and text[self.pos+1] in 'nN':
                    # ~N, ~n
                    val = text[self.pos:self.pos+2]

            if val is None:
                val = self.current_char

            for t in AKSHARA:
                if val in TOKEN_CHARS[t]:
                    p = self.pos
                    self.advance(len(val))
                    return Token(t, val, p)

            self.error()

        return Token(EOF, None, self.pos)

    def get_next_token(self):
        if self.pending_token is not None:
            tok = self.pending_token
            self.pending_token = None
        else:
            tok = self._internal_next_token()

        if tok.type == HAL:
            tok2 = self._internal_next_token()
            if tok2.type == ACH_HRASVA:
                return Token(HRASVA_AKSHARA, tok.value+tok2.value, tok.position)
            elif tok2.type == ACH_DEERGHA:
                return Token(DEERGHA_AKSHARA, tok.value+tok2.value, tok.position)
            # remember tok2
            self.pending_token = tok2
            return tok
        elif tok.type == ACH_HRASVA:
            return Token(HRASVA_AKSHARA, tok.value, tok.position)
        elif tok.type == ACH_DEERGHA:
            return Token(DEERGHA_AKSHARA, tok.value, tok.position)

        return tok

class ParseException(Exception):
    pass

class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.nodeVal = ''

    def error(self):
        raise ParseException('Error parsing token %s'%self.current_token, self.current_token)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def anunaasika(self):
        tok = self.current_token
        self.eat(ANUNAASIKA)
        self.nodeVal += tok.value

    def deergha_akshara(self):
        tok = self.current_token
        self.eat(DEERGHA_AKSHARA)
        self.nodeVal += tok.value

    def hrasva_akshara(self):
        tok = self.current_token
        self.eat(HRASVA_AKSHARA)
        self.nodeVal += tok.value

    def akshara_suffix(self):
        """akshara_suffix = ANUSVAARA | VISARGA"""
        tok = self.current_token
        if self.current_token.type == ANUSVAARA:
            self.eat(ANUSVAARA)
            self.nodeVal += tok.value
        elif self.current_token.type == VISARGA:
            self.eat(VISARGA)
            self.nodeVal += tok.value
        else:
            self.error()

    def suffix_hal(self):
        tok = self.current_token
        self.eat(HAL)
        self.nodeVal += tok.value

    def deergha_guru(self):
        self.deergha_akshara()

        if self.current_token.type == ANUNAASIKA:
            self.anunaasika()

        if self.current_token.type in (ANUSVAARA, VISARGA):
            self.akshara_suffix()
        elif self.current_token.type == HAL:
            self.suffix_hal()

        out = ('GURU(%s)'%(self.nodeVal))
        self.nodeVal = ''
        return out

    def hrasva_guru(self):
        self.hrasva_akshara()

        if self.current_token.type == ANUNAASIKA:
            self.anunaasika()

        if self.current_token.type in (ANUSVAARA, VISARGA):
            self.akshara_suffix()
        elif self.current_token.type == HAL:
            self.suffix_hal()

        out = ('GURU(%s)'%(self.nodeVal))
        self.nodeVal = ''
        return out

    def hrasva_gana(self):
        self.hrasva_akshara()

        if self.current_token.type == ANUNAASIKA:
            self.anunaasika()

        out = None
        if self.current_token.type in (ANUSVAARA, VISARGA):
            self.akshara_suffix()
            out = 'GURU(%s)'
        elif self.current_token.type == HAL:
            self.suffix_hal()
            out = 'GURU(%s)'
        else:
            out = 'LAGHU(%s)'

        if not out:
            self.error()

        ret = out%self.nodeVal
        self.nodeVal = ''

        return ret

    def prefixHal(self):
        tok = self.current_token
        self.eat(HAL)
        self.nodeVal += tok.value

    def detectGana(self):
        """
        Use for detecting
        :return:
        """
        while self.current_token.type == HAL:
            self.prefixHal()

        if self.current_token.type == DEERGHA_AKSHARA:
            return self.deergha_guru()
        elif self.current_token.type == HRASVA_AKSHARA:
            return self.hrasva_gana()

        self.error()

    def guru(self):
        """
        Use only for verifying
        :return:
        """
        while self.current_token.type == HAL:
            self.prefixHal()

        if self.current_token.type == DEERGHA_AKSHARA:
            return self.deergha_guru()
        elif self.current_token.type == HRASVA_AKSHARA:
            return self.hrasva_guru()

        self.error()

    def laghu(self):
        """
        Use only for verifying
        :return:
        """
        while self.current_token.type == HAL:
            self.prefixHal()
        self.hrasva_akshara()

        if self.current_token.type == HAL:
            self.error()

        ret = 'LAGHU(%s)'%self.nodeVal
        self.nodeVal = ''

        return ret

    def parse(self, pattern=None):
        ganas = []
        gana_methods = {
            'L':self.laghu, 'G':self.guru
        }
        if pattern:
            pattern = pattern.upper()
            for g in pattern:
                ganas.append(gana_methods[g]())
            if self.current_token.type != EOF:
                self.error()
        else:
            while self.current_token.type != EOF:
                ganas.append(self.detectGana())

        return ganas

def testLexer(text):
    lex = Lexer(text)
    while True:
        token = lex.get_next_token()
        print(token)
        if token.type == 'EOF':
            break

def detectGanas(text, pattern=None):
    """
    Detect the ganas in `text` if no `pattern` is specified.
    Check if the `text` matches the gana pattern specified in `pattern`.
    
    `text` -- a string with sanskrit text in ITRANS transliteration format.
    `pattern` -- a string the characters 'L' and 'G'.
                 Eg:- 'GGLGGLLGLGGL' is the pattern for indra vajra meter
    """
    lex = Lexer(text)
    p = Parser(lex)
    # print('======'+text+'======')
    try:
        ganas = p.parse(pattern=pattern)
        print(ganas)
        if pattern:
            print('Matched')
    except LexException as le:
        msg, pos, char = le.args
        print(text)
        print(' '*(pos-1), '^')
        print(msg)
    except ParseException as pe:
        msg, token = pe.args
        print(text)
        print(' '*(token.position-1), '^')
        print(msg)

def main():
    print('===============================')
    print('SANSKRIT CHANDAS GANA DETECTION')
    print('===============================')
    print('\nThe program runs in two modes:')
    print('1. Print gana pattern of verses')
    print('2. Check if a verse matches a given gana pattern')
    mode = int(input('Enter choice>'))
    pattern = None
    if mode == 2:
        while not pattern:
            print('A gana pattern is specified as a string of L and G characters')
            print('L for Laghu(short); G for Guru(long)')
            print('''Eg:- 'GGLGGLLGLGG' is the pattern for the indra vajra meter''')
            pattern = input('Enter pattern to detect (Eg. LGGLLGLG)>')
            pattern = pattern.upper()
            pchars = ''.join(sorted(set(pattern)))
            if pchars != 'GL':
                pattern = None
                print('Invalid spec for gana pattern')
    while True:
        text = input('Enter sanskrit text in ITRANS format (q to exit)>\n')
        if text in 'qQ':
            break
        detectGanas(text, pattern=pattern)

if __name__ == '__main__':
    main()
    # print('OmaruNAcala')
    # testLexer('OmaruNAcala')
    # print('Om na mO bha ga va tE shrI ra ma NA ya')
    # testLexer('OmnamObhagavatEshrIramaNAyabhOH')
    #
    # # testLexer('syAdindravajrAyadidaujagaugaH')
    #
    # # testLexer('yaMvaidikAmantradRRishaHpurANAH')
    #
    # # testLexer('upEndravajrAjatajAstatOgau')
    #
    # # testLexer('yaMvaidikAmantradRRishaHpurANAH')
    #
    # # testLexer('indraMyamaMmAtarishvAnamAhuH')
    #
    # # testLexer('vEdAntinOnirvacanIyamEkaM')
    #
    # # testLexer('yaMbrahmashabdEnavinirdishanti')
    #
    # # testLexer('shaivAyamIshaMshiva ityavOcan')
    #
    # # testLexer('yaMvaiShNavAviShNuritistuvanti')
    #
    #
    # # testLexer('OmbhUrbhuvassuvaHtatsaviturvarENyambhargOdEvasyadhImahIdhiyOyOnaHpracOdayAt')

    # testLexer('yaMvaidikAmantradRRishaHpurANAH')
    # detectGanas('yaMvaidikAmantradRRishaHpurANAHa', 'GGLGGLLGLGGL')

    # testLexer('indraMyamaMmAtarishvAnamAhuH')
    # detectGanas('indraMyamaMmAtarishvAnamAhuH', 'GGLGGLLGLGG')
    
