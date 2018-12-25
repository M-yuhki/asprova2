#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import fileinput
import operator
from operator import itemgetter, attrgetter

class Order:
    def __init__(self, r, i, e, d, q):
        # オーダ番号    : Order number
        self.r=r
        # 品目番号      : Item number
        self.i=i
        # 最早開始時刻  : Earliest start time
        self.e=e
        # 納期          : Deadline
        self.d=d
        # 製造数量      : Manufacturing quanity
        self.q=q
        # 納期までの時間
        self.lim = d - e
        # このオーダにおける残り工数
        self.prest = -1
        # 既に割り当てた工数分の時間を差し引いた納期
        self.drest = d
        # 直前の工程の段取り時間が確定しているか否か
        self.dflg = True

class Bom:
    def __init__(self, i, p, m, t,c,d):
        # 品目番号             : Item number
        self.i = i
        # 工程番号             : Process number
        self.p = p
        # 設備番号             : Machine number
        self.m = m
        # 1個当たりの製造時間  : Manufacturing time per piece
        self.t = t
        # そのBOMに対応するマシンのcとdの値
        self.c = c
        self.d = d
        # cとdを掛け合わせた評価値
        self.cd = c*d

class Operation:
    def __init__(self, m, r, p, t1, t2, t3, i, order):
        # 設備番号           : Machine number
        self.m = m
        # オーダ番号         : Order number
        self.r = r
        # 工程番号           : Process number
        self.p = p
        # 段取り開始時刻     : Setup start time
        self.t1 = t1
        # 製造開始時刻       : Manufacturing start time
        self.t2 = t2
        # 製造終了時刻      : Manufacturing end time
        self.t3 = t3
        # 品目番号
        self.i = i
        # オーダそのもの
        self.order = order # オーダそのもの

