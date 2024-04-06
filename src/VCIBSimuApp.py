"""
統合評価環境HMIツールのGUI
			株式会社オブジェクトデータ
			作成日:2024年3月1日
			作成者:淺野

"""
import threading
import time
from typing import Union
import tkinter
from tkinter import ttk, messagebox

import HMIManager

#送信データ
send_data_infos = ((142, 'ドア開要求',             ('OFF', 'ON'),                0),
                   (143, 'ドア閉要求',             ('OFF', 'ON'),                0),
                   (141, '発車判定要求',           ('OFF', 'ON'),                0),
                   (144, 'ドア閉要求(最終バス停)', ('終了', '実行'),             0),
                   (145, '乗車・降車人数要求',     ('終了', '実行'),             0),
                   (146, '画像認識処理モード',     ('OFF', 'Lv1', 'Lv2', 'Lv3'), 0),
                   (148, '判定要求生成方法',       ('HMI操作', '車両状態連動'),  0),
                  )

#受信データ(VCIB)
vcib_recv_data_infos = (( 1, 'D席シートベルト'), (2, 'エアコン状態'),      (3, 'ヘッドランプ状態' ),
                        ( 4, '車速'),            (5, 'EPB/シフトP'),       (6, 'ドア状態(左)' ),
                        ( 7, 'ドア状態(右)'),    (8, 'ブレーキ操作量(%)'), (9, 'アクセル操作量(%)'),
                        (10, 'シフト'),                      
                       )

#受信データ(画認)
recv_data_infos = ((124, 'ドア状態'),           (180, 'ドア作動要求(VCIB)'), (200, 'instruction'),
                   (201, 'signage_info'),       (203, 'failure_severity'),   (205, '遠隔要請'),
                   (206, '乗車人数'),           (207, '降車人数'),           (208, '車室内乗客人数')
)

