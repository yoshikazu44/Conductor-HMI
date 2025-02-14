"""
車掌機能実験システムとの通信を行うクラス

"""
import socket
import threading
import json
import time

import SharedMemory as sm
import LogManager

class ConductorComm():
    
    #---------------------------------
    # コンストラクタ
    #
    # @param ipaddress    : 接続先のIPアドレス
    # @param port         : 接続先のポート番号
    # @param logfile_path : ログ(受信データ)を出力するパス
    #---------------------------------
    def __init__(self, ipaddress, port, logfile_path="", recvFlag=True):

        #メンバー変数を初期化する
        self._socket       = None
        self._connect_flag = False
        self._end_flag     = False
        self._ipaddress    = ipaddress
        self._port         = port
        self._log_manager  = None
        self._send_thr     = None
        self._recv_thr     = None
        self._senddata     = list()
        self._recv_flag    = recvFlag

        #車掌システムに接続する
        t = threading.Thread(target=self.connect_conductor, args=(recvFlag,))
        t.setDaemon(True)
        t.start()

        if logfile_path != "":
            #ログ管理クラスのインスタンスを作成する。
            self._log_manager = LogManager.LogManager(logfile_path)


    #---------------------------------
    # デストラクタ
    #---------------------------------
    def __del__(self):
        
        print("del ConductorComm")
	    #ログファイルを閉じる。
        if self._log_manager is not None:
            del self._log_manager

        #通信用ソケットを破棄する。
        if self._socket is not None:
            self._socket.close()
	

    #---------------------------------
    # 通信処理を終了する関数
    #---------------------------------
    def end_proc(self):

        self._end_flag = True
        while True:

            if self._recv_thr is None:
                break

            elif self._recv_thr.is_alive() == False:
                break
            
            time.sleep(0.1)

    #---------------------------------
    # 車掌システム接続フラグを取得する関数
    #---------------------------------
    def get_connect_flag(self):
    
        return self._connect_flag


    #---------------------------------
    # 車掌システムに接続する関数
    #---------------------------------
    def connect_conductor(self, recvFlag):

        #通信用ソケットを作成する。
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(5.0)
        print("Connect {}:{} ...".format(self._ipaddress, self._port))
        
        while True:

            try:

                if self._end_flag == True:
                    break

                #通信相手のアドレス、ポートを指定し、接続する。
                self._socket.connect((self._ipaddress, self._port))
                
                break
            
            except Exception as e:

                time.sleep(1)
                #print(self._socket)
        
        self._connect_flag = True
        print("Success {}:{}".format(self._ipaddress, self._port))
        
        #if recvFlag:
        #受信処理を開始する。
        self._recv_thr = threading.Thread(target=self._recv_data)
        self._recv_thr.setDaemon(True)
        self._recv_thr.start()

    #---------------------------------
    # 送信処理を開始する関数
    #---------------------------------
    def run(self):
        
    	#送信処理を開始する。
        self._send_thr = threading.Thread(target=self._send_vcib_data)
        self._send_thr.start()
        
        #送受信処理が終了するまで待機
        #self._recv_thr.join()
        #self._send_thr.is_alive()


    #---------------------------------
    # データを送信する関数
    #---------------------------------
    def send_data(self, data):
    
        try:
            str_data = json.dumps(data)
            data_len = len(str_data)
            tmp = str_data + " "*(1024 - data_len -1) + "\n"
            #print("send : ", str_data)
            self._socket.sendall(tmp.encode())
            

        except BaseException as e:
            print("send error")
            self._connect_flag = False
            raise e
    

    #---------------------------------
    # 送信処理を実施する関数
    #---------------------------------
    def _send_vcib_data(self):
        
        try:
            while True:

                st_time = time.perf_counter()

                #実行フラグがOFFなら終了
                if sm.exec_flag == False:
                    break
            
                #データ更新フラグがtrueの場合
                if sm.update_flag == True:
            
                    #送信データを生成する。
                    self._generate_send_data()
            
                #送信データ更新フラグをOFFにする。
                sm.update_flag = False
            
                #データを送信する。
                self.send_data(self._senddata)
            
                #次の送信まで待機(100ms)
                ed_time = time.perf_counter()
                time.sleep(0.1 - (ed_time - st_time))
        
        except BaseException as e:
            print(e)
            self._connect_flag = False
            #sm.exec_flag == False


    #---------------------------------
    # 共有メモリ(送信領域)の内容から送信するデータを生成する関数
    #
    #---------------------------------
    def _generate_send_data(self):
        
        #送信データを格納するリストを初期化する。
        self._senddata.clear()
        
        for data in sm.SharedMemorySend:
        
            dict_data = dict()
            
            #データNoとデータ型を変換する。
            dict_data["DataNo"]   = data.dataNo
            dict_data["DataType"] = data.dataType
            dict_data["Value"]    = data.value
            
            #リストに送信データを追加する。
            self._senddata.append(dict_data)

    #---------------------------------
    # 受信処理を実施する関数
    #
    #---------------------------------
    def _recv_data(self):
        
        try:
            LEN = 18000
            recv_msg = ''

            #if self._recv_flag == False:
            #    self._socket.settimeout(None)

            while True:
                
                st_time = time.perf_counter()

                #終了フラグがONなら終了
                if self._end_flag == True:
                    break
            
                try:
                    #車掌機能実験システムからデータを受信する。
                    recv_msg1 = self._socket.recv(LEN - len(recv_msg))
                    if len(recv_msg1) == 0:
                        #time.sleep(3)   # recv()でブロックしないので待機
                        continue

                    recv_msg += recv_msg1.decode('UTF-8')
                    if len(recv_msg) < LEN:
                        # 全体を受信していない
                        continue
                    
                    recv_data = json.loads(recv_msg)
                    recv_msg = ''
                except socket.timeout:

                    if self._recv_flag:
                        raise
                    else:
                        print("recv continue")
                        continue
                except json.decoder.JSONDecodeError as e:
                    print("{} : {}".format(type(e), e))
                    print(len(recv_msg))
                    if len(recv_msg) == 0:
                        raise
                    else:
                        continue

                # 受信したデータを共有メモリ(受信領域)に設定する。
                for data in recv_data:

                    #リストのデータからデータNoを取得する。
                    data_no = data["DataNo"]

                    #データNoに対応する共有メモリに対してデータ値を設定する。
                    value = data["Value"]
                    for i, sm_data in enumerate(sm.SharedMemoryRecv):

                        if sm_data.dataNo == data_no:
                            sm.SharedMemoryRecv[i].value = value
                            break
                
                #print(recv_data)
                #受信したデータをログに出力する。
                if sm.exec_flag == True:
                    self._log_manager.write_log_file()

                ed_time = time.perf_counter()
                if (ed_time - st_time) < 0.1:
                    time.sleep(0.1 - (ed_time - st_time))
            
        except Exception as e:
            print("{}:{}".format(type(e), e))
            self._connect_flag = False
            #sm.exec_flag == False

        print("Recv End")

    #---------------------------------
    # 送信処理が終了しているかチェックする関数
    #
    # return end_flag : True:処理終了/False:処理実行中
    #---------------------------------    
    def is_stop(self):

        end_flag = False

        if self._send_thr is None:
            end_flag = True

        elif self._send_thr.is_alive() == False:
            end_flag = True
        
        return end_flag





#-------------------------------------------
# メイン関数(テスト用)
#-------------------------------------------
if __name__ == "__main__":
    try:
        comm = ConductorComm("192.168.1.63", 30000, "./Output")
        sm.exec_flag = True
        sm.update_flag = True
        comm.run()

        time.sleep(1)
        sm.exec_flag = False

    except Exception as e:
        sm.exec_flag = False

    print("wait")
    comm._send_thr.join()
    comm._recv_thr.join()
    print("join")

    sm.exec_flag = True
    comm.run()
    time.sleep(1)
    sm.exec_flag = False

    print("wait")
    comm._send_thr.join()
    comm._recv_thr.join()
    print("join")


    del comm
