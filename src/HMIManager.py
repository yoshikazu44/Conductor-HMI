"""
HMI全体の管理をするクラス

"""
import time
import json
from enum import Enum

import SharedMemory as sm
import SendDataManager
import ConductorComm

SETTING_FILE = "HmiSetting.json"

#Enum プログラム種別
class SystemType(Enum):
    ADK        = 1
    CONTROLLER = 2


class HmiManager():

    #---------------------------------
    # コンストラクタ
    #
    #---------------------------------
    def __init__(self):

        #メンバー変数の初期化
        self._send_data_manager = None
        self._adk_comm          = None
        self._adk_ipaddress     = ""
        self._adk_port          = 0
        self._cntl_ipaddress    = ""
        self._cntl_port         = 0
        self._logfile_path      = ""
        self._data_file_path    = ""
        self._log_split_inst    = dict()

        #システム設定ファイル（JSON形式）を読込む。
        self._read_system_setting_file()

        #送信データ管理クラスと通信クラスをインスタンス化する
        self._send_data_manager = SendDataManager.SendDataManager(self._data_file_path)
        self._adk_comm          = ConductorComm.ConductorComm(self._adk_ipaddress,  self._adk_port, self._logfile_path)
        self._cntl_comm         = ConductorComm.ConductorComm(self._cntl_ipaddress, self._cntl_port, "", False)

        #ログ分割指示信号を作成する
        self._create_log_split_instruction()
    
    
    #---------------------------------
    # デストラクタ
    #
    #---------------------------------
    def __del__(self):
        
        del self._send_data_manager
        print("del HMI Manager")

        
        self._adk_comm.end_proc()
        del self._adk_comm

        self._cntl_comm.end_proc()
        del self._cntl_comm
        

    #---------------------------------
    # システム設定ファイルを読み込む関数
    #
    #---------------------------------
    def _read_system_setting_file(self):
        
        try:
            #システム設定ファイル（JSON形式）をオープンする。
            with open(SETTING_FILE, "r", encoding="utf_8_sig") as f:
                setting_info = json.load(f)

                #設定項目を読み込み、メンバー変数へ設定する。
                self._logfile_path   = setting_info.get("LogFileDir",   "./Output")
                self._data_file_path = setting_info.get("DataFilePath", "./Templete.csv")

                adk                  = setting_info.get("ADK", dict())
                self._adk_ipaddress  = adk.get("Host", "localhost")
                self._adk_port       = adk.get("Port", 30000)

                controller           = setting_info.get("Controller", dict())
                self._cntl_ipaddress = controller.get("Host", "localhost")
                self._cntl_port      = controller.get("Port", 31000)

        except IOError:
            #print("setting.json cannot be opened.")
            return 1
        
        except json.decoder.JSONDecodeError as e:
            print("HmiSetting.json cannot be opened.")
            print("{} : {}".format(type(e), e))
            return 1
        
        return 0

    #---------------------------------
    # ログ分割指示信号を作成する関数
    #
    #--------------------------------- 
    def _create_log_split_instruction(self):

        self._log_split_inst["DataNo"]   = 90
        self._log_split_inst["DataType"] = 3
        self._log_split_inst["Value"]    = 1

    #---------------------------------
    # ADKダミーに接続しているか判定する関数
    #
    # return True:接続中/False:未接続
    #---------------------------------
    def is_connect_adk(self):
    
        return self._adk_comm.get_connect_flag()

    #---------------------------------
    # 試験評価プログラムに接続しているか判定する関数
    #
    # return True:接続中/False:未接続
    #---------------------------------
    def is_connect_cntl(self):
    
        return self._cntl_comm.get_connect_flag()

    #---------------------------------
    # データパターン名のリストを取得する関数
    #
    # return データパターン名のリスト
    #---------------------------------
    def get_pattern_name_list(self):

        #データパターン名のリストを取得する。
        return self._send_data_manager.get_pattern_name_list()


    #---------------------------------
    # 指定のパターン名のデータを取得する関数
    #
    # @param pattern_name : データパターン名
    # return データパターン名のリスト
    #---------------------------------
    def get_data_pattern(self, pattern_name:str):

        #引数のデータパターン名に対応するデータパターンを取得する。
        return self._send_data_manager.get_data_pattern(pattern_name)


    #---------------------------------
    # 共有メモリにデータを設定する関数
    #
    # @param send_data_list : 送信データの値
    #---------------------------------
    def set_data(self, send_data_list):
        
        #データ送信中かつ送信データ更新あり
        if sm.exec_flag == True:
        
            #送信データ更新フラグがOFFになるまで待機
            while sm.update_flag == True:
                time.sleep(0.05)
        
        for send_data in send_data_list:
        
            #リストからデータ値を取得する
            data_no = send_data[0]
            value   = send_data[1]

            #共有メモリに対して、データを設定する。
            for i, sm_data in enumerate(sm.SharedMemorySend):
                
                if sm_data.dataNo == data_no:

                    if sm.SharedMemorySend[i].dataType == sm.DataType.BOOL:
                        sm.SharedMemorySend[i].value = bool(value)
                    
                    elif sm.SharedMemorySend[i].dataType == sm.DataType.INT:
                        sm.SharedMemorySend[i].value = int(value)
                    
                    elif sm.SharedMemorySend[i].dataType == sm.DataType.DOUBLE:
                        sm.SharedMemorySend[i].value = float(value)
                    
                    break
                
        #送信データ更新フラグをONにする
        sm.update_flag = True

    #---------------------------------
    # 受信データ取得する関数
    #
    # return recv_data_list : 受信データリスト
    #---------------------------------
    def get_recv_data(self):
        
        recv_data_list = list()
        
        #共有メモリ(受信領域)の要素数だけループ
        for recv_data in sm.SharedMemoryRecv:
        
            #データNoが0の場合、スキップ
            if recv_data.dataNo == 0:
                continue
        
            #共有メモリからデータNoとデータ値を取得する
            data_no = recv_data.dataNo
            value   = recv_data.value
        
            #データNoとデータ値をセットとして戻り値用のリストに追加する。
            recv_data_list.append((data_no, value,))
        
        return recv_data_list

    #---------------------------------
    # 指定データNoの値を取得する関数
    #
    # @param data_no :
    # return value   :
    #---------------------------------
    def get_recv_data_by_data_no(self, data_no):

        #共有メモリ(受信領域)の要素数だけループ
        for recv_data in sm.SharedMemoryRecv:

            if recv_data.dataNo == data_no:
                return recv_data.value
        
        else:
            return -1

    #---------------------------------
    # 車掌機能実験システムとの通信を開始する関数
    #
    #---------------------------------
    def start_comm(self):
        
        #通信実行中フラグをONにする。
        sm.exec_flag = True

        #データの送受信を開始する。
        self._adk_comm.run()


    #---------------------------------
    # 車掌機能実験システムとの通信を終了する関数
    #
    #---------------------------------
    def end_comm(self):
        
        #通信実行中フラグをOFFにする
        sm.exec_flag = False
        
        #送受信処理がともに終了するまで待機
        while True:

            if self._adk_comm.is_stop() == True:
                break

            else:
                time.sleep(0.1)

    #---------------------------------
    # ADKダミーへ再接続する関数
    #
    #---------------------------------
    def reconnect(self, sys_type):
    
        #ADKダミーとの再接続を実行
        if sys_type == SystemType.ADK:
            
            del self._adk_comm
            self._adk_comm = ConductorComm.ConductorComm(self._adk_ipaddress, self._adk_port, self._logfile_path)
        
        #制御部との再接続を実行
        elif sys_type == SystemType.CONTROLLER:
            
            del self._cntl_comm
            self._cntl_comm = ConductorComm.ConductorComm(self._cntl_ipaddress, self._cntl_port, "", False)

    
    #---------------------------------
    # ログ分割指示を送信する関数
    #
    # @param sys_type : 送信先システム
    #---------------------------------
    def send_log_split(self, sys_type):

        try:
            self.__send_data_once(self._log_split_inst, sys_type)
        
        except BaseException as e:
            raise

    #---------------------------------
    # 遠隔操作完了信号を送信する関数
    #
    #---------------------------------
    def send_remote_op(self):

        try:
            remote_op_complete = dict()
            remote_op_complete["DataNo"]   = 147
            remote_op_complete["DataType"] = 3
            remote_op_complete["Value"]    = 1
        
            self.__send_data_once(remote_op_complete, SystemType.ADK)
                
        except BaseException as e:
            raise

    #---------------------------------
    # 画像ソース種別を送信する関数
    #
    #---------------------------------
    def send_image_source(self, image_src_type):

        try:
            image_source = dict()
            image_source["DataNo"]   = 149
            image_source["DataType"] = 3
            image_source["Value"]    = image_src_type
        
            self.__send_data_once(image_source, SystemType.ADK)
                
        except BaseException as e:
            raise

    #---------------------------------
    # 指定プログラムにデータを送信する関数
    #
    # @param send_data : 送信データ
    # @param sys_type  : 送信先システム
    #---------------------------------
    def __send_data_once(self, send_data, sys_type):
    
        send_data_list = list()
        send_data_list.append(send_data)

        try:
            if sys_type == SystemType.ADK:
                self._adk_comm.send_data(send_data_list)
            
            elif sys_type == SystemType.CONTROLLER:
                self._cntl_comm.send_data(send_data_list)
        
        except BaseException as e:
            raise

#-------------------------------------------
# メイン関数(テスト用)
#-------------------------------------------
if __name__ == "__main__":

    hmi = HmiManager()
    print(hmi.get_pattern_name_list())
    data = hmi.get_data_pattern("test1")
    print(data)
    
    sm.update_flag = True
    hmi.start_comm()
#    for sm_send in sm.SharedMemorySend:
#        print("DataNo: {},\tDataType: {},\tValue:{}".format(sm_send.dataNo, sm_send.dataType, sm_send.value))
    time.sleep(1)
    hmi.set_data(data)
    time.sleep(1)
#    print("")
#    for sm_send in sm.SharedMemorySend:
#        print("DataNo: {},\tDataType: {},\tValue:{}".format(sm_send.dataNo, sm_send.dataType, sm_send.value))
    print("end")
    hmi.end_comm()
   