"""
GUIクラス


"""
class VCIBSimuApp():

    #-----------------------------
    #コンストラクタ
    #-----------------------------
    def __init__(self):
        
        self.hmi_manager = HMIManager.HmiManager()
        self.exec_flag   = False
        self.recv_thr    = None
        self.pre_remote_op_state = 0

        #メインウインドウ
        self.main_win = tkinter.Tk()
        self.main_win.title('HMI APP')
        self.main_win.resizable(width=False, height=False)
        self.main_win.protocol('WM_DELETE_WINDOW', (lambda:self.quit()))

        self.data_label = ttk.Label(self.main_win, text='接続先')
        self.data_label.grid(column=0, row=0, sticky=tkinter.NW, padx=5)

        #############################
        # 接続先領域の作成
        #############################
        self.connect_frm = ttk.Frame(self.main_win, relief='solid')
        self.connect_frm.grid(column=0, row=1, sticky=tkinter.NW, padx=5, pady=5)

        self.connect_status_adk  = ttk.Style()
        self.connect_status_adk.configure('connadk.TLabel',   background = 'red')
        self.connect_status_cntl = ttk.Style()
        self.connect_status_cntl.configure('conncntl.TLabel', background = 'red')
        self._init_connect_info(self.connect_frm, 0, self.hmi_manager._adk_ipaddress,  self.hmi_manager._adk_port, 'connadk.TLabel')
        self._init_connect_info(self.connect_frm, 1, self.hmi_manager._cntl_ipaddress, self.hmi_manager._cntl_port, 'conncntl.TLabel')

        t = threading.Thread(target=self.check_connect)
        t.setDaemon(True)
        t.start()

        #############################
        # 画像ソース選択領域の作成
        #############################
        self.image_select_label = ttk.Label(self.main_win, text='画像ソース選択')
        self.image_select_label.grid(column=0, row=2, sticky=tkinter.NW, padx=5)

        self.image_select_frm = ttk.Frame(self.main_win, relief='solid')
        self.image_select_frm.grid(column=0, row=3, sticky=tkinter.NSEW, padx=5, pady=5)

        self.image_select_var = tkinter.IntVar()
        self.image_select_var.set(0)
    
        self.image_select_camera_btn = ttk.Radiobutton(self.image_select_frm, value=0, variable=self.image_select_var,
                                                       text='カメラ', command=lambda:self.select_image_source())
        self.image_select_camera_btn.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.image_select_no_alert_btn = ttk.Radiobutton(self.image_select_frm, value=1, variable=self.image_select_var, 
                                                         text='エリア侵入/転倒なし', command=lambda:self.select_image_source())
        self.image_select_no_alert_btn.grid(column=1, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.image_select_door_alert_btn = ttk.Radiobutton(self.image_select_frm, value=2, variable=self.image_select_var, 
                                                           text='エリア侵入', command=lambda:self.select_image_source())
        self.image_select_door_alert_btn.grid(column=2, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.image_select_incabin_alert_btn = ttk.Radiobutton(self.image_select_frm, value=3, variable=self.image_select_var, 
                                                              text='転倒', command=lambda:self.select_image_source())
        self.image_select_incabin_alert_btn.grid(column=3, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        #############################
        # 送信データ領域の作成
        #############################
        self.send_label = ttk.Label(self.main_win, text='送信データ')
        self.send_label.grid(column=0, row=4, sticky=tkinter.NW, padx=5)

        self.send_frm = ttk.Frame(self.main_win, relief='solid')
        self.send_frm.grid(column=0, row=5, sticky=tkinter.NSEW, padx=5, pady=5)

        #データパターンの設定
        self.pattern_frm = ttk.Frame(self.send_frm, relief='flat')
        self.pattern_frm.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.pattern_label = ttk.Label(self.pattern_frm, text='データパターン', width=13)
        self.pattern_label.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        pattern_name_list = self.hmi_manager.get_pattern_name_list()
        self.pattern_box = ttk.Combobox(self.pattern_frm, state="readonly", values=pattern_name_list)
        self.pattern_box.bind('<<ComboboxSelected>>', lambda e: self.change_data())
        self.pattern_box.set(pattern_name_list[0])
        self.pattern_box.grid(column=1, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.apply_btn = ttk.Button(self.pattern_frm, text="適用", command=lambda:self.apply_data())
        self.apply_btn.grid(column=3, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        #送信データの設定
        self.send_data_frm = ttk.Frame(self.send_frm, relief='solid')
        self.send_data_frm.grid(column=0, row=1, sticky=tkinter.SW, padx=5, pady=5)

        self.send_data_labels: list[ttk.Label]                           = list()
        self.send_data_boxes : dict[int, Union[ttk.Combobox, ttk.Entry]] = dict()
        self._init_send_data_area(self.send_data_frm)


        #############################
        # 受信データ領域の作成
        #############################
        self.recv_label = ttk.Label(self.main_win, text='受信データ')
        self.recv_label.grid(column=0, row=6, sticky=tkinter.SW, padx=5)

        self.recv_frm = ttk.Frame(self.main_win, relief='solid')
        self.recv_frm.grid(column=0, row=7, sticky=tkinter.NSEW, padx=5, pady=5)

        self.vcib_recv_frm = ttk.LabelFrame(self.recv_frm, relief='solid', text='VCIB')
        #self.vcib_recv_frm.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=5)
        self.vcib_recv_frm.pack(anchor=tkinter.NW, padx=5, pady=5, fill=tkinter.X, expand=True)

        self.image_recv_frm = ttk.LabelFrame(self.recv_frm, relief='solid', text='認識部')
        #self.image_recv_frm.grid(column=0, row=1, sticky=tkinter.NSEW, padx=5, pady=5)
        self.image_recv_frm.pack(anchor=tkinter.NW, padx=5, fill=tkinter.X)

        self.recv_data_labels: list[ttk.Label]      = list()
        self.recv_data_boxes : dict[int, ttk.Entry] = dict()
        self._init_recv_data_area(self.vcib_recv_frm, vcib_recv_data_infos)
        self._init_recv_data_area(self.image_recv_frm, recv_data_infos)

        # 遠隔OP領域の作成
        self.remote_op_frm = ttk.LabelFrame(self.recv_frm, relief='solid', text='遠隔OP')
        #self.remote_op_frm.grid(column=0, row=2, sticky=tkinter.NW, padx=5, pady=5)
        self.remote_op_frm.pack(anchor=tkinter.NW, padx=5, pady=5)

        self.remote_op_state_label = ttk.Label(self.remote_op_frm, text='遠隔OP状態')
        self.remote_op_state_label.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.remote_op_state = ttk.Entry(self.remote_op_frm, width=12)
        self.remote_op_state.insert(0, "非対応中")
        self.remote_op_state.grid(column=1, row=0, sticky=tkinter.NSEW, padx=5, pady=5)

        self.completed_btn = ttk.Button(self.remote_op_frm, text="操作完了", command=lambda:self.send_remote_op())
        self.completed_btn.grid(column=2, row=0, sticky=tkinter.NSEW, padx=5, pady=5)


        #メインフレーム(制御ボタン)
        self.control_frm = ttk.Frame(self.main_win)
        self.control_frm.grid(column=0, row=8, sticky=tkinter.NSEW, padx=5, pady=10, columnspan=6)

        self.log_btn = ttk.Button(self.control_frm, text='ログ生成', command=lambda:self.split_log())
        self.log_btn.grid(column=2, row=0)
        self.start_btn = ttk.Button(self.control_frm, text='送信', command=lambda:self.start())
        self.start_btn.grid(column=3, row=0)
        self.stop_btn  = ttk.Button(self.control_frm, text='中止', state=tkinter.DISABLED, command=lambda:self.cancel())
        self.stop_btn.grid(column=4, row=0)
        self.close_btn = ttk.Button(self.control_frm, text='終了', command=lambda:self.quit())
        self.close_btn.grid(column=5, row=0)

        self.send_data_frm.rowconfigure(1, weight=1)
        self.control_frm.columnconfigure(1, weight=1)
        self.control_frm.rowconfigure(0, weight=1)


        self.main_win.mainloop()


    #--------------------------------------------
    # 接続先領域を作成する関数
    #
    #--------------------------------------------
    def _init_connect_info(self, parent, row_num, ipaddress, port, label):

        names = ["ADKダミー", "制御部"]

        if row_num >= len(names):
            return

        self.connect_name = ttk.Label(parent, text=names[row_num])
        self.connect_name.grid(column=0, row=row_num, sticky=tkinter.EW, padx=5, pady=5)

        self.connect_info = ttk.Label(parent, text="[{}:{}]".format(ipaddress, port))
        self.connect_info.grid(column=1, row=row_num, sticky=tkinter.EW, padx=5, pady=5)
        
        self.connect_cond = ttk.Label(parent, text="   ", relief='solid', style= label)
        self.connect_cond.grid(column=2, row=row_num, sticky=tkinter.NSEW, padx=5, pady=5)

    #--------------------------------------------
    # 送信データ領域を作成する関数
    #
    #--------------------------------------------
    def _init_send_data_area(self, parent):

        pattern_name_list = self.hmi_manager.get_pattern_name_list()
        init_data         = self.hmi_manager.get_data_pattern(pattern_name_list[0])
        
        for i, send_data_info in enumerate(send_data_infos):
        
            #表示位置の計算
            tmpRow = i//3
            tmpCol = (i%3) * 2
            
            #ラベルの作成
            label = ttk.Label(parent, text=send_data_info[1])
            label.grid(row=tmpRow, column=tmpCol, sticky=tkinter.NSEW, padx=5, pady=5)
            self.send_data_labels.append(label)
            
            init_value = self.__get_init_value(init_data, send_data_info[0])

            #データ領域の作成
            if len(send_data_info) == 2:
                box = ttk.Entry(parent, justify=tkinter.RIGHT)
                box.insert(0, init_value)
            
            else:
                box = ttk.Combobox(parent, state="readonly", values=send_data_info[2], width=11)
                box.current(init_value)
            
            box.grid(row=tmpRow, column=(tmpCol + 1), sticky=tkinter.NSEW, padx=5, pady=5)      
            self.send_data_boxes[send_data_info[0]] = box

            #print(self.send_data_boxes[0].get())


    #--------------------------------------------
    # 指定データNoの初期値を取得する関数
    #
    #--------------------------------------------
    def __get_init_value(self, init_datas :list, data_no :int):
        
        init_value = 0

        #初期値を取得する
        for send_data_info in send_data_infos:

            if send_data_info[0] == data_no:
                init_value = send_data_info[3]
                break

        #最初に読み込んだデータパターンで初期値が指定されていれば、上書き
        for init_data in init_datas:

            if init_data[0] == data_no:
                init_value = init_data[1]
                break
        
        return init_value


    #--------------------------------------------
    #受信データ領域を作成する関数
    #
    #--------------------------------------------
    def _init_recv_data_area(self, parent, show_data):

        for i, recv_data_info in enumerate(show_data):

            #データNo.0はダミーなのでスキップ
            if recv_data_info[0] == 0:
                continue

            #表示位置の計算
            tmpRow = i//3
            tmpCol = (i%3) * 2

            #ラベルの作成
            label = ttk.Label(parent, text=recv_data_info[1])
            label.grid(row=tmpRow, column=tmpCol, sticky=tkinter.NSEW, padx=5, pady=5)
            self.recv_data_labels.append(label)
            
            #データ領域の作成
            box = ttk.Entry(parent, width=12)
            box.grid(row=tmpRow, column=(tmpCol + 1), sticky=tkinter.NSEW, padx=5, pady=5)
            #box.configure(state='disabled')
            self.recv_data_boxes[recv_data_info[0]] = box


    #--------------------------------------------
    # 通信状態を監視する関数
    #
    #--------------------------------------------
    def check_connect(self):
    
        prev_adk_ret  = False
        prev_cntl_ret = False
        
        try:
            while True:
            
                adk_ret  = self.hmi_manager.is_connect_adk()
                cntl_ret = self.hmi_manager.is_connect_cntl()

                #print("pre_adk :{}, adk :{}".format(prev_adk_ret,  adk_ret))
                #print("pre_cntl:{}, cntl:{}".format(prev_cntl_ret, cntl_ret))
                
                if prev_adk_ret != adk_ret and adk_ret == True:
                    self.connect_status_adk.configure('connadk.TLabel', background = 'green')
                    self.select_image_source()
                
                elif prev_adk_ret != adk_ret and adk_ret == False:
                    self.connect_status_adk.configure('connadk.TLabel', background = 'red')
                    self.cancel()
                    
                    messagebox.showerror("Error", "ADKダミーとの接続が切れました")
                    self.hmi_manager.reconnect(HMIManager.SystemType.ADK)
                
                else:
                    pass

                if prev_cntl_ret != cntl_ret and cntl_ret == True:
                    self.connect_status_cntl.configure('conncntl.TLabel', background = 'green')
                
                elif prev_cntl_ret != cntl_ret and cntl_ret == False:
                    self.connect_status_cntl.configure('conncntl.TLabel', background = 'red')
                                        
                    messagebox.showerror("Error", "制御部との接続が切れました")
                    self.hmi_manager.reconnect(HMIManager.SystemType.CONTROLLER)
                
                else:
                    pass
                    
                prev_adk_ret  = adk_ret
                prev_cntl_ret = cntl_ret

                #遠隔OP状態を監視する
                self.check_remote_op_state()
                
                time.sleep(1)
        
        except AttributeError as e:
            pass
        
        except Exception as e:
            print("{} : {}".format(type(e), e))

    #--------------------------------------------
    # 遠隔OP状態を監視する関数
    #
    #--------------------------------------------
    def check_remote_op_state(self):

        value = self.hmi_manager.get_recv_data_by_data_no(304)

        if self.pre_remote_op_state == 0 and value == 1:
            self.remote_op_state.delete(0, "end")
            self.remote_op_state.insert(0, "対応中")

        elif self.pre_remote_op_state == 1 and value == 0:
            self.remote_op_state.delete(0, "end")
            self.remote_op_state.insert(0, "非対応中")

        self.pre_remote_op_state = value

    #--------------------------------------------
    # 画像ソース選択時に呼ばれる関数
    #
    #--------------------------------------------
    def select_image_source(self):
        self.hmi_manager.send_image_source(self.image_select_var.get())


    #--------------------------------------------
    #データパターンの変更に合わせて表示データを変更する関数
    #
    #--------------------------------------------
    def change_data(self):

        #指定のパターンのデータ値を取得する
        pattren_name = self.pattern_box.get()
        data_pattern = self.hmi_manager.get_data_pattern(pattren_name)
        
        print("選択パターン名 {}".format(pattren_name))

        #各領域に値を設定する
        for data_no, value in data_pattern:
            
            #存在しないデータNoはスルー
            if data_no not in self.send_data_boxes:
                continue

            print(data_no)

            if isinstance(self.send_data_boxes[data_no], ttk.Combobox):
                if len(self.send_data_boxes[data_no].cget('values')) > value:
                    self.send_data_boxes[data_no].current(value)

            elif isinstance(self.send_data_boxes[data_no], ttk.Entry):
                self.send_data_boxes[data_no].delete(0, "end")
                self.send_data_boxes[data_no].insert(0, value)
            else:
                pass


    #--------------------------------------------
    # 選択されている値を共有メモリに設定する関数
    #
    #--------------------------------------------
    def apply_data(self):

        print("適用ボタンが押されました。")
        send_data_list = list()

        for data_no, data in self.send_data_boxes.items():
            
            if isinstance(data, ttk.Combobox):
                value = int(data.current())

            elif isinstance(data, ttk.Entry):
                value = float(data.get())
                
                # 車速をkm/hからm/sに変換する
                if data_no == 4:
                    value = value * 1000/3600
            else:
                value = None
            
            if value is not None:
                send_data_list.append( (data_no, value) )
        
        #共有メモリにデータを設定する
        self.hmi_manager.set_data(send_data_list)

        messagebox.showinfo("Info", "適用完了")

    #--------------------------------------------
    # 遠隔OP完了を送信する関数
    #
    #--------------------------------------------
    def send_remote_op(self):

        print("操作完了ボタンが押されました。")

        try:
            #遠隔OP完了を送信
            if self.hmi_manager.is_connect_adk() == True:
                self.hmi_manager.send_remote_op()

        except BaseException as e:
            print(e)


    #--------------------------------------------
    # ADKダミーと試験評価プログラムのログファイルを分割する関数
    #
    #--------------------------------------------
    def split_log(self):

        adk_msg  = "ADKダミー\t: "
        cntl_msg = "制御部\t: "

        try:
            #ADKダミーへのログ分割指示
            if self.hmi_manager.is_connect_adk() == True:
                self.hmi_manager.send_log_split(HMIManager.SystemType.ADK)
                adk_msg += "送信済み"
            else:
                adk_msg += "送信失敗"
        except BaseException as e:
            print(e)
            adk_msg += "送信失敗"
        
        try:
            #制御部へのログ分割指示
            if self.hmi_manager.is_connect_cntl() == True:
                self.hmi_manager.send_log_split(HMIManager.SystemType.CONTROLLER)
                cntl_msg += "送信済み"
            else:
                cntl_msg += "送信失敗"

        except BaseException as e:
            print(e)
            cntl_msg += "送信失敗"

        messagebox.showinfo("ログ生成信号送信結果", adk_msg + "\n" + cntl_msg)

    #--------------------------------------------
    # 送受信処理を開始する関数
    #
    #--------------------------------------------
    def start(self):

        if self.hmi_manager.is_connect_adk() == True:
        #if self.hmi_manager.is_connect_adk() == False:
        
            self.start_btn['state'] = tkinter.DISABLED
            self.close_btn['state'] = tkinter.DISABLED

            self.exec_flag = True
            self.recv_thr = threading.Thread(target=self._show_recv_data)
            self.recv_thr.setDaemon(True)
            self.recv_thr.start()

            self.hmi_manager.start_comm()

            self.stop_btn['state'] = tkinter.NORMAL
        
        else:
        
            messagebox.showerror("Error", "ADKダミーに接続していません")


    #--------------------------------------------
    # 受信したデータを表示する関数
    #
    #--------------------------------------------
    def _show_recv_data(self):

        while True:

            st_time = time.perf_counter()

            if self.exec_flag == False:
                break

            recv_datas = self.hmi_manager.get_recv_data()

            for data_no, value in recv_datas:

                #受信データ表示領域に存在するデータNoの場合
                if data_no in self.recv_data_boxes:
                    self.recv_data_boxes[data_no].delete(0, "end")
                    
                    #画面に受信データを表示
                    if data_no == 180:
                        self.recv_data_boxes[data_no].insert(0, hex(value))
                    else:
                        self.recv_data_boxes[data_no].insert(0, value)

            #print("Recv")
            #1秒待機  
            ed_time = time.perf_counter()
            time.sleep(1 - (ed_time - st_time))

        print("_show_recv_data End")

    #--------------------------------------------
    # 送受信処理を中止する関数
    #
    #--------------------------------------------
    def cancel(self):

        self.exec_flag = False

        self.hmi_manager.end_comm()

        while self.recv_thr is not None and self.recv_thr.is_alive() == True:
            time.sleep(0.01)

        self.start_btn['state'] = tkinter.NORMAL
        self.close_btn['state'] = tkinter.NORMAL
        self.stop_btn['state']  = tkinter.DISABLED

    #--------------------------------------------
    # システムを終了する関数
    #
    #--------------------------------------------
    def quit(self):

        #通信中は終了不可
        if self.exec_flag == False:
            print("del APP")
            del self.hmi_manager

            self.main_win.destroy()
        
        else:
            messagebox.showinfo("Info", "通信中は終了できません")

if __name__ == '__main__':
	
	App = VCIBSimuApp()
