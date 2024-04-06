"""
送信データパターンを管理するクラス


"""
import csv

import SharedMemory as sm

class SendDataManager():
    
    #---------------------------------
    # コンストラクタ
    #
    # @param data_setting_file : 
    #---------------------------------
    def __init__(self, data_setting_file):

        #メンバー変数を初期化する
        self._data_setting_file = data_setting_file
        self._data_patterns     = dict()

	    #データパターンファイル（CSV形式）を読込む。
        self._read_data_setting_file()


    #---------------------------------
    # デストラクタ
    #
    #---------------------------------
    def __del__	(self):
        print("del SendDataManager")

    #---------------------------------
    # データ設定ファイルを読み込む関数
    #
    #---------------------------------
    def _read_data_setting_file(self):
        
        with open(self._data_setting_file, "r", encoding="utf-8") as csvfile:

            data = csv.reader(csvfile, delimiter=",")

            #1行目読み込む(ヘッダー部のため読み捨て)
            next(data)

            #1行ずつ読み込む
            for row in data:

                #データパターン名をkey、データ値のリストをvalueとした辞書を作成する
                if row[0] not in self._data_patterns:
                    self._data_patterns[row[0]] = list()
                else:
                    pass

                #リストの[データNo -1]の位置にデータ値を設定する
                dataNo    = int(row[2])
                data_type = self.__get_data_type(dataNo)
                
                if data_type == sm.DataType.CHAR:
                    self._data_patterns[row[0]].append( (dataNo, row[3][0],) )

                elif data_type == sm.DataType.BOOL:
                    self._data_patterns[row[0]].append( (dataNo, bool(row[3]),) )

                elif data_type == sm.DataType.INT:
                    self._data_patterns[row[0]].append( (dataNo, int(row[3]),) )

                elif data_type == sm.DataType.DOUBLE:
                    self._data_patterns[row[0]].append( (dataNo, float(row[3]),) )

                else:
                    pass

                
    def __get_data_type(self, data_no):

        data_type = sm.DataType.UNDEFINED

        for send_data in sm.SharedMemorySend:

            if send_data.dataNo == data_no:
                data_type = send_data.dataType
                break
        
        return data_type



    #---------------------------------
    # データパターン名のリストを取得する関数
    #
    # return pattern_name_list : データパターン名のリスト
    #---------------------------------
    def get_pattern_name_list(self):
        
        pattern_name_list = list(self._data_patterns.keys())

        return pattern_name_list

    
    
    #---------------------------------
    # 指定のパターンのデータを取得する関数
    #
    # @param pattern_name : データパターン名
    # return data_pattern : 指定のデータパターンの値
    #---------------------------------
    def get_data_pattern(self, pattern_name:str):
        
        data_pattern = self._data_patterns[pattern_name]

        return data_pattern


#-------------------------------------------
# メイン関数(テスト用)
#-------------------------------------------
if __name__ == "__main__":

    dm = SendDataManager("Templete.csv")
    print(dm._data_patterns)
    print(dm.get_pattern_name_list())
    print(dm.get_data_pattern("test1"))