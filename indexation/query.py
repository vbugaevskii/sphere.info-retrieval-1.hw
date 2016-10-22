# -*- coding: utf-8 -*

import re


class Query:
    def __init__(self, index=None, term=None):
        """
        Every query can be represented as union of two lists: X and I_X
        READ LIKE THAT: docs in X or NOT in I_X

        self.query = X
        self.exclude = I_X

        P.S. self.exclude = None ~ self.exclude = list_of_all_docs

        :param index: reverse index
        :param term:  interested term
        """
        if index is not None:
            self.query = index[term]
            self.exclude = None

    @staticmethod
    def __cross_target_and_target(x1, x2):
        res = []
        i, j = 0, 0

        while i < len(x1) and j < len(x2):
            if x1[i] == x2[j]:
                res.append(x1[i])
                i += 1
                j += 1
            elif x1[i] > x2[j]:
                j += 1
            elif x1[i] < x2[j]:
                i += 1

        return res

    @staticmethod
    def __exclude_from_target(x_target, x_exclude):
        if x_exclude is None:
            return []

        res = []
        i, j = 0, 0

        while i < len(x_target) and j < len(x_exclude):
            if x_target[i] == x_exclude[j]:
                i += 1
                j += 1
            elif x_target[i] > x_exclude[j]:
                j += 1
            elif x_target[i] < x_exclude[j]:
                res.append(x_target[i])
                i += 1

        if i < len(x_target):
            res.extend(x_target[i:])

        return res

    @staticmethod
    def __merge_target_and_target(x1, x2):
        if len(x1) == 0:
            return x2
        elif len(x2) == 0:
            return x1

        res = []
        i, j = 0, 0

        while i < len(x1) and j < len(x2):
            if x1[i] <= x2[j]:
                if len(res) == 0 or x1[i] != res[-1]:
                    res.append(x1[i])
                i += 1
            else:
                if len(res) == 0 or x2[j] != res[-1]:
                    res.append(x2[j])
                j += 1

        if i < len(x1):
            res.extend([x for x in x1[i:] if x > res[-1]])

        if j < len(x2):
            res.extend([x for x in x2[i:] if x > res[-1]])

        return res

    def get_query_urls(self, n_urls_all):
        if self.exclude is None:
            return self.query
        else:
            return Query.__merge_target_and_target(
                self.query,
                Query.__exclude_from_target(range(n_urls_all), self.exclude)
            )

    def __and__(self, other):
        """
        Z | !I_Z = (X | !I_X) & (Y | !I_Y) = X & Y | X & !I_Y | Y & !I_X | !I_X & !I_Y

        READ LIKE THAT:
            (docs in X and in Y) OR
            (docs in X and NOT in I_Y) OR
            (docs in Y and NOT in I_X) OR
            (docs NOT in I_X and NOT in I_Y)

        Z = X & Y | X & !I_Y | Y & !I_X
        !I_Z = !I_X & !I_Y = !(I_X | I_Y)

        :param other: other query   ~ Y | !I_Y
        :return: new query          ~ Z | !I_Z
        """
        res = Query()
        query1 = Query.__cross_target_and_target(self.query, other.query)
        query2 = Query.__exclude_from_target(self.query, other.exclude)
        query3 = Query.__exclude_from_target(other.query, self.exclude)
        
        res.query = Query.__merge_target_and_target(query1, Query.__merge_target_and_target(query2, query3))

        if self.exclude is None or other.exclude is None:
            res.exclude = None
        else:
            res.exclude = Query.__merge_target_and_target(self.exclude, other.exclude)
        return res

    def __or__(self, other):
        """
        Z | !I_Z = (X | !I_X) | (Y | !I_Y) = (X | Y) | (!I_X | !I_Y) = (X | Y) | !(I_X & I_Y)

        READ LIKE THAT:
            (docs in X or in Y) OR (docs NOT in (I_X and I_Y))

        Z = X | Y
        !I_Z = !(I_X & I_Y)

        :param other: other query   ~ Y | !I_Y
        :return: new query          ~ Z | !I_Z
        """
        res = Query()
        res.query = Query.__merge_target_and_target(self.query, other.query)

        if self.exclude is None:
            res.exclude = other.exclude
        elif other.exclude is None:
            res.exclude = self.exclude
        else:
            res.exclude = Query.__cross_target_and_target(self.exclude, other.exclude)
        return res

    def neg(self, n_urls_all):
        """
        Z | !I_Z = !(X | !I_X) = !X & I_X

        :return: new query          ~ Z | !I_Z
        """
        res = Query()
        query = range(n_urls_all) if self.exclude is None else self.exclude
        res.query = Query.__exclude_from_target(query, self.query)
        res.exclude = None
        return res


class QueryParser:
    def __init__(self):
        pass

    @staticmethod
    def is_operator(x):
        if x == '|':
            return True
        elif x == '&':
            return True
        elif x == '!':
            return True
        elif x == '(' or x == ')':
            return True
        else:
            return False

    def parse(self, query):
        query = re.sub(r'\s+', '', query)
        query = re.findall(r"[^&|!()]+|\S", query)
        query = map(lambda x: unicode(x, 'utf-8'), query)
        query = map(lambda x: x.lower(), query)

        self.query = query
        self.stack = []
        self.i = 0

        self.__expr()
        return self.stack

    def __expr(self):
        """
        expr -> exp1 | exp1 or expr
        """
        self.__exp1()
        while self.i < len(self.query) and self.query[self.i] == '|':
            self.i += 1
            self.__expr()
            self.stack.append('|')

    def __exp1(self):
        """
        exp1 -> exp2 | exp2 & exp1
        """
        self.__exp2()
        while self.i < len(self.query) and self.query[self.i] == '&':
            self.i += 1
            self.__exp2()
            self.stack.append('&')

    def __exp2(self):
        """
        exp2 -> exp3 | ! exp3
        """
        flag = self.query[self.i] == '!'
        if flag:
            self.i += 1
        self.__exp3()
        if flag:
            self.stack.append('!')

    def __exp3(self):
        """
        exp3 -> exp4 | (exp4)
        """
        if self.query[self.i] == '(':
            self.i += 1
            self.__expr()
            if self.query[self.i] == ')':
                self.i += 1
        else:
            self.__exp4()

    def __exp4(self):
        """
        exp4 -> term
        """
        if not QueryParser.is_operator(self.query[self.i]):
            self.stack.append(self.query[self.i])
            self.i += 1


class QueryStack:
    def __init__(self, index, n_urls_all):
        self.index = index
        self.n_urls_all = n_urls_all

    def compile(self, query):
        query = QueryParser().parse(query)
        stack = []

        for q in query:
            if q == '&' or q == '|':
                q1 = stack.pop()
                q2 = stack.pop()
                if q == '&':
                    stack.append(q1 & q2)
                else:
                    stack.append(q1 | q2)
            elif q == '!':
                q1 = stack.pop()
                stack.append(q1.neg(self.n_urls_all))
            else:
                stack.append(Query(self.index, q))

        return stack[0]


if __name__ == "__main__":
    parser = QueryParser()

    query = "A & (!B | C) & !D & !(E | F & G) | H"
    print parser.parse(query)
