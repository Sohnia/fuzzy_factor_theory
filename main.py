#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:Zgc
# datetime:2020/4/7 14:41
# software: PyCharm
from decimal import Decimal

import numpy as np

class Ruler:
    def __init__(self, facts, target, prob):
        self.facts = facts
        self.target = target
        self.prob = prob.replace('\n', '')


class ComputeElement():
    def __init__(self, sub_probs, ele_probs, type):
        self.type = type
        self.subs_probs = sub_probs # 子节点的概率
        self.ele_probs = ele_probs # 节点的概率

    def compute(self):
        if self.type == "AND":
            self.type = ComputeElement.compute_and
        elif self.type == 'OR':
            self.type = ComputeElement.compute_or
        else:
            self.type = ComputeElement.mutil_compute_mix
        tmp = np.array(self.subs_probs) * np.array(self.ele_probs)
        return self.type(*self.subs_probs) * self.ele_probs \
            if type(self.ele_probs) != list else self.type(*tmp)

    @staticmethod
    def compute_and(a, b):
        return b if a > b else a

    @staticmethod
    def compute_or(a, b):
        return a if a > b else b

    @staticmethod
    def mutil_compute_mix(*m):
        tmp = ComputeElement.compute_mix(m[0],m[1])
        for index, ele in enumerate(list(m)):
            if index < 2:
                continue
            else:
                tmp = ComputeElement.compute_mix(tmp, ele)
        return tmp

    @staticmethod
    def compute_mix(a, b):
        if a >= 0 and b >= 0:
            return a + b - a * b
        elif a <= 0 and b <= 0:
            return a + b + a * b
        elif a * b == -1.0:
            return 0.0
        else:
            return (a + b) / (1 - min(abs(a), abs(b)))


class Fuzzy:
    def __init__(self, file_path):
        self.file_path = file_path
        self.rulers = self._parser()
        self.count_customize = 0

    def _parser(self):
        f = open(self.file_path, 'r', encoding='utf-8')
        rulers = []
        for line in f.readlines():
            ruler_text, prob = line.split('\t')
            # print(prob, ruler_text)
            if ruler_text.__contains__(' -> '):
                facts, target = ruler_text.split(' -> ')
                ruler = Ruler(facts, target, prob)
            else:
                ruler = Ruler(ruler_text, "", prob)
            rulers.append(ruler)
        return rulers

    def _deal_node(self):
        # 对节点的进行整理
        tmp_rulers = self.rulers
        self.single_nodes = {}
        for ruler in tmp_rulers:
            if ruler.target == "":
                # 单节点的概率
                self.single_nodes[ruler.facts] = float(ruler.prob)
        for ruler in tmp_rulers:
            if ruler.target == "":
                continue
            elif ruler.facts.__contains__('AND') or ruler.facts.__contains__('OR'):
                res = self._split_facts(ruler.facts)
                if len(res) == 2:
                    self.single_nodes[ruler.target] = [res[0], res[1], float(ruler.prob)]  # 含有的元素以及操作方式
                else:
                    new_node = 'nomame' + str(self.count_customize)
                    self.count_customize += 1
                    self.single_nodes[ruler.target] = [[res[0], new_node], res[1], float(ruler.prob)]
                    self.single_nodes[new_node] = [res[2][0], res[2][1], 1]  # 递归后的返回值和操作方式
            else:
                subs, subs_probs = self._get_mix_sub(ruler.target, tmp_rulers)
                self.single_nodes[ruler.target] = [subs, 'MIX', subs_probs]

    def _get_mix_sub(self, target, rulers):
        mix_sub = []
        sub_probs = []
        for ruler in rulers:
            if ruler.target == target:
                mix_sub.append(ruler.facts)
                sub_probs.append(float(ruler.prob))
        return mix_sub, sub_probs

    def _split_facts(self, facts):
        index_bra = facts.find('(')
        if index_bra == -1:  # 说明不含有括号，只有两个元素
            if facts.find(' AND ') != -1:
                return facts.split(' AND '), 'AND'
            else:
                return facts.split(' OR '), 'OR'
        else:
            tmp_facts = facts.replace(')', '')
            single, two = tmp_facts.split('(')
            if single.find(' AND '):
                return single.replace(' AND ', ''), 'AND', self._split_facts(two)
            else:
                return single.replace(' OR ', ''), 'OR', self._split_facts(two)

    def _check_node(self, subs_node):
        res = []
        for node in subs_node:
            tmp = self.single_nodes[node]
            if type(tmp) == list:
                return 0
            else:
                res.append(tmp)
        return res

    def get_res(self):
        self._deal_node()
        keys = list(self.single_nodes.keys())
        res_key = ''
        last_len = 0
        while keys:
            if len(keys) == 1: res_key = keys[0]  # 最终节点的结果
            for key in keys:
                tmp = self.single_nodes[key]
                if not type(tmp) == list:
                    keys.remove(key)  # 已经计算过了，就不需要再次计算了
                else:
                    subs_node, compute_type, ele_probs = tmp
                    cur_probs = self._check_node(subs_node)
                    if not cur_probs:
                        continue  # 这个节点还不能计算，因为里面有的节点还没有计算出来
                    else:
                        self.single_nodes[key] = ComputeElement(cur_probs, ele_probs,
                            compute_type).compute()
                        keys.remove(key)
            last_len = len(keys)
        return res_key, self.single_nodes[res_key]

if __name__ == '__main__':
    file_path = 'ruler.txt'
    f = Fuzzy(file_path)
    f._deal_node()
    nodes = f.single_nodes
    print(f.get_res())
