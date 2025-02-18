"""
受信データログを管理するクラス


"""
import os
import datetime
import csv

import SharedMemory as sm

SIGNAL_INFO_PATH = "./SignalInfo.txt"

class LogManager():

    #---------------------------------
    # コンストラクタ
    #
    # @param output_path : ログ出力フォルダ
    #---------------------------------
    def __init__(self, output_path):
        
        self._output_path      = output_path
        self._signal_info_path = SIGNAL_INFO_PATH
        self._signal_info      = list()
        self._log_file         = None

        # DataNo → 信号名
        self._singal_name      = {}

        #ログファイルを作成し、ファイルをオープンする。
        #出力先フォルダが存在していなければ作成する
        os.makedirs(self._output_path, exist_ok=True)

        #ログファイルを作成する
        dt_now         = datetime.datetime.now()
        timeStr        = (dt_now.strftime('%Y%m%d %H%M%S')).replace(" ", "_")
        self._log_file = open(self._output_path + "/Data_"+timeStr+".csv", mode='x')
	
	    #信号情報ファイルを読み込む
        self._read_signal_info()
	
	    #ログファイルのヘッダを出力する
        self._write_header()


    #---------------------------------
    # デストラクタ
    #
    #---------------------------------
    def __del__	(self):
        
        print("close log file")
        #ログファイルをクローズする。
        self._log_file.close()


    #---------------------------------
    # 信号情報ファイルを読み込む関数
    #
    #---------------------------------
    def _read_signal_info(self):
        
        #信号情報ファイル(SignalInfo.txt)を読み込む。
        with open(self._signal_info_path, "r", encoding="utf-8") as csvfile:
            
            signal_infos = csv.reader(csvfile, delimiter=",")

            for signal_info in signal_infos:
            
                #信号名とデータNoを取得する。
                signal_name = signal_info[0]
                data_no     = int(signal_info[1])
            
                #信号名とデータNoをセットとしてリストに追加する。
                self._signal_info.append((signal_name, data_no,))

                # DataNo → 信号名
                self._singal_name[data_no] = signal_name
        

    #---------------------------------
    # ログファイルのヘッダを出力する関数
    #
    #---------------------------------
    def _write_header(self):
        
	    #時刻(Time)を出力する。
        self._log_file.write("Time")
        
        for signal_name, data_no in self._signal_info:
        
            #_signal_infoから信号名を取り出し出力する。
            self._log_file.write(","+signal_name)
            
        self._log_file.write("\n")

        #self._log_file.flush()


    #---------------------------------
    # 共有メモリ(受信領域)の内容をログに出力する関数
    #
    #---------------------------------
    def write_log_file(self):
        
        #print("write log\t", end='')
	    #現在時刻を取得し、ログに出力する。
        dt_now  = datetime.datetime.now()
        timeStr = dt_now.strftime('%Y/%m/%dT%H:%M:%S.%f')[:-3]
        self._log_file.write(timeStr)
	
        for signal_name, data_no in self._signal_info:
        
            value = 0

            #受信データからデータNoに該当するデータを取得する。
            for data in sm.SharedMemoryRecv:
                if data_no == data.dataNo:
                    value = data.value
                    break

                else:
                    pass
            
            #データ値をログに出力する。
            self._log_file.write("," + str(value))
            #print(" {}".format(value), end='')

        self._log_file.write("\n")
        #print("")

    # DataNo → 信号名
    def signal_name(self, data_no):
        return self._singal_name[data_no]

#-------------------------------------------
# メイン関数(テスト用)
#-------------------------------------------
if __name__ == "__main__":

    log = LogManager("./Output")
    log.write_log_file()