class Asprova2:
    def __init__(self):
        # 設備数                   : Number of machines
        self.M=0
        # 品目数                   : Number of items
        self.I=0
        # 最大工程数               : Max number of processes
        self.P=0
        # 注文数                   : Number of Processes
        self.R=0
        # BOM行数                  : Number of BOM line
        self.BL=0
        # 段取り時間ペナルティ係数 : Setup time penalty
        self.A1=0
        # 納期遅れペナルティ係数   : Missed deadline penalty
        self.A2=0
        # 着手遅延ポイント係数     : Assignment lateness bonus
        self.A3=0
        # 段取り時間べき乗数       : Setup time exponent
        self.B1=0
        # 納期遅れべき乗数         : Missed deadline exponent
        self.B2=0
        # 着手遅延べき乗数         : Late assignment exponent
        self.B3=0
        # 設備mの製造時間係数   : Machine manufacturing time multiplier
        self.C=[]
        # 設備mの段取り時間係数 : Machine setup time multiplier
        self.D=[]
        self.boms = []
        self.orders = []
        self.operations = []

    def readProblem(self):
        n = 0
        for line in fileinput.input():
            split = line.strip().split()
            if n == 0:
                self.M = int(split[1])
                self.I = int(split[2])
                self.P = int(split[3])
                self.R = int(split[4])
                self.BL = int(split[5])
            elif n == 1:
                self.A1 = float(split[1])
                self.A2 = float(split[2])
                self.A3 = float(split[3])
                self.B1 = float(split[4])
                self.B2 = float(split[5])
                self.B3 = float(split[6])
            elif n == 2:
                self.C = [int(split[1+m]) for m in range(self.M)]
            elif n == 3:
                self.D = [int(split[1+m]) for m in range(self.M)]
            elif split[0] == "BOM":
                i = int(split[1]) - 1
                p = int(split[2]) - 1
                m = int(split[3]) - 1
                t = int(split[4])
                c = self.C[m]
                d = self.D[m]
                self.boms.append(Bom(i, p, m, t, c, d))
            elif split[0] == "ORDER":
                r = int(split[1]) - 1
                i = int(split[2]) - 1
                e = int(split[3])
                d = int(split[4])
                q = int(split[5])
                
                
                self.orders.append(Order(r, i, e, d, q))

            n = n + 1

        # 各品目の工程数 : Number of processes by each item
        self.iToP = [0 for i in range(self.I)]
        for bom in self.boms:
            self.iToP[bom.i] = max(self.iToP[bom.i], bom.p + 1)
        
        # ORDER毎の残り工程数を登録しておく
        for i in range(self.R):
            self.orders[i].prest = self.iToP[self.orders[i].i] -1
        
        self.P = 0;
        for i in range(self.I):
            self.P = max(self.P, self.iToP[i]);

    def time(self, m, i, p):
        for bom in self.boms:
            if bom.i == i and bom.p == p and bom.m == m:
                return bom.t
        return -1

    def canMake(self, m, i, p):
        for bom in self.boms:
            if bom.i == i and bom.p == p and bom.m == m:
                return True
        return False
    
    def selectMachine(self,i,p,num):
        
        minm = -1
        minnum = 99999999999
        
        # BOMを順番に見ていく
        for bom in self.boms:
            if (bom.i == i and bom.p == p): # 対応できるBOMである
                if(num[bom.m] == 0): # そのマシンにまだ一つのオーダも割り当てられていなければ確定
                    return bom.m
                elif(num[bom.m] < minnum): # 割り当てられている場合、なるべく少ないマシンを選択
                    minnum = num[bom.m]
                    minm = bom.m
        
        return minm
        
    
    def selectOrder(self):
        
        # orderは更新されるのでsortし直す
        self.orders = sorted(self.orders, key=attrgetter('lim'))
        self.orders = sorted(self.orders, key=attrgetter('drest','e', 'r'),reverse = True)
        
        for order in self.orders: # orderをsortした順に見ていく
            if(order.prest == -1): # prestが0のオーダは完了済みなので割り付けない
                continue
        
            if(order.dflg): # dflgがTrueのものから優先的に使用
                return order
        
        # dflgが全てFalseならprestが0でない先頭のorderを使用
        for order in self.orders:
            if(order.prest != -1):
                return order
        

    def solve(self):
        # 各設備の直後の製造開始時刻 : Previous manufacturing end time of each machine
        #mToPreviousT3 = [0 for m in range(self.M)]
        mToPreviousT1 = [0 for m in range(self.M)]
        # 各設備の直後の品目: Previous item of each machine
        mToPreviousI = [-1 for m in range(self.M)]
        # 各設備の直後のジョブを参照するために登録
        mToPreviousOpe = [-1 for m in range(self.M)]
        # 各注文の各工程の製造終了時刻 : Manufacturing end time of each process of each order
        t3rp = [[-1 for p in range(self.iToP[self.orders[r].i])] for r in range(self.R)]
        # 各設備に割り当てられたオーダの数
        mToNumorder = [0 for m in range(self.M)]
        
        # 工程の総数
        ol = 0
        for i in t3rp:
            ol += len(i)

        # 注文を納期が遅い順に並べ替える : Sort orders by earliest start time
        # 納期が遅い→limitが少ないの順
        self.orders = sorted(self.orders, key=attrgetter('lim'))
        self.orders = sorted(self.orders, key=attrgetter('drest','e', 'r'),reverse = True)
        
        # BOMをsortする
        # 段取り時間ペナルティ係数が遅延ペナルティ係数より大きい場合のみ順序入れ替え
        if(self.A1 == max(self.A1,self.A2,self.A3)):
            self.boms = sorted(self.boms, key = attrgetter("d"))
        else:
            self.boms = sorted(self.boms, key = attrgetter("cd"))

        # オーダを1つずつ処理していくのではなく各工程毎に処理
        while True:
            # selectOrder関数を新たに作成
            #order = self.orders[j]
            order = self.selectOrder()
            r = order.r;
            i = order.i;
            e = order.e;
            d = order.d;
            q = order.q;
            prest = order.prest;
            drest = order.drest;
            
            #選ばれた注文の最後の工程から設備と時間を割り付けていく
            # 利用可能な設備を見つける
            m = -1;
            
            # マシンごとに見ていくのではなく、すべてのマシンを総当たりして
            # 望ましいマシンを探す
            
            m = self.selectMachine(i,prest,mToNumorder)
            
            if m == -1:
                continue
            """
            for m2 in range(self.M):
                # マシンを選択
                # BOMをsortしているので望ましいものから選ばれる
                if self.canMake(m2, i, prest):
                    m = m2
                    break
            if m == -1:
                continue
            """
            
            if(mToPreviousI[m] == -1): #そのマシンにオーダが割り付けられていない場合
                t3 = order.drest
                dantime = 0
            
            else: # そのマシンにオーダが割り付けられている場合
                #発生しうる段取り時間
                dantime = self.D[m] * (abs(i - mToPreviousI[m])%3)
            
                # 段取り終了時刻は{そのオーダの納期、直後の工程の製造開始時刻+段取り時間}の最小値
                t3 = min(order.drest, mToPreviousT1[m]-dantime)
            
            # t2はt3から実行時間を引いたもの
            t2 = t3 - self.C[m] * self.time(m, i, order.prest) * q
            
            # 段取り開始時刻はあとから計算するためt1=t2
            t1 = t2
            
            # orderを追加
            ope = Operation(m, r, order.prest, t1, t2, t3, i, order)
            self.operations.append(ope)
            
            # 既にそのマシンに工程がわりあてられていたら、そのオーダのパラメータを更新
            if(mToPreviousI[m] != -1):
                mToPreviousOpe[m].t1 -= dantime # t1に段取り時間を追加
                mToPreviousOpe[m].order.drest  -= dantime # drestから段取り時間を引く
                mToPreviousOpe[m].order.dflg = True # dflgをTrueにする 
            
            # Falseの時に段取り時間がどうなってる?
            # 後から割り当てられたりした関係できちんと更新できていないのではないか？
            
            # NumOrderの更新
            mToNumorder[m] += 1
            
            # 対象としたオーダのdrestとdflgを更新
            order.drest = t1
            order.dflg = False
            order.prest -= 1
            
            # Previous系のパラメータを更新
            mToPreviousT1[m] = t1
            mToPreviousI[m] = i
            mToPreviousOpe[m] = ope
            

            # olを更新して、ループから抜ける判定
            
            ol -= 1
            if(ol == 0):
                break
            
            """
            # 各注文の最初の工程から設備と時間を割り付けていく : Assign operation from the first of each order to machine and time
            for p in range(self.iToP[i]):
                # 利用可能な設備を見つける : Find assignable resource
                m = -1;
                for m2 in range(self.M):
                    # マシンを選択
                    # BOMをsortしているので望ましいものから選ばれる
                    if self.canMake(m2, i, p):
                        m = m2
                        break
                if m == -1:
                    continue

                # 段取り開始時刻は、｛この注文の最早開始時刻、この工程の前の工程の製造終了時刻、この設備の前回の製造終了時刻｝の最大値
    	        # Setup start time is max number of { Earliest start time of this order,
          	    #                                  	  Manufacturing end time of the operation of previous process,
            	#                                     Manufacturing end time of last assigend operation to this machine }
                t1 = max(e, t3rp[r][p - 1] if p - 1 >= 0 else 0, mToPreviousT3[m])
                t2 = t1
                if mToPreviousI[m] != -1:
                    # この設備を使うのが２回目以降なら、段取り時間を足す。 : Add setup time if this operation is not the first operation assigned to this machine.
                    t2 += self.D[m] * (abs(i - mToPreviousI[m]) % 3)
                t3 = t2 + self.C[m] * self.time(m, i, p) * q

                self.operations.append(Operation(m, r, p, t1, t2, t3, i, order))

                mToPreviousI[m] = i
                mToPreviousT3[m] = t3
                t3rp[r][p] = t3
            """
            
    def checkResult(self): #最早時間を超えているものを調整する
        max_over = 0
        for operation in self.operations:
            over = operation.order.e - operation.t1
            if(over > max_over):
                max_over = over
        
        if(max_over > 0):
            for operation in self.operations:
                operation.t1 += max_over
                operation.t2 += max_over
                operation.t3 += max_over

    def writeSolution(self):
        print("{}".format(len(self.operations)))
        for operation in self.operations:
            print("{} {} {} {} {} {}".format((operation.m + 1), (operation.r + 1), (operation.p + 1), operation.t1, operation.t2, operation.t3))

    def run(self):
        self.readProblem()
        self.solve()
        self.checkResult()
        self.writeSolution()

if __name__ == '__main__':
    asprova2 = Asprova2()
    asprova2.run()
